import sys
import importlib
from pathlib import Path
import streamlit as st

# Add frontend directory to path
FRONTEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(FRONTEND_DIR))

import services.api_client
importlib.reload(services.api_client)
from services.api_client import APIClient

st.set_page_config(
    page_title="Enterprise Knowledge Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished modern design
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 950px;
    }
    .stApp {
        background-color: #0e1117;
    }
    .header-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .header-title {
        font-size: 26px;
        font-weight: 700;
        color: #f8fafc;
        margin: 0;
    }
    .header-subtitle {
        font-size: 14px;
        color: #94a3b8;
        margin-top: 6px;
    }
    .citation-badge {
        display: inline-flex;
        align-items: center;
        background-color: #1e293b;
        border: 1px solid #475569;
        border-radius: 6px;
        padding: 6px 12px;
        margin-right: 8px;
        margin-top: 6px;
        font-size: 13px;
        color: #e2e8f0;
    }
    .source-icon {
        margin-right: 6px;
        font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize API Client
client = APIClient()

# Initialize Chat History in Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Navigation & Backend Status
with st.sidebar:
    st.image("https://img.icons8.com/isometric/96/brain.png", width=64)
    st.title("Enterprise RAG")
    st.caption("Phase 1 — Basic Knowledge Assistant")
    st.divider()

    # Health Check Status
    health = client.check_health()
    if health.get("online"):
        st.success("Backend Online (FastAPI)")
    else:
        st.error("Backend Offline (http://localhost:8000)")
        st.info("Start backend server:\n`uvicorn backend.app.main:app --reload`")

    st.divider()
    st.subheader("📤 Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload internal docs (.md, .txt, .json)",
        type=["md", "txt", "json"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        if st.button("⚡ Ingest Uploaded Documents", use_container_width=True):
            with st.spinner("Uploading and indexing documents into ChromaDB..."):
                up_res = client.upload_documents(uploaded_files)
                if up_res.get("success"):
                    st.success("Successfully uploaded & indexed into ChromaDB!")
                    st.rerun()
                else:
                    st.error(up_res.get("error", "Upload failed."))

    st.divider()
    st.subheader("💡 Sample Questions")
    sample_questions = [
        "What delivery date was promised to ABC Corp?",
        "What issue is customer ABC Corp having?",
        "What is the status of Project Beta?",
        "What delivery date was promised for Project Gamma?",
        "What was the company's revenue in 2024?",
    ]

    for q in sample_questions:
        if st.button(q, use_container_width=True):
            st.session_state.preset_query = q

    st.divider()
    st.caption("🔒 Phase 1 Notice: Security & Permissions will be enabled in Phase 2.")


# Main App Layout
st.markdown(
    """
    <div class="header-card">
        <div class="header-title">🏢 Enterprise Knowledge Assistant</div>
        <div class="header-subtitle">Ask questions about internal projects, support tickets, and team Slack discussions.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "citations" in message and message["citations"]:
            st.markdown("**Sources Used:**")
            cols = st.columns(len(message["citations"]))
            for idx, citation in enumerate(message["citations"]):
                st_type = citation.get("source_type", "doc")
                icon = "📄"
                if "slack" in st_type.lower():
                    icon = "💬"
                elif "ticket" in st_type.lower():
                    icon = "🎫"
                
                title = citation.get("title", "Source")
                doc_id = citation.get("document_id", "")
                st.markdown(f"`{icon} {title}`")

# Check for preset query selection from sidebar
preset_q = st.session_state.pop("preset_query", None)

# Chat Input Box
user_query = st.chat_input("Ask a question about internal documents...") or preset_q

if user_query:
    # 1. Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.write(user_query)

    # 2. Process query via backend API
    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base & generating response..."):
            res = client.send_question(user_query)

            if res.get("success"):
                data = res["data"]
                answer = data.get("answer", "")
                citations = data.get("citations", [])

                st.write(answer)

                if citations:
                    st.markdown("### 📚 Sources")
                    for citation in citations:
                        st_type = citation.get("source_type", "doc")
                        icon = "📄"
                        if "slack" in st_type.lower():
                            icon = "💬"
                        elif "ticket" in st_type.lower():
                            icon = "🎫"
                        
                        title = citation.get("title", "Untitled")
                        doc_id = citation.get("document_id", "")
                        st.markdown(
                            f"""
                            <div class="citation-badge">
                                <span class="source-icon">{icon}</span>
                                <strong>{title}</strong> &nbsp;<span style="color:#64748b;">({doc_id})</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                # Store assistant response in history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "citations": citations,
                })
            else:
                error_msg = res.get("error", "An unknown error occurred.")
                st.error(error_msg)
