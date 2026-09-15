import pytest
from backend.app.db.models import Company, User, Document, DocumentPermission
from backend.app.auth.security import hash_password, verify_password


def test_phase1_models_instantiation():
    """Verify Phase 1 SQLAlchemy ORM models initialize correctly with UUID keys and attributes."""
    company = Company(name="Acme Corp")
    assert company.name == "Acme Corp"

    user = User(
        company_id="comp_123",
        email="test.user@acme.com",
        hashed_password="hashed_pwd_secret",
        full_name="Test User",
        role="engineer",
    )
    assert user.role == "engineer"
    assert user.email == "test.user@acme.com"

    doc = Document(
        company_id="comp_123",
        title="Engineering Spec v1",
        file_path="/docs/eng_v1.pdf",
        file_type="pdf",
        created_by="user_123",
        is_indexed=False,
    )
    assert doc.title == "Engineering Spec v1"
    assert doc.is_indexed is False

    perm = DocumentPermission(
        document_id="doc_123",
        allowed_role="engineer",
    )
    assert perm.allowed_role == "engineer"


def test_phase1_password_hashing():
    """Verify Phase 1 bcrypt password hashing and verification logic."""
    raw_pass = "SecureP@ssw0rd!2026"
    hashed = hash_password(raw_pass)

    assert hashed != raw_pass
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_phase1_empty_password_handling():
    """Verify fail-closed validation for empty password parameters."""
    assert verify_password("", "") is False
    assert verify_password("pass", "") is False
    assert verify_password("", "hashed") is False
    with pytest.raises(ValueError):
        hash_password("")
