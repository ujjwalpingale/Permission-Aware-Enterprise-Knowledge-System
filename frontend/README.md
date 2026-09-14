# Frontend — Streamlit Knowledge Assistant Interface

Streamlit dashboard providing an interactive, real-time chat interface for querying the enterprise knowledge base via the FastAPI backend API.

## Features
- **Strict Separation**: Communicates only with FastAPI backend endpoints (`/chat` and `/health`). Contains zero direct LLM / RAG logic.
- **Chat History**: Preserves multi-turn chat history within session state.
- **Source Badges**: Visually renders source citations with distinct icons:
  - 📄 Project Documents
  - 💬 Slack Conversations
  - 🎫 Support Tickets
- **Backend Status Indicator**: Live status monitoring in the sidebar for connection health to `http://localhost:8000`.

## Execution

```bash
pip install -r requirements.txt
streamlit run app.py
```
