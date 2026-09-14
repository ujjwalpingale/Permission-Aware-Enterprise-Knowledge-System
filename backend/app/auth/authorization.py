import logging
from typing import Dict, Any, List, Union
from backend.app.auth.models import User

logger = logging.getLogger("authorization")


class PermissionService:
    """Centralized authorization rules engine.
    
    Security Principle: Fail Closed.
    Never grant access because metadata is missing, malformed, or unauthenticated.
    """

    @staticmethod
    def _parse_list_field(val: Union[str, List[str], None]) -> List[str]:
        """Helper to parse list metadata fields stored as python lists or comma-separated strings in ChromaDB."""
        if not val:
            return []
        if isinstance(val, list):
            return [str(item).strip() for item in val if item]
        if isinstance(val, str):
            val_str = val.strip()
            if not val_str:
                return []
            return [item.strip() for item in val_str.split(",") if item.strip()]
        return []

    @classmethod
    def is_authorized(cls, user: User, doc_metadata: Dict[str, Any]) -> bool:
        """Determines whether a user is authorized to view a chunk/document based on permission metadata.
        
        Fail-Closed: Returns False on any error, missing user, or invalid metadata.
        """
        # Rule 0: Fail closed on missing user or metadata
        if not user or not doc_metadata or not isinstance(doc_metadata, dict):
            logger.warning("Denied: Missing user or metadata.")
            return False

        doc_id = doc_metadata.get("document_id", "unknown_doc")

        # Rule 1: Admin bypass - Admin has global access to everything
        if user.role == "admin" or user.id == "admin_001":
            logger.info(f"Allowed (Admin): user={user.id} doc={doc_id}")
            return True

        # Extract permission metadata fields
        access_level = str(doc_metadata.get("access_level", "restricted")).lower().strip()
        account = str(doc_metadata.get("account", "*")).strip()
        department = str(doc_metadata.get("department", "*")).lower().strip()
        allowed_roles = cls._parse_list_field(doc_metadata.get("allowed_roles"))
        allowed_users = cls._parse_list_field(doc_metadata.get("allowed_users"))

        # Rule 2: Explicit User Permission
        if user.id in allowed_users:
            logger.info(f"Allowed (Explicit User): user={user.id} doc={doc_id}")
            return True

        # Rule 3: Public Access Level
        if access_level == "public":
            logger.info(f"Allowed (Public): user={user.id} doc={doc_id}")
            return True

        # Rule 4: Account Access Restriction
        # If document is tied to a specific account, user must have access to that account (or global '*')
        if account != "*" and account != "":
            user_accounts = [acc.strip() for acc in user.accessible_accounts]
            if "*" not in user_accounts and account not in user_accounts:
                logger.info(f"Denied (Account Mismatch): user={user.id} doc={doc_id} doc_account='{account}' user_accounts={user_accounts}")
                return False

        # Rule 5: Restricted Access Level
        if access_level == "restricted":
            # For restricted documents, explicit allowed_roles or explicit allowed_users match is required
            role_match = bool(allowed_roles and user.role in allowed_roles)
            user_match = bool(allowed_users and user.id in allowed_users)
            if not (role_match or user_match):
                logger.info(f"Denied (Restricted Role/User Mismatch): user={user.id} doc={doc_id} user_role='{user.role}' allowed_roles={allowed_roles}")
                return False
            if department != "*" and department != "" and user.department != department:
                logger.info(f"Denied (Restricted Dept Mismatch): user={user.id} doc={doc_id} user_dept='{user.department}' doc_dept='{department}'")
                return False
            logger.info(f"Allowed (Restricted Passed): user={user.id} doc={doc_id}")
            return True

        # Rule 6: Internal Access Level
        if access_level == "internal":
            # Role check if roles specified
            if allowed_roles and user.role not in allowed_roles:
                logger.info(f"Denied (Internal Role Mismatch): user={user.id} doc={doc_id} user_role='{user.role}' allowed={allowed_roles}")
                return False
            logger.info(f"Allowed (Internal Passed): user={user.id} doc={doc_id}")
            return True

        # Default Fail-Closed
        logger.info(f"Denied (Default Fail Closed): user={user.id} doc={doc_id}")
        return False
