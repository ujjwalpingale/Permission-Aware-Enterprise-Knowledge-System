# Permission-Aware Enterprise Knowledge System

> **Security & System Status: Production Ready (Passed 87/87 Automated Security & RAG Tests)**  
> *A secure multi-tenant enterprise RAG system where authorization is enforced BEFORE vector retrieval so unauthorized document chunks never reach the LLM.*

---

## 📖 System Overview

The **Permission-Aware Enterprise Knowledge System** enables organization employees to query enterprise knowledge bases using natural language and receive grounded answers with verifiable source citations — **strictly limited to documents they are authorized to access**.

### Differentiating Security Feature: True Pre-Retrieval Authorization
Unlike traditional RAG systems that retrieve a broad pool of candidate documents and attempt to filter or censor results after vector search (or rely on LLM system prompts for authorization), this system generates native metadata filters **before** vector search occurs.

ChromaDB performs vector similarity distance calculations **strictly on chunks matching the authenticated user's tenant (`company_id`) and role permissions (`role_<role> = True`)**. Unauthorized document chunks are physically excluded before vector search candidate results are returned.

---

## 🏗️ Core Architecture & Data Flow

```mermaid
flowchart TD
    A[User / Client] -->|HTTP + Authorization: Bearer JWT| B[Streamlit Frontend app.py]
    B -->|REST API Request| C[FastAPI Backend main.py]
    C -->|get_current_user Dependency| D[MySQL DBUser Lookup]
    D -->|Authoritative DBUser Object| E[RAGService & StandardRetriever]
    E -->|Generate auth_filter| F[PermissionService.get_retrieval_filter]
    F -->|Filter Dict: company_id + role_flags| E
    E -->|Native Filtered Similarity Search| G[(ChromaDB Vector Store)]
    G -->|Only Authorized Candidate Chunks| E
    E -->|Build Context String| H[Context Assembly & Prompt Defense]
    H -->|Filtered Context + Question| I[Google Gemini LLM]
    I -->|Grounded Answer| H
    H -->|Answer + Authorized Citations| C
    C -->|HTTP Response| B
    B -->|Render Answer & Source Badges| A
```

---

## 🛡️ Multi-Tenant & Role-Based Access Control (RBAC)

### 1. Multi-Tenant Isolation
- Documents and users belong strictly to a single tenant (`company_id`).
- A user from **Company A** can never retrieve, view, or query documents belonging to **Company B**.
- Cross-tenant queries are blocked natively at database query time, pre-retrieval vector search time, and authorization engine evaluation.

### 2. Admin Access
- Authenticated **Admin** users (`role = "admin"`) receive access to all indexed documents belonging to their own company (`company_id`).
- Admins are prohibited from accessing documents belonging to other companies.
- Admin is the only role permitted to upload documents (`POST /documents/upload`).

### 3. Employee Access
- Authenticated **Employee** access requires **both**:
  1. Same Tenant Boundary (`user.company_id == document.company_id`)
  2. Document Role Permission (`role_<user_role> == True` on the document chunk)
- Supported employee roles:
  - `engineer`
  - `hr`
  - `sales`
  - `support`
- Employee registration requires a valid Company ID and Company Invite Code generated during Admin bootstrap.

### 4. Single Authoritative Engine
- Frontend role checks are **UI/UX conveniences only**.
- The backend `PermissionService.can_access_document()` and `PermissionService.get_retrieval_filter()` methods serve as the single, non-bypassable authorization authority.

---

## 🗄️ Database & Vector Storage Architecture

### 1. MySQL Application Database (`enterprise_rag_db`)
- **Source of Truth**: Manages `companies`, `users`, `documents`, and `document_permissions`.
- **ORM & Migrations**: SQLAlchemy ORM with `pymysql` driver and Alembic migration authority (`alembic upgrade head`).
- **Binary Payload Storage**: Original document payloads are stored as MySQL `LONGBLOB` (`documents.file_data`).
- **Path Column Removal**: No local `file_path` storage is used.
- **Application DB**: **SQLite is NOT used as the application database.**

### 2. ChromaDB Persistent Vector Store (`backend/chroma_db`)
- **Metadata Fields**: Every indexed document chunk contains:
  - `document_id`
  - `company_id`
  - `allowed_roles` (comma-separated string for display)
  - `title`
  - `file_type`
  - Explicit boolean role flags: `role_engineer`, `role_hr`, `role_sales`, `role_support`
- **Fail-Closed Handling**: Employee retrieval queries require `role_<role> = True`. Any legacy or malformed chunks lacking explicit boolean flags automatically fail pre-retrieval filtering.

---

## 📥 Document Ingestion Pipeline

```
Admin Uploads File (POST /documents/upload)
       │
       ▼
FastAPI validates JWT + Admin role
       │
       ▼
Original binary stored in MySQL LONGBLOB (documents.file_data)
       │
       ▼
In-Memory Text Extraction (DocumentLoader)
       │
       ▼
Document Chunking (DocumentChunker)
       │
       ▼
Google Gemini Embeddings (models/text-embedding-004)
       │
       ▼
ChromaDB Vector Store Indexing with Boolean Role Flags
       │
       ▼
Mark is_indexed = True in MySQL
```
*If ChromaDB indexing fails, the original binary remains safe in MySQL with `is_indexed = False` for re-indexing.*

---

## 🔍 Secure RAG Query Pipeline & Zero-Context Behavior

```
User Query (POST /chat with Bearer JWT)
       │
       ▼
FastAPI decodes JWT & loads DBUser from MySQL
       │
       ▼
PermissionService.get_retrieval_filter(user)
       │
       ├─► Admin:    {"company_id": user.company_id}
       └─► Employee: {"$and": [{"company_id": user.company_id}, {f"role_{user.role}": True}]}
       │
       ▼
ChromaDB Native Vector Similarity Search (filter=auth_filter)
       │
       ▼
Are Authorized Chunks Returned?
       │
       ├─► YES: Build Context ──► Gemini LLM ──► Grounded Answer + Citations
       │
       └─► NO:  Return NO_ANSWER_MESSAGE (LLM IS NOT CALLED)
```

---

## 🔌 Core API Endpoints

### Authentication
- `POST /auth/register-company`: Bootstraps new company and initial Admin user. Returns Company Invite Code.
- `POST /auth/register`: Registers employees using company invite code and role selection.
- `POST /auth/login`: Authenticates email/password and returns signed JWT `access_token`.
- `GET /auth/me`: Returns current authenticated user profile from MySQL.

### Documents
- `POST /documents/upload`: Admin-only document upload endpoint (multipart form data). Persists binary to MySQL `LONGBLOB` and indexes ChromaDB.
- `GET /documents`: Returns company documents authorized for the authenticated user's company and role.

### RAG & System
- `POST /chat`: Permission-aware RAG query endpoint requiring Bearer JWT.
- `GET /health`: Health status endpoint.

---

## 🛠️ Environment Configuration

Copy `backend/.env.example` to `backend/.env` and configure:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_CHAT_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=models/text-embedding-004
CHROMA_PERSIST_DIRECTORY=./backend/chroma_db
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/enterprise_rag_db
JWT_SECRET_KEY=your_jwt_secret_key_here
CHUNK_SIZE=800
CHUNK_OVERLAP=100
TOP_K=5
```

---

## 🚀 Local Setup & Quickstart Guide

### 1. Prerequisites
- Python 3.13+
- MySQL Server 8.0+ running on `localhost:3306` with database `enterprise_rag_db`

### 2. Install Dependencies
```bash
# Activate Python Virtual Environment
.venv\Scripts\activate

# Install backend & frontend packages
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 3. Database Migration
```bash
.venv\Scripts\alembic upgrade head
```

### 4. Launch Backend API
```bash
.venv\Scripts\uvicorn backend.app.main:app --reload --port 8000
```

### 5. Launch Frontend Dashboard
```bash
.venv\Scripts\streamlit run frontend/app.py
```

Open `http://localhost:8501` to access the interactive web interface.

---

## 🧪 Automated Testing & Verification

Run the full 87-test automated test suite:

```bash
.venv\Scripts\pytest backend/tests/
```

- **Test Suite Result**: **87 / 87 PASSED** (0 failures).

---

## 📋 Production Security Checklist

- [x] Strong JWT Secret configured (`JWT_SECRET_KEY`)
- [x] Pre-retrieval vector authorization filtering verified (`filter=auth_filter`)
- [x] Multi-tenant isolation verified (`company_id`)
- [x] Admin-only document upload enforced (`POST /documents/upload`)
- [x] Deleted insecure `/upload` endpoint verified removed (404)
- [x] Zero-context short-circuiting verified (LLM not invoked when 0 chunks matched)
- [x] Prompt injection defense headers applied to context strings
- [x] Request payload identity tampering blocked (JWT authority)
- [x] Original document binary persistence in MySQL `LONGBLOB` verified
- [x] SQLite application database excluded
- [x] All 87 backend security, auth, database, and RAG tests passing
