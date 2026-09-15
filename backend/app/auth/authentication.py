import secrets
import logging
from typing import Dict, Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.models import Company, User as DBUser
from backend.app.auth.models import User as DemoUser
from backend.app.auth.security import hash_password, verify_password, create_access_token, decode_access_token
from backend.app.schemas.auth import (
    CompanyRegisterRequest,
    CompanyRegisterResponse,
    EmployeeRegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
)

logger = logging.getLogger("authentication")
security_scheme = HTTPBearer(auto_error=False)

# Allowed employee roles
ALLOWED_EMPLOYEE_ROLES = {"engineer", "hr", "sales", "support"}

# Synthetic Demo Directory Users (Preserved for test backwards-compatibility)
DEMO_USERS: Dict[str, DemoUser] = {
    "user_001": DemoUser(
        id="user_001",
        name="Alice Johnson",
        email="alice.johnson@corp.internal",
        role="account_manager",
        department="sales",
        accessible_accounts=["ABC Corp", "XYZ Corp"],
    ),
    "user_002": DemoUser(
        id="user_002",
        name="Bob Williams",
        email="bob.williams@corp.internal",
        role="engineer",
        department="engineering",
        accessible_accounts=["XYZ Corp"],
    ),
    "user_003": DemoUser(
        id="user_003",
        name="Charlie Smith",
        email="charlie.smith@corp.internal",
        role="support_agent",
        department="support",
        accessible_accounts=["ABC Corp"],
    ),
    "admin_001": DemoUser(
        id="admin_001",
        name="Admin",
        email="admin@corp.internal",
        role="admin",
        department="administration",
        accessible_accounts=["*"],
    ),
}


class UserService:
    """Authentication and user directory service for demo users."""

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[DemoUser]:
        """Look up user by ID. Returns None if user does not exist."""
        if not user_id:
            return None
        return DEMO_USERS.get(user_id.strip())

    @staticmethod
    def list_all_users() -> List[DemoUser]:
        """Returns list of all demo users."""
        return list(DEMO_USERS.values())


# ============================================================================
# MYSQL PERSISTENT AUTHENTICATION & BUSINESS LOGIC
# ============================================================================

def register_company_service(db: Session, req: CompanyRegisterRequest) -> CompanyRegisterResponse:
    """Bootstraps a new Company and initial Admin user inside a DB transaction."""
    # Check duplicate company name
    existing_company = db.query(Company).filter(Company.name == req.company_name.strip()).first()
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Company name '{req.company_name}' is already registered.",
        )

    # Check duplicate user email
    existing_user = db.query(DBUser).filter(DBUser.email == req.admin_email.strip().lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email address '{req.admin_email}' is already registered.",
        )

    # Generate random 8-character invite code for company
    raw_invite_code = f"INV-{secrets.token_hex(4).upper()}"
    hashed_invite = hash_password(raw_invite_code)
    hashed_admin_pass = hash_password(req.password)

    try:
        # Create company
        new_company = Company(
            name=req.company_name.strip(),
            invite_code_hash=hashed_invite,
        )
        db.add(new_company)
        db.flush()  # populate new_company.id

        # Create initial Admin user (role='admin' assigned strictly on server)
        new_admin = DBUser(
            company_id=new_company.id,
            email=req.admin_email.strip().lower(),
            hashed_password=hashed_admin_pass,
            full_name=req.admin_name.strip(),
            role="admin",
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_company)
        db.refresh(new_admin)

        return CompanyRegisterResponse(
            company_id=new_company.id,
            company_name=new_company.name,
            invite_code=raw_invite_code,
            admin_id=new_admin.id,
            admin_email=new_admin.email,
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error during company registration transaction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete company registration due to a server error.",
        )


def register_employee_service(db: Session, req: EmployeeRegisterRequest) -> UserResponse:
    """Registers an employee for an existing company after verifying company invite code."""
    role_clean = req.role.strip().lower()

    # Reject role = 'admin'
    if role_clean == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin role cannot be assigned during employee registration.",
        )

    # Validate allowed employee roles
    if role_clean not in ALLOWED_EMPLOYEE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid employee role '{req.role}'. Allowed roles: {sorted(list(ALLOWED_EMPLOYEE_ROLES))}",
        )

    # Query target company
    company = db.query(Company).filter(Company.id == req.company_id.strip()).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company ID '{req.company_id}' not found.",
        )

    # Verify company invite code
    if not company.invite_code_hash or not verify_password(req.invite_code.strip(), company.invite_code_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid company registration code.",
        )

    # Check duplicate email
    existing_user = db.query(DBUser).filter(DBUser.email == req.email.strip().lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email address '{req.email}' is already registered.",
        )

    hashed_emp_pass = hash_password(req.password)
    new_employee = DBUser(
        company_id=company.id,
        email=req.email.strip().lower(),
        hashed_password=hashed_emp_pass,
        full_name=req.full_name.strip(),
        role=role_clean,
    )

    try:
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)

        return UserResponse(
            id=new_employee.id,
            full_name=new_employee.full_name,
            email=new_employee.email,
            company_id=new_employee.company_id,
            role=new_employee.role,
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error during employee registration transaction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register employee due to a server error.",
        )


def login_user_service(db: Session, req: LoginRequest) -> TokenResponse:
    """Authenticates user against MySQL DB and returns signed JWT access token."""
    email_clean = req.email.strip().lower()
    user = db.query(DBUser).filter(DBUser.email == email_clean).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Generate JWT token with sub=user.id, company_id=user.company_id, role=user.role
    token_payload = {
        "sub": user.id,
        "company_id": user.company_id,
        "role": user.role,
    }
    access_token = create_access_token(token_payload)

    return TokenResponse(access_token=access_token, token_type="bearer")


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> DBUser:
    """Reusable FastAPI dependency extracting JWT token and loading authoritative User from MySQL."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token missing. Please provide Authorization: Bearer <token>.",
        )

    token = credentials.credentials.strip()
    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token: missing subject (user_id).",
        )

    # Load authoritative User directly from MySQL DB
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists in database.",
        )

    return user
