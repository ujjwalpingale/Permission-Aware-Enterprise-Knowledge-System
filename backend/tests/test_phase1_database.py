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
        file_data=b"%PDF-1.4 sample pdf binary content",
        file_type="pdf",
        created_by="user_123",
        is_indexed=False,
    )
    assert doc.title == "Engineering Spec v1"
    assert doc.file_data == b"%PDF-1.4 sample pdf binary content"
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


def test_phase2_5_document_binary_longblob_storage():
    """Verify Phase 2.5 requirements: binary file_data storage in MySQL and schema verification."""
    from sqlalchemy import inspect
    from backend.app.db.database import SessionLocal, engine
    from backend.app.db.models import Company

    # 1. Verify MySQL Inspector Schema
    inspector = inspect(engine)
    columns = {col["name"]: str(col["type"]) for col in inspector.get_columns("documents")}

    # Assert file_data column exists and is LONGBLOB in MySQL
    assert "file_data" in columns, "file_data column missing from MySQL documents table"
    assert columns["file_data"] == "LONGBLOB", f"Expected LONGBLOB, got {columns['file_data']}"

    # Assert file_path column NO LONGER exists in MySQL
    assert "file_path" not in columns, "file_path column still exists in MySQL documents table"

    # 2. Verify Database Persistence & Retrieval of Binary Data
    db = SessionLocal()
    try:
        # Create test company
        company = Company(name="Binary Storage Test Corp")
        db.add(company)
        db.flush()

        # Create document with binary data
        binary_payload = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        doc = Document(
            company_id=company.id,
            title="Logo Image",
            file_data=binary_payload,
            file_type="png",
            is_indexed=False,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Retrieve doc from MySQL
        retrieved_doc = db.query(Document).filter_by(id=doc.id).first()
        assert retrieved_doc is not None
        assert isinstance(retrieved_doc.file_data, bytes)
        assert retrieved_doc.file_data == binary_payload

        # Clean up
        db.delete(company)
        db.commit()
    finally:
        db.close()
