import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Index, LargeBinary
from sqlalchemy.orm import relationship

from backend.app.db.database import Base


def generate_uuid() -> str:
    """Generates string representation of UUID4."""
    return str(uuid.uuid4())


def utc_now():
    """Returns current UTC datetime."""
    return datetime.now(timezone.utc)


class Company(Base):
    """Multi-tenant Company ORM Model."""

    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True, index=True)
    invite_code_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company(id='{self.id}', name='{self.name}')>"


class User(Base):
    """User ORM Model for enterprise authentication and permission context."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)  # e.g., 'admin', 'engineer', 'hr', 'sales', 'support'
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="users")
    documents_created = relationship("Document", back_populates="creator")

    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', role='{self.role}', company_id='{self.company_id}')>"


class Document(Base):
    """Document ORM Model tracking company scope, file details, and indexing status."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    file_data = Column(LargeBinary, nullable=True)
    file_type = Column(String(50), nullable=True)  # e.g., 'pdf', 'md', 'txt', 'json'
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_indexed = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="documents")
    creator = relationship("User", back_populates="documents_created")
    permissions = relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id='{self.id}', title='{self.title}', company_id='{self.company_id}', is_indexed={self.is_indexed})>"


class DocumentPermission(Base):
    """Document Role Permission ORM Model mapping allowed employee roles per document."""

    __tablename__ = "document_permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    allowed_role = Column(String(50), nullable=False, index=True)  # e.g., 'engineer', 'hr', 'sales', 'support'

    # Relationships
    document = relationship("Document", back_populates="permissions")

    # Index for fast combined lookup
    __table_args__ = (
        Index("idx_doc_role", "document_id", "allowed_role", unique=True),
    )

    def __repr__(self):
        return f"<DocumentPermission(id='{self.id}', document_id='{self.document_id}', allowed_role='{self.allowed_role}')>"
