import logging
from typing import Dict, Any, List, Union, Optional

logger = logging.getLogger("authorization")

VALID_EMPLOYEE_ROLES = {"engineer", "hr", "sales", "support"}


class PermissionService:
    """Centralized, single authoritative document permission service.

    Security Principle: Fail Closed.
    Never grant access if user, document, company_id, or role permissions are missing or mismatching.
    """

    @staticmethod
    def _parse_list_field(val: Union[str, List[str], None]) -> List[str]:
        """Helper to parse role metadata fields stored as lists or comma-separated strings."""
        if not val:
            return []
        if isinstance(val, list):
            return [str(item).strip().lower() for item in val if item]
        if isinstance(val, str):
            val_str = val.strip()
            if not val_str:
                return []
            return [item.strip().lower() for item in val_str.split(",") if item.strip()]
        return []

    @classmethod
    def can_access_document(
        cls,
        user: Any,
        document: Any,
        db: Any = None,
    ) -> bool:
        """Single authoritative method to determine if a user can access a document.

        Checks:
        1. Fail Closed (user, document, user_id, user_role, user_company_id must exist).
        2. Strict Multi-Tenant Company Boundary (user.company_id == document.company_id).
        3. Admin Access (Admin has access to all documents in their own company).
        4. Employee Access (Employee role must match document's allowed_roles).
        """
        # 1. Fail Closed: missing user or document
        if user is None or document is None:
            logger.warning("Denied: Missing user or document object.")
            return False

        # Extract user fields safely
        user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
        user_company_id = getattr(user, "company_id", None) or (user.get("company_id") if isinstance(user, dict) else None)
        user_role_raw = getattr(user, "role", None) or (user.get("role") if isinstance(user, dict) else None)

        if not user_id or not user_company_id or not user_role_raw:
            logger.warning(f"Denied: User missing required attributes (id={user_id}, company_id={user_company_id}, role={user_role_raw}).")
            return False

        user_role = str(user_role_raw).lower().strip()

        # Extract document fields safely
        doc_company_id = None
        doc_allowed_roles: List[str] = []

        if isinstance(document, dict):
            # Document dictionary or ChromaDB chunk metadata
            doc_company_id = document.get("company_id")
            doc_allowed_roles = cls._parse_list_field(document.get("allowed_roles"))

        elif hasattr(document, "company_id"):
            # SQLAlchemy Document ORM object
            doc_company_id = getattr(document, "company_id", None)
            if hasattr(document, "permissions") and document.permissions:
                doc_allowed_roles = [p.allowed_role.lower().strip() for p in document.permissions if hasattr(p, "allowed_role")]
            else:
                doc_allowed_roles = cls._parse_list_field(getattr(document, "allowed_roles", None))

        elif isinstance(document, str) and db is not None:
            # Document ID passed as string with active db session
            from backend.app.db.models import Document
            doc_obj = db.query(Document).filter(Document.id == document).first()
            if not doc_obj:
                logger.warning(f"Denied: Document ID '{document}' not found in database.")
                return False
            doc_company_id = doc_obj.company_id
            doc_allowed_roles = [p.allowed_role.lower().strip() for p in doc_obj.permissions]

        else:
            logger.warning("Denied: Unrecognized document object format.")
            return False

        if not doc_company_id:
            logger.warning("Denied: Document missing company_id.")
            return False

        # 2. Strict Multi-Tenant Company Boundary Check (FIRST RULE)
        if user_company_id != doc_company_id:
            logger.info(
                f"Denied (Cross-Company Access Attempt): user={user_id} user_company='{user_company_id}' doc_company='{doc_company_id}'"
            )
            return False

        # 3. Admin Access Rule (Same Company)
        if user_role == "admin":
            logger.info(f"Allowed (Admin Same Company): user={user_id} company={user_company_id}")
            return True

        # 4. Employee Access Rule (Role Match)
        if user_role not in VALID_EMPLOYEE_ROLES:
            logger.warning(f"Denied (Invalid Employee Role): user={user_id} role='{user_role}'")
            return False

        if user_role in doc_allowed_roles:
            logger.info(f"Allowed (Employee Role Match): user={user_id} role='{user_role}' doc_roles={doc_allowed_roles}")
            return True

        logger.info(f"Denied (Employee Role Mismatch): user={user_id} role='{user_role}' doc_roles={doc_allowed_roles}")
        return False

    @classmethod
    def is_authorized(cls, user: Any, doc_metadata: Any, db: Any = None) -> bool:
        """Delegates directly to canonical can_access_document method to maintain single authorization rule set."""
        return cls.can_access_document(user=user, document=doc_metadata, db=db)
