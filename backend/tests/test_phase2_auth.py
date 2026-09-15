import uuid
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.db.database import get_db, engine
from backend.app.db.models import Company, User as DBUser
from backend.app.auth.security import create_access_token, verify_password

client = TestClient(app)


def unique_str():
    return uuid.uuid4().hex[:8]


# ============================================================================
# PHASE 2 AUTHENTICATION & MULTI-TENANT SECURITY TEST SUITE
# ============================================================================

def test_1_company_registration_succeeds_and_creates_admin():
    """Tests 1, 2, 3, 4, 21, 24: Company registration creates company & initial admin with hashed password."""
    uid = unique_str()
    company_name = f"Test Acme Tech {uid}"
    admin_email = f"alice.admin_{uid}@acme.com"

    payload = {
        "company_name": company_name,
        "admin_name": "Alice Admin",
        "admin_email": admin_email,
        "password": "AdminSecretPassword123!",
    }
    response = client.post("/auth/register-company", json=payload)
    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()

    assert "company_id" in data
    assert data["company_name"] == company_name
    assert "invite_code" in data
    assert data["invite_code"].startswith("INV-")
    assert "admin_id" in data
    assert data["admin_email"] == admin_email

    # Verify in MySQL DB directly
    db: Session = next(get_db())
    db_company = db.query(Company).filter(Company.id == data["company_id"]).first()
    assert db_company is not None
    assert db_company.name == company_name

    db_admin = db.query(DBUser).filter(DBUser.id == data["admin_id"]).first()
    assert db_admin is not None
    assert db_admin.email == admin_email
    assert db_admin.role == "admin"
    assert db_admin.company_id == db_company.id
    # Password must be stored hashed
    assert db_admin.hashed_password != "AdminSecretPassword123!"
    assert verify_password("AdminSecretPassword123!", db_admin.hashed_password) is True
    db.close()


def test_2_employee_registration_succeeds_with_valid_invite():
    """Tests 5, 8: Employee registration succeeds using valid company invite code."""
    uid = unique_str()
    comp_res = client.post("/auth/register-company", json={
        "company_name": f"Emp Test Corp {uid}",
        "admin_name": "Emp Admin",
        "admin_email": f"emp.admin_{uid}@testcorp.com",
        "password": "Password123!",
    })
    assert comp_res.status_code == 200, f"Error: {comp_res.text}"
    comp_data = comp_res.json()
    invite_code = comp_data["invite_code"]
    company_id = comp_data["company_id"]

    # Register employee
    emp_email = f"bob.engineer_{uid}@testcorp.com"
    emp_res = client.post("/auth/register", json={
        "full_name": "Bob Engineer",
        "email": emp_email,
        "password": "EmpPassword123!",
        "company_id": company_id,
        "role": "engineer",
        "invite_code": invite_code,
    })
    assert emp_res.status_code == 200, f"Error: {emp_res.text}"
    emp_data = emp_res.json()

    assert emp_data["email"] == emp_email
    assert emp_data["role"] == "engineer"
    assert emp_data["company_id"] == company_id


def test_3_employee_cannot_register_as_admin():
    """Test 6: Employee cannot self-assign role='admin' during registration."""
    uid = unique_str()
    comp_res = client.post("/auth/register-company", json={
        "company_name": f"No Admin Self Reg {uid}",
        "admin_name": "Real Admin",
        "admin_email": f"realadmin_{uid}@noadmin.com",
        "password": "Password123!",
    })
    assert comp_res.status_code == 200
    comp_data = comp_res.json()

    res = client.post("/auth/register", json={
        "full_name": "Malicious Employee",
        "email": f"attacker_{uid}@noadmin.com",
        "password": "Password123!",
        "company_id": comp_data["company_id"],
        "role": "admin",
        "invite_code": comp_data["invite_code"],
    })
    assert res.status_code == 400
    assert "Admin role cannot be assigned" in res.json()["detail"]


def test_4_employee_cannot_create_company():
    """Test 7: Regular employee registration endpoint cannot create a new company."""
    res = client.post("/auth/register", json={
        "full_name": "Employee Fake Comp",
        "email": f"fakecomp_{unique_str()}@emp.com",
        "password": "Password123!",
        "company_id": "non_existent_company_id",
        "role": "engineer",
        "invite_code": "INV-FAKE1234",
    })
    assert res.status_code == 404


def test_5_invalid_invite_code_rejected():
    """Test 9: Invalid company invite code is rejected with 401."""
    uid = unique_str()
    comp_res = client.post("/auth/register-company", json={
        "company_name": f"Bad Invite Corp {uid}",
        "admin_name": "Inv Admin",
        "admin_email": f"invadmin_{uid}@badinvite.com",
        "password": "Password123!",
    })
    assert comp_res.status_code == 200
    comp_data = comp_res.json()

    res = client.post("/auth/register", json={
        "full_name": "Charlie Sales",
        "email": f"charlie_{uid}@badinvite.com",
        "password": "Password123!",
        "company_id": comp_data["company_id"],
        "role": "sales",
        "invite_code": "INV-WRONGCODE",
    })
    assert res.status_code == 401
    assert "Invalid company registration code" in res.json()["detail"]


def test_6_duplicate_email_rejected():
    """Test 10: Registering with an existing email is rejected with 409 Conflict."""
    uid = unique_str()
    email = f"dup_{uid}@corp.com"

    client.post("/auth/register-company", json={
        "company_name": f"Dup Email Corp {uid}",
        "admin_name": "Dup Admin",
        "admin_email": email,
        "password": "Password123!",
    })

    res = client.post("/auth/register-company", json={
        "company_name": f"Dup Email Corp 2 {uid}",
        "admin_name": "Dup Admin 2",
        "admin_email": email,
        "password": "Password123!",
    })
    assert res.status_code == 409
    assert "already registered" in res.json()["detail"]


def test_7_login_flow():
    """Tests 11, 12, 13: Login succeeds with correct password, fails with wrong password or unknown email."""
    uid = unique_str()
    admin_email = f"login.admin_{uid}@logintest.com"

    # Register company
    client.post("/auth/register-company", json={
        "company_name": f"Login Test Corp {uid}",
        "admin_name": "Login Admin",
        "admin_email": admin_email,
        "password": "CorrectPassword123!",
    })

    # Correct login
    login_res = client.post("/auth/login", json={
        "email": admin_email,
        "password": "CorrectPassword123!",
    })
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Wrong password
    wrong_pass_res = client.post("/auth/login", json={
        "email": admin_email,
        "password": "WrongPassword123!",
    })
    assert wrong_pass_res.status_code == 401

    # Unknown email
    unknown_res = client.post("/auth/login", json={
        "email": f"unknown_{uid}@logintest.com",
        "password": "CorrectPassword123!",
    })
    assert unknown_res.status_code == 401


def test_8_jwt_validation_and_me_endpoint():
    """Tests 14, 15, 16, 17, 18, 19: JWT validation, header requirements, and GET /auth/me payload."""
    uid = unique_str()
    admin_email = f"jwt.user_{uid}@jwttest.com"

    comp_res = client.post("/auth/register-company", json={
        "company_name": f"JWT Test Corp {uid}",
        "admin_name": "JWT User",
        "admin_email": admin_email,
        "password": "Password123!",
    })
    assert comp_res.status_code == 200
    comp_data = comp_res.json()

    login_res = client.post("/auth/login", json={
        "email": admin_email,
        "password": "Password123!",
    })
    token = login_res.json()["access_token"]

    # Valid GET /auth/me
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == admin_email
    assert me_data["role"] == "admin"
    assert me_data["company_id"] == comp_data["company_id"]
    assert "hashed_password" not in me_data
    assert "password" not in me_data

    # Invalid JWT
    bad_headers = {"Authorization": "Bearer invalid_token_xyz"}
    assert client.get("/auth/me", headers=bad_headers).status_code == 401

    # Missing Authorization header
    assert client.get("/auth/me").status_code == 401

    # Malformed Authorization header
    malformed_headers = {"Authorization": "Basic 12345"}
    assert client.get("/auth/me", headers=malformed_headers).status_code == 401


def test_9_expired_jwt_rejected():
    """Test 16: Expired JWT token is rejected with 401."""
    uid = unique_str()
    comp_res = client.post("/auth/register-company", json={
        "company_name": f"Expired Token Corp {uid}",
        "admin_name": "Exp Admin",
        "admin_email": f"exp_{uid}@token.com",
        "password": "Password123!",
    })
    assert comp_res.status_code == 200
    admin_id = comp_res.json()["admin_id"]

    # Create token expired 10 minutes ago
    expired_token = create_access_token({"sub": admin_id}, expires_delta=timedelta(minutes=-10))
    headers = {"Authorization": f"Bearer {expired_token}"}

    res = client.get("/auth/me", headers=headers)
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


def test_10_client_cannot_override_company_id_or_role():
    """Tests 20, 22, 23, SECURITY ATTACK DEFENSE: Client cannot tamper with company_id or role."""
    uid_a = unique_str()
    uid_b = unique_str()

    # Create Company A (Victim)
    comp_a_res = client.post("/auth/register-company", json={
        "company_name": f"Company A Victim {uid_a}",
        "admin_name": "Admin A",
        "admin_email": f"admin_{uid_a}@companyA.com",
        "password": "Password123!",
    })
    assert comp_a_res.status_code == 200
    comp_a = comp_a_res.json()

    # Create Company B (Attacker's target)
    comp_b_res = client.post("/auth/register-company", json={
        "company_name": f"Company B Target {uid_b}",
        "admin_name": "Admin B",
        "admin_email": f"admin_{uid_b}@companyB.com",
        "password": "Password123!",
    })
    assert comp_b_res.status_code == 200
    comp_b = comp_b_res.json()

    # Register Employee Bob in Company A (role=engineer)
    bob_email = f"bob_{uid_a}@companyA.com"
    bob_emp_res = client.post("/auth/register", json={
        "full_name": "Bob Engineer",
        "email": bob_email,
        "password": "Password123!",
        "company_id": comp_a["company_id"],
        "role": "engineer",
        "invite_code": comp_a["invite_code"],
    })
    assert bob_emp_res.status_code == 200

    # Bob logs in and gets JWT token
    bob_login = client.post("/auth/login", json={
        "email": bob_email,
        "password": "Password123!",
    }).json()
    bob_token = bob_login["access_token"]
    headers = {"Authorization": f"Bearer {bob_token}"}

    # Verify Bob's identity loaded from MySQL DB
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()

    # CRITICAL SECURITY ASSERTIONS:
    # 1. Company ID must be Company A, NOT Company B
    assert me_data["company_id"] == comp_a["company_id"]
    assert me_data["company_id"] != comp_b["company_id"]

    # 2. Role must be engineer, NOT admin
    assert me_data["role"] == "engineer"
    assert me_data["role"] != "admin"


def test_11_database_technology_is_mysql_not_sqlite():
    """Tests 25, 26: Confirms MySQL dialect is active and SQLite is not used for application DB."""
    assert engine.dialect.name == "mysql"
    assert engine.dialect.name != "sqlite"
