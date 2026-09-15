from pydantic import BaseModel, EmailStr, Field, ConfigDict


class CompanyRegisterRequest(BaseModel):
    """Request payload for bootstrapping a company and its initial Admin."""

    company_name: str = Field(..., min_length=2, max_length=255, description="Unique company name")
    admin_name: str = Field(..., min_length=2, max_length=255, description="Full name of initial admin")
    admin_email: EmailStr = Field(..., description="Unique email of initial admin")
    password: str = Field(..., min_length=6, max_length=128, description="Admin password")


class CompanyRegisterResponse(BaseModel):
    """Response payload returned upon successful company creation."""

    company_id: str
    company_name: str
    invite_code: str = Field(..., description="Company invite code for employee registration")
    admin_id: str
    admin_email: str


class EmployeeRegisterRequest(BaseModel):
    """Request payload for registering an employee under an existing company."""

    full_name: str = Field(..., min_length=2, max_length=255, description="Full name of employee")
    email: EmailStr = Field(..., description="Unique email of employee")
    password: str = Field(..., min_length=6, max_length=128, description="Employee password")
    company_id: str = Field(..., description="Target company ID to join")
    role: str = Field(..., description="Employee role (engineer, hr, sales, support)")
    invite_code: str = Field(..., description="Company verification invite code")


class LoginRequest(BaseModel):
    """Request payload for user authentication."""

    email: EmailStr = Field(..., description="Registered user email")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """JWT Token response payload."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Safe user profile response payload excluding sensitive credentials."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: str
    company_id: str
    role: str

