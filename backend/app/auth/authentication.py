from typing import Dict, Optional, List
from backend.app.auth.models import User

# Synthetic Demo Directory Users
DEMO_USERS: Dict[str, User] = {
    "user_001": User(
        id="user_001",
        name="Alice Johnson",
        email="alice.johnson@corp.internal",
        role="account_manager",
        department="sales",
        accessible_accounts=["ABC Corp", "XYZ Corp"],
    ),
    "user_002": User(
        id="user_002",
        name="Bob Williams",
        email="bob.williams@corp.internal",
        role="engineer",
        department="engineering",
        accessible_accounts=["XYZ Corp"],
    ),
    "user_003": User(
        id="user_003",
        name="Charlie Smith",
        email="charlie.smith@corp.internal",
        role="support_agent",
        department="support",
        accessible_accounts=["ABC Corp"],
    ),
    "admin_001": User(
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
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Look up user by ID. Returns None if user does not exist."""
        if not user_id:
            return None
        return DEMO_USERS.get(user_id.strip())

    @staticmethod
    def list_all_users() -> List[User]:
        """Returns list of all demo users."""
        return list(DEMO_USERS.values())
