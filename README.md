# Permission-Aware Enterprise RAG System

> **Current Phase: Phase 2 — Authentication & Permission-Aware Retrieval (Powered by Google Gemini)**  
> *Note: Pre-LLM security enforcement, synthetic RBAC user profiles, fail-closed authorization rules, document permission metadata, and authorized citation delivery are fully operational.*

---

## 📖 Overview

The **Permission-Aware Enterprise RAG System** allows enterprise employees to query internal knowledge bases (project documentation, support tickets, Slack channels) with natural language questions and receive accurate, grounded answers accompanied by verifiable source citations — **strictly limited to documents they are authorized to view**.

### Phase 2 Key Features:
- **Pre-LLM Authorization Filtering (Fail-Closed)**: Vector candidates are filtered against user permissions *before* prompt context construction. Unauthorized content or metadata never enters LLM context.
- **Synthetic Demo User Directory**: Pre-configured user profiles (`Alice`, `Bob`, `Charlie`, `Admin`) representing distinct enterprise roles and account boundaries.
- **Zero Information Leakage**: Queries targeting unauthorized documents return standard no-answer fallback responses without exposing document existence or title metadata.
- **Document Permission Metadata**: Every chunk in ChromaDB preserves granular metadata fields (`access_level`, `account`, `department`, `allowed_roles`, `allowed_users`).
- **Interactive UI User Switcher**: Streamlit frontend feature allowing instant toggling between demo users to observe live permission enforcement.

---

## 👥 Demo User Reference Table

| User ID | Name | Role | Department | Accessible Accounts | Permitted Documents & Resources |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `user_001` | **Alice** | `account_manager` | sales | ABC Corp, XYZ Corp | Project Alpha, Support Tickets (ABC Corp), Slack #project-alpha |
| `user_002` | **Bob** | `engineer` | engineering | XYZ Corp | Project Beta, Slack #project-beta |
| `user_003` | **Charlie** | `support_agent` | support | ABC Corp | Support Tickets (ABC Corp), Slack #project-alpha |
| `admin_001` | **Admin** | `admin` | executive | `*` (Global) | **All** documents (including Restricted Project Gamma) |

---

## 🏗️ Architecture

```mermaid
flowchart TD
    A[User] -->|Select User & Query| B[Streamlit Frontend]
    B -->|POST /chat {user_id, question}| C[FastAPI Backend]
    C -->|Authenticate user_id| D[UserService]
    D -->|User Object| C
    C -->|Retrieve Candidates| E[StandardRetriever]
    E -->|Similarity Search| F[(ChromaDB Vector Store)]
    F -->|Raw Vector Candidates| E
    E -->|Pre-LLM Authorization Check| G[PermissionService]
    G -->|Fail-Closed Access Rules| E
    E -->|Authorized Context Chunks| H[RAGService]
    H -->|Prompt Context strictly filtered| I[Google Gemini LLM]
    I -->|Grounded Answer| H
    H -->|Answer + Authorized Citations| C
    C -->|HTTP Response| B
    B -->|Render Answer & Citations| A

    J[Enterprise Data] --> K[Ingestion Pipeline]
    K --> L[Metadata Preservation]
    L --> M[Gemini Embeddings]
    M --> F
```

---

## 🛡️ Access Control & Security Model

The system enforces a **Fail-Closed** security principle at the vector retrieval layer:

1. **Authentication**: Requests must include a valid `user_id` mapped in `UserService`. Unknown `user_id` requests return `HTTP 401 Unauthorized`.
2. **Admin Bypass**: Users with `role="admin"` bypass restriction checks and receive full access to all indexed documents.
3. **Explicit User Grant**: If `user_id` is present in `allowed_users`, access is immediately granted.
4. **Account Boundary Enforcement**: If document `account` is specified and not `"*"`, the user's `accessible_accounts` must explicitly include that account.
5. **Access Level Enforcement**:
   - `public`: Accessible to all authenticated users.
   - `internal`: Accessible if `allowed_roles` is empty OR contains the user's role.
   - `restricted`: Access is **DENIED** unless the user's role is explicitly listed in `allowed_roles` or user ID is in `allowed_users`.
6. **Missing/Malformed Metadata**: Defaults to `restricted` access level and **DENIED** access (Fail-Closed).

---

## 🛠️ Technology Stack

### Backend & AI
- **Python 3.13+**
- **FastAPI**: Asynchronous REST API framework
- **Uvicorn**: ASGI server
- **LangChain & LangChain Google GenAI**: RAG abstractions & Gemini model integrations (`gemini-2.5-flash` & `models/text-embedding-004`)
- **ChromaDB**: Persistent vector database
- **Pydantic / Pydantic Settings**: Data validation & settings management

### Frontend
- **Streamlit**: Dashboard with Demo User Switcher badge and chat UI
- **HTTPX / Requests**: REST API client communication

---

## 📂 Project Structure

```text
permission-aware-rag/
│
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application entry point
│   │   ├── api/
│   │   │   └── chat.py                 # Chat API endpoint with auth validation
│   │   ├── auth/
│   │   │   ├── models.py               # User Pydantic model
│   │   │   ├── authentication.py       # UserService & synthetic demo user directory
│   │   │   └── authorization.py        # Centralized PermissionService (Fail-Closed)
│   │   ├── core/
│   │   │   └── config.py               # Configuration & environment settings
│   │   ├── schemas/
│   │   │   └── chat.py                 # ChatRequest (user_id requirement) & ChatResponse
│   │   ├── services/
│   │   │   ├── retrieval_service.py    # Permission-aware chunk retrieval
│   │   │   └── rag_service.py          # RAG service with pre-LLM authorization
│   │   └── rag/
│   │       ├── loaders.py              # Permission metadata preserving loaders
│   │       ├── chunker.py              # Metadata preserving chunker
│   │       ├── vector_store.py         # ChromaDB persistence manager
│   │       ├── retriever.py            # Pre-LLM filtered retriever
│   │       └── prompts.py              # Strict RAG system & user prompts
│   │
│   ├── data/                           # Synthetic Enterprise Data with Permissions
│   │   ├── project_docs/               # Alpha, Beta, Gamma (Restricted Finance)
│   │   ├── support_tickets/            # Support tickets with account metadata
│   │   └── slack/                      # Slack chat logs with channel access roles
│   │
│   ├── scripts/
│   │   └── ingest.py                   # Data ingestion CLI script
│   │
│   ├── tests/                          # Automated Test Suite (18 tests)
│   │   ├── conftest.py
│   │   ├── test_health.py
│   │   ├── test_chat_validation.py
│   │   ├── test_retrieval.py
│   │   ├── test_no_answer.py
│   │   └── test_phase2_authorization.py# Phase 2 Security & Permission Tests
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app.py                          # Streamlit UI dashboard with User Selector
│   ├── services/
│   │   └── api_client.py              # FastAPI HTTP client passing user_id
│   └── requirements.txt
│
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Environment Setup

Configure your Google Gemini API Key in `backend/.env`:

```env
GEMINI_API_KEY=AIzaSy...your-gemini-api-key...
GEMINI_CHAT_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=models/text-embedding-004
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHUNK_SIZE=800
CHUNK_OVERLAP=100
TOP_K=5
```

---

### 2. Install Dependencies

In your activated virtual environment:

```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

---

### 3. Ingest Enterprise Data

Run the data ingestion script to populate ChromaDB with permission metadata:

```bash
python backend/scripts/ingest.py
```

---

### 4. Run Backend & Frontend Applications

**Backend (FastAPI)**:
```bash
uvicorn backend.app.main:app --reload --port 8000
```

**Frontend (Streamlit)**:
```bash
streamlit run frontend/app.py
```

Open `http://localhost:8501` to use the interactive application.

---

## 🧪 Running Automated Tests

Run all 18 automated unit and security tests:

```bash
python -m pytest backend/tests/ -v
```

---

## 🗺️ Roadmap to Future Phases

- **Phase 3: Database Authentication & JWT**: Real user management via PostgreSQL & JWT tokens.
- **Phase 4: Hybrid Search & Reranking**: Dense vector embeddings combined with BM25 keyword search and Cross-Encoder reranking.
- **Phase 5: Security Audit Logging & Compliance**: Structured access logs, prompt injection safeguards, and sanitization.
