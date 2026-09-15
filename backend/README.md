# Backend — Permission-Aware Enterprise Knowledge System API Service

FastAPI backend service providing multi-tenant JWT authentication, MySQL binary document persistence (`LONGBLOB`), ChromaDB vector store integration with pre-retrieval authorization filtering, and Google Gemini RAG completions.

## Features
- **JWT Multi-Tenant Authentication**: `POST /auth/register-company`, `POST /auth/register`, `POST /auth/login`, `GET /auth/me`.
- **Authoritative Permission Engine**: `PermissionService` enforces single-source fail-closed authorization rules.
- **Pre-Retrieval Vector Filtering**: Passes native metadata filters (`company_id` and `role_<role> = True`) directly to ChromaDB prior to candidate calculation.
- **MySQL LONGBLOB Document Persistence**: Original uploaded files stored as MySQL `LONGBLOB` (`documents.file_data`).
- **Admin-Only Ingestion**: `POST /documents/upload` restricts document uploads to Admins, splitting and indexing embeddings in ChromaDB with explicit boolean role flags.
- **Prompt Injection Defense**: Delimited context boundaries (`<<<BEGIN RETRIEVED CONTEXT DATA>>>`) and strict LLM instructions.

## Directory Layout
- `app/main.py`: FastAPI application entrypoint.
- `app/api/`:
  - `auth.py`: Company/Employee registration, login, profile endpoints.
  - `documents.py`: Admin document upload (`POST /documents/upload`) & document listing (`GET /documents`).
  - `chat.py`: Permission-aware chat endpoint (`POST /chat`).
- `app/auth/`:
  - `authentication.py`: JWT decoding, password hashing, `get_current_user` dependency.
  - `authorization.py`: `PermissionService` authorization logic & `get_retrieval_filter`.
  - `security.py`: JWT token creation/decoding functions.
- `app/db/`:
  - `database.py`: SQLAlchemy engine & session factory (`enterprise_rag_db`).
  - `models.py`: SQLAlchemy models (`Company`, `User`, `Document`, `DocumentPermission`).
- `app/rag/`: Core RAG components (`loaders`, `chunker`, `embeddings`, `vector_store`, `retriever`, `prompts`).
- `app/services/`: Service orchestrators (`ingestion_service`, `retrieval_service`, `rag_service`).
- `tests/`: 87 automated unit, authorization, and RAG security tests.

## Execution

```bash
# Apply Database Migrations
alembic upgrade head

# Run API Server
uvicorn backend.app.main:app --reload --port 8000
```
