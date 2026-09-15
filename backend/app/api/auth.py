from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.models import User as DBUser
from backend.app.auth.authentication import (
    register_company_service,
    register_employee_service,
    login_user_service,
    get_current_user,
)
from backend.app.schemas.auth import (
    CompanyRegisterRequest,
    CompanyRegisterResponse,
    EmployeeRegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register-company", response_model=CompanyRegisterResponse)
def register_company_endpoint(req: CompanyRegisterRequest, db: Session = Depends(get_db)):
    """Bootstrap endpoint creating a new Company and its initial Admin user."""
    return register_company_service(db=db, req=req)


@router.post("/register", response_model=UserResponse)
def register_employee_endpoint(req: EmployeeRegisterRequest, db: Session = Depends(get_db)):
    """Endpoint for registering an employee for an existing company after invite verification."""
    return register_employee_service(db=db, req=req)


@router.post("/login", response_model=TokenResponse)
def login_endpoint(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates user credentials against MySQL and returns a JWT access token."""
    return login_user_service(db=db, req=req)


@router.get("/me", response_model=UserResponse)
def get_me_endpoint(current_user: DBUser = Depends(get_current_user)):
    """Returns safe profile information for the authenticated user from MySQL DB."""
    return UserResponse(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        company_id=current_user.company_id,
        role=current_user.role,
    )
