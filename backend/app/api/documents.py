import json
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.database import get_db
from backend.app.db.models import User, Document, DocumentPermission, generate_uuid
from backend.app.auth.authentication import get_current_user
from backend.app.schemas.documents import DocumentResponse, DocumentUploadResponse
from backend.app.rag.loaders import DocumentLoader
from backend.app.rag.chunker import DocumentChunker
from backend.app.rag.embeddings import get_embedding_function
from backend.app.rag.vector_store import VectorStoreManager

logger = logging.getLogger("documents_api")

router = APIRouter(prefix="/documents", tags=["Documents"])

VALID_EMPLOYEE_ROLES = {"engineer", "hr", "sales", "support"}
SUPPORTED_EXTENSIONS = {".md", ".markdown", ".txt", ".json", ".pdf"}


def parse_allowed_roles(allowed_roles_input: str) -> List[str]:
    """Parses and validates allowed employee roles from form input string."""
    if not allowed_roles_input or not allowed_roles_input.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one allowed employee role must be provided.",
        )

    raw_str = allowed_roles_input.strip()
    if raw_str.startswith("[") and raw_str.endswith("]"):
        try:
            parsed = json.loads(raw_str)
            roles = [str(r).strip() for r in parsed if str(r).strip()]
        except Exception:
            roles = [r.strip() for r in raw_str.strip("[]").split(",") if r.strip()]
    else:
        roles = [r.strip() for r in raw_str.split(",") if r.strip()]

    if not roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one allowed employee role must be provided.",
        )

    for role in roles:
        if role.lower() == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role 'admin' cannot be required as a document permission. Admins automatically access all company documents.",
            )
        if role.lower() not in VALID_EMPLOYEE_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid employee role '{role}'. Allowed roles: {', '.join(sorted(VALID_EMPLOYEE_ROLES))}.",
            )

    return sorted(list(set(roles)))


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    allowed_roles: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin-only document upload endpoint supporting MySQL LONGBLOB storage and ChromaDB indexing."""
    # 1. Role enforcement: Admin only
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can upload documents.",
        )

    # 2. Parse and validate allowed employee roles
    validated_roles = parse_allowed_roles(allowed_roles)

    # 3. Read uploaded file bytes and validate extension
    filename = file.filename or "document.txt"
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}.",
        )

    doc_title = title.strip() if (title and title.strip()) else Path(filename).stem.replace("_", " ").title()
    file_type = ext.lstrip(".")

    # 4. Create MySQL Document record (company_id strictly from current_user)
    doc_id = generate_uuid()
    new_doc = Document(
        id=doc_id,
        company_id=current_user.company_id,
        title=doc_title,
        file_data=file_bytes,
        file_type=file_type,
        created_by=current_user.id,
        is_indexed=False,
    )
    db.add(new_doc)

    # 5. Add DocumentPermission records
    for role in validated_roles:
        perm = DocumentPermission(
            id=generate_uuid(),
            document_id=doc_id,
            allowed_role=role,
        )
        db.add(perm)

    try:
        db.commit()
        db.refresh(new_doc)
    except Exception as e:
        db.rollback()
        logger.error(f"Database error during document creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist document to database: {str(e)}",
        )

    # 6. In-memory text extraction, chunking, and ChromaDB vector indexing
    try:
        doc_metadata = {
            "document_id": new_doc.id,
            "company_id": current_user.company_id,
            "allowed_roles": ",".join(validated_roles),
            "title": doc_title,
            "file_type": file_type,
            "source_type": f"{file_type}_document",
        }

        loaded_docs = DocumentLoader.load_bytes(
            file_bytes=file_bytes,
            filename=filename,
            metadata=doc_metadata,
        )

        chunker = DocumentChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        chunks = chunker.split_documents(loaded_docs)

        # Ensure explicit ChromaDB metadata fields on all chunks
        for chunk in chunks:
            chunk.metadata["document_id"] = new_doc.id
            chunk.metadata["company_id"] = current_user.company_id
            chunk.metadata["allowed_roles"] = ",".join(validated_roles)
            chunk.metadata["title"] = doc_title
            chunk.metadata["file_type"] = file_type

        embedding_fn = get_embedding_function(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_EMBEDDING_MODEL,
        )
        vector_store = VectorStoreManager(
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            embedding_function=embedding_fn,
        )
        vector_store.add_documents(chunks)

        # Mark document as successfully indexed upon completion
        new_doc.is_indexed = True
        db.commit()
        db.refresh(new_doc)

    except Exception as e:
        # ChromaDB indexing failed — keep is_indexed = False in MySQL
        logger.error(f"ChromaDB indexing failed for document {new_doc.id}: {e}")
        db.rollback()
        # Return response with is_indexed=False and HTTP 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document stored in database, but vector indexing failed: {str(e)}",
        )

    doc_response = DocumentResponse(
        id=new_doc.id,
        company_id=new_doc.company_id,
        title=new_doc.title,
        file_type=new_doc.file_type,
        created_by=new_doc.created_by,
        is_indexed=new_doc.is_indexed,
        created_at=new_doc.created_at,
        allowed_roles=validated_roles,
    )

    return DocumentUploadResponse(
        message="Document uploaded and indexed successfully.",
        document=doc_response,
    )


@router.get("", response_model=List[DocumentResponse])
def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves company documents scoped to authenticated user's company and role permissions."""
    if current_user.role == "admin":
        # Admin can view all documents belonging to their company
        docs = db.query(Document).filter(Document.company_id == current_user.company_id).all()
    else:
        # Employee can view company documents where they hold matching role permission
        docs = (
            db.query(Document)
            .join(DocumentPermission)
            .filter(
                Document.company_id == current_user.company_id,
                DocumentPermission.allowed_role == current_user.role,
            )
            .all()
        )

    results = []
    for doc in docs:
        allowed_roles = [p.allowed_role for p in doc.permissions]
        results.append(
            DocumentResponse(
                id=doc.id,
                company_id=doc.company_id,
                title=doc.title,
                file_type=doc.file_type,
                created_by=doc.created_by,
                is_indexed=doc.is_indexed,
                created_at=doc.created_at,
                allowed_roles=allowed_roles,
            )
        )

    return results
