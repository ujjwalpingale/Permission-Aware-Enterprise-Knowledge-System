# Backend — Enterprise RAG API Service

FastAPI backend service providing document ingestion pipelines, vector storage via ChromaDB, similarity retrieval, and OpenAI LLM generation.

## Features
- **Data Loaders**: Supports Markdown (`.md`), Plain Text (`.txt`), and JSON formats (Support Tickets & Slack logs).
- **Metadata Preservation**: Retains `source_type`, `source_file`, `document_id`, `title`, and `chunk_index` across document splits.
- **Idempotent Ingestion**: Generates deterministic chunk hashes to prevent duplicate database records.
- **Strict Anti-Hallucination Prompting**: Instructs LLM to rely solely on context and return standard no-answer fallback when information is absent.

## Directory Layout
- `app/main.py`: FastAPI application entrypoint.
- `app/api/chat.py`: `/chat` endpoint implementation.
- `app/core/config.py`: Environment configuration via Pydantic Settings.
- `app/rag/`: Core RAG components (loaders, chunker, embeddings, vector_store, retriever, prompts).
- `app/services/`: Service orchestrators (`ingestion_service`, `retrieval_service`, `rag_service`).
- `data/`: Sample synthetic enterprise data.
- `scripts/ingest.py`: CLI ingestion script.

## Execution

```bash
# Ingest Data
python scripts/ingest.py

# Run API Server
uvicorn app.main:app --reload --port 8000
```
