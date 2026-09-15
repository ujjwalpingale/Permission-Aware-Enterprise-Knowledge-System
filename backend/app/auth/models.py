from typing import List
from pydantic import BaseModel, Field


class User(BaseModel):
    """Synthetic user model for permission-aware access control."""

    id: str = Field(..., description="Unique user identifier e.g. user_001")
    name: str = Field(..., description="User full name e.g. Alice Johnson")
    email: str = Field(default="user@corp.internal", description="User corporate email address")
    role: str = Field(..., description="User role e.g. engineer, account_manager, support_agent, admin")
    company_id: str = Field(default="comp_a", description="Company ID for multi-tenant isolation")
    accessible_accounts: List[str] = Field(
        default_factory=list,
        description="List of accounts user is authorized to access e.g. ['ABC Corp', '*']",
    )
