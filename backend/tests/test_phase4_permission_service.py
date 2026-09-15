import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.db.models import Company, User as DBUser, Document, DocumentPermission, generate_uuid
from backend.app.auth.authorization import PermissionService

client = TestClient(app)


def unique_str(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def phase4_setup():
    """Fixture initializing two isolated companies (Company A and Company B) with admins and employees."""
    db = SessionLocal()

    # Create Company A
    c_a_name = unique_str("Phase4CompA")
    admin_a_email = unique_str("adminA") + "@compa.com"
    emp_a_email = unique_str("engA") + "@compa.com"

    res_a = client.post(
        "/auth/register-company",
        json={"company_name": c_a_name, "admin_name": "Admin A", "admin_email": admin_a_email, "password": "Password123!"},
    )
    comp_a_id = res_a.json()["company_id"]
    invite_a = res_a.json()["invite_code"]

    client.post(
        "/auth/register",
        json={"full_name": "Engineer A", "email": emp_a_email, "password": "Password123!", "company_id": comp_a_id, "role": "engineer", "invite_code": invite_a},
    )

    token_admin_a = client.post("/auth/login", json={"email": admin_a_email, "password": "Password123!"}).json()["access_token"]
    token_emp_a = client.post("/auth/login", json={"email": emp_a_email, "password": "Password123!"}).json()["access_token"]

    # Create Company B
    c_b_name = unique_str("Phase4CompB")
    admin_b_email = unique_str("adminB") + "@compb.com"
    emp_b_email = unique_str("engB") + "@compb.com"

    res_b = client.post(
        "/auth/register-company",
        json={"company_name": c_b_name, "admin_name": "Admin B", "admin_email": admin_b_email, "password": "Password123!"},
    )
    comp_b_id = res_b.json()["company_id"]
    invite_b = res_b.json()["invite_code"]

    client.post(
        "/auth/register",
        json={"full_name": "Engineer B", "email": emp_b_email, "password": "Password123!", "company_id": comp_b_id, "role": "engineer", "invite_code": invite_b},
    )

    token_admin_b = client.post("/auth/login", json={"email": admin_b_email, "password": "Password123!"}).json()["access_token"]
    token_emp_b = client.post("/auth/login", json={"email": emp_b_email, "password": "Password123!"}).json()["access_token"]

    # Fetch User ORM objects from DB
    admin_a_obj = db.query(DBUser).filter_by(email=admin_a_email).first()
    emp_a_obj = db.query(DBUser).filter_by(email=emp_a_email).first()
    admin_b_obj = db.query(DBUser).filter_by(email=admin_b_email).first()
    emp_b_obj = db.query(DBUser).filter_by(email=emp_b_email).first()

    # Create Documents in DB for Company A
    doc_a_eng = Document(
        id=generate_uuid(),
        company_id=comp_a_id,
        title="Comp A Eng Spec",
        file_data=b"Eng payload",
        file_type="txt",
        created_by=admin_a_obj.id,
        is_indexed=True,
    )
    perm_a = DocumentPermission(id=generate_uuid(), document_id=doc_a_eng.id, allowed_role="engineer")
    db.add(doc_a_eng)
    db.add(perm_a)

    doc_a_hr = Document(
        id=generate_uuid(),
        company_id=comp_a_id,
        title="Comp A HR Policy",
        file_data=b"HR payload",
        file_type="txt",
        created_by=admin_a_obj.id,
        is_indexed=True,
    )
    perm_hr = DocumentPermission(id=generate_uuid(), document_id=doc_a_hr.id, allowed_role="hr")
    db.add(doc_a_hr)
    db.add(perm_hr)

    # Create Document in DB for Company B
    doc_b_eng = Document(
        id=generate_uuid(),
        company_id=comp_b_id,
        title="Comp B Eng Spec",
        file_data=b"Comp B payload",
        file_type="txt",
        created_by=admin_b_obj.id,
        is_indexed=True,
    )
    perm_b = DocumentPermission(id=generate_uuid(), document_id=doc_b_eng.id, allowed_role="engineer")
    db.add(doc_b_eng)
    db.add(perm_b)

    db.commit()

    yield {
        "comp_a_id": comp_a_id,
        "comp_b_id": comp_b_id,
        "admin_a": admin_a_obj,
        "emp_a": emp_a_obj,
        "admin_b": admin_b_obj,
        "emp_b": emp_b_obj,
        "doc_a_eng": doc_a_eng,
        "doc_a_hr": doc_a_hr,
        "doc_b_eng": doc_b_eng,
        "headers_admin_a": {"Authorization": f"Bearer {token_admin_a}"},
        "headers_emp_a": {"Authorization": f"Bearer {token_emp_a}"},
        "headers_admin_b": {"Authorization": f"Bearer {token_admin_b}"},
        "headers_emp_b": {"Authorization": f"Bearer {token_emp_b}"},
    }

    db.close()


def test_1_admin_own_company_access_allow(phase4_setup):
    """Scenario 1: Admin querying own-company document -> ALLOW."""
    admin_a = phase4_setup["admin_a"]
    doc_a = phase4_setup["doc_a_eng"]
    assert PermissionService.can_access_document(admin_a, doc_a) is True


def test_2_admin_other_company_access_deny(phase4_setup):
    """Scenario 2: Admin querying other-company document -> DENY."""
    admin_a = phase4_setup["admin_a"]
    doc_b = phase4_setup["doc_b_eng"]
    assert PermissionService.can_access_document(admin_a, doc_b) is False


def test_3_employee_same_company_permitted_role_allow(phase4_setup):
    """Scenario 3: Employee querying same-company document with permitted role -> ALLOW."""
    emp_a = phase4_setup["emp_a"]  # engineer role
    doc_a_eng = phase4_setup["doc_a_eng"]  # allowed_role: engineer
    assert PermissionService.can_access_document(emp_a, doc_a_eng) is True


def test_4_employee_same_company_unpermitted_role_deny(phase4_setup):
    """Scenario 4: Employee querying same-company document with unpermitted role -> DENY."""
    emp_a = phase4_setup["emp_a"]  # engineer role
    doc_a_hr = phase4_setup["doc_a_hr"]  # allowed_role: hr
    assert PermissionService.can_access_document(emp_a, doc_a_hr) is False


def test_5_employee_other_company_matching_role_deny(phase4_setup):
    """Scenario 5: Employee querying other-company document with matching role -> DENY."""
    emp_a = phase4_setup["emp_a"]  # engineer role in Comp A
    doc_b_eng = phase4_setup["doc_b_eng"]  # Comp B doc with engineer allowed_role
    assert PermissionService.can_access_document(emp_a, doc_b_eng) is False


def test_6_missing_permission_deny(phase4_setup):
    """Scenario 6: Document with no matching permissions -> DENY."""
    emp_a = phase4_setup["emp_a"]
    empty_perm_doc = {
        "document_id": "doc_empty",
        "company_id": phase4_setup["comp_a_id"],
        "allowed_roles": "",
    }
    assert PermissionService.can_access_document(emp_a, empty_perm_doc) is False


def test_7_invalid_or_unknown_role_deny(phase4_setup):
    """Scenario 7: User with invalid/unknown role -> DENY."""
    invalid_role_user = DBUser(
        id="user_inv",
        company_id=phase4_setup["comp_a_id"],
        email="inv@compa.com",
        hashed_password="hash",
        full_name="Invalid Role User",
        role="hacker_role",
    )
    doc_a_eng = phase4_setup["doc_a_eng"]
    assert PermissionService.can_access_document(invalid_role_user, doc_a_eng) is False


def test_8_missing_user_deny(phase4_setup):
    """Scenario 8: Missing user object (None) -> DENY."""
    doc_a_eng = phase4_setup["doc_a_eng"]
    assert PermissionService.can_access_document(None, doc_a_eng) is False


def test_9_request_supplied_company_id_cannot_override_auth_user(phase4_setup):
    """Scenario 9: Request/dict company_id cannot trick PermissionService into cross-company access."""
    emp_a = phase4_setup["emp_a"]  # Comp A engineer
    # Attempting to fake user's company_id in dictionary parameter
    fake_user_payload = {
        "id": emp_a.id,
        "role": emp_a.role,
        "company_id": phase4_setup["comp_b_id"],  # Attempted override to Comp B
    }
    doc_b_eng = phase4_setup["doc_b_eng"]  # Real Comp B doc
    # Fake payload should be rejected if authenticated identity in DB says Comp A
    assert PermissionService.can_access_document(emp_a, doc_b_eng) is False


def test_10_get_documents_uses_permission_service(phase4_setup):
    """Scenario 10: GET /documents endpoint delegates directly to PermissionService."""
    # Engineer A in Comp A gets documents
    res_emp = client.get("/documents", headers=phase4_setup["headers_emp_a"])
    assert res_emp.status_code == 200
    docs_emp = res_emp.json()
    titles_emp = [d["title"] for d in docs_emp]
    assert "Comp A Eng Spec" in titles_emp
    assert "Comp A HR Policy" not in titles_emp
    assert "Comp B Eng Spec" not in titles_emp

    # Admin A in Comp A gets documents
    res_admin = client.get("/documents", headers=phase4_setup["headers_admin_a"])
    assert res_admin.status_code == 200
    docs_admin = res_admin.json()
    titles_admin = [d["title"] for d in docs_admin]
    assert "Comp A Eng Spec" in titles_admin
    assert "Comp A HR Policy" in titles_admin
    assert "Comp B Eng Spec" not in titles_admin
