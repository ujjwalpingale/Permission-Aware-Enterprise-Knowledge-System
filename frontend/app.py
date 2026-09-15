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
    page_title="Permission-Aware Enterprise Assistant",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for modern main-page dashboard
st.markdown(
    """
    <style>
    /* Hide sidebar completely */
    [data-testid="stSidebar"], section[data-testid="stSidebar"] {
        display: none !important;
    }
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1150px;
    }
    .stApp {
        background-color: #0e1117;
    }
    .header-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .header-title {
        font-size: 24px;
        font-weight: 700;
        color: #f8fafc;
        margin: 0;
    }
    .header-subtitle {
        font-size: 13px;
        color: #94a3b8;
        margin-top: 4px;
    }
    .user-profile-box {
        background-color: #1e293b;
        border: 1px solid #3b82f6;
        border-radius: 10px;
        padding: 12px 16px;
        margin-top: 10px;
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
    .sample-q-btn button {
        text-align: left !important;
        font-size: 12px !important;
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

# Demo User Data Definitions
DEMO_USER_PROFILES = {
    "user_001": {"name": "Alice", "role": "Account Manager", "department": "Sales", "accounts": "ABC Corp, XYZ Corp"},
    "user_002": {"name": "Bob", "role": "Engineer", "department": "Engineering", "accounts": "XYZ Corp"},
    "user_003": {"name": "Charlie", "role": "Support Agent", "department": "Support", "accounts": "ABC Corp"},
    "admin_001": {"name": "Admin", "role": "Administrator", "department": "Administration", "accounts": "All Accounts (*)"},
}

# Check Backend Health Status
health = client.check_health()
is_online = health.get("online", False)

# Main Header Section
st.markdown(
    """
    <div class="header-card">
        <div class="header-title">🧠 Enterprise RAG Knowledge Assistant</div>
        <div class="header-subtitle">Phase 2 — Permission-Aware Knowledge System with Pre-LLM Context Authorization</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main Control Grid (User Switcher + Document Uploader)
ctrl_col1, ctrl_col2 = st.columns([1, 1], gap="medium")

with ctrl_col1:
    st.markdown("### 👤 Select Active Demo User")
    selected_user_id = st.selectbox(
        "Select User Account:",
        options=list(DEMO_USER_PROFILES.keys()),
        format_func=lambda x: f"{DEMO_USER_PROFILES[x]['name']} — {DEMO_USER_PROFILES[x]['role']} ({DEMO_USER_PROFILES[x]['department']})",
        label_visibility="collapsed",
    )
    profile = DEMO_USER_PROFILES[selected_user_id]
    st.markdown(
        f"""
        <div class="user-profile-box">
            <div style="font-weight:700; color:#38bdf8; font-size:15px; margin-bottom:4px;">👤 {profile['name']}</div>
            <div style="font-size:12px; color:#cbd5e1;"><strong>Role:</strong> {profile['role']} &nbsp;|&nbsp; <strong>Dept:</strong> {profile['department']}</div>
            <div style="font-size:12px; color:#cbd5e1;"><strong>Accessible Accounts:</strong> {profile['accounts']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with ctrl_col2:
    st.markdown("### 📤 Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload docs (.md, .txt, .json)",
        type=["md", "txt", "json"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded_files:
        if st.button("⚡ Ingest Uploaded Documents", use_container_width=True):
            with st.spinner("Indexing documents into ChromaDB..."):
                up_res = client.upload_documents(uploaded_files)
                if up_res.get("success"):
                    st.success("Successfully indexed into ChromaDB!")
                    st.rerun()
                else:
                    st.error(up_res.get("error", "Upload failed."))

st.divider()

# Sample Questions Bar
st.markdown("#### 💡 Quick Sample Questions")
sample_questions = [
    "What delivery date was promised to ABC Corp?",
    "What is the status of Project Beta?",
    "What is the confidential financial status of Project Gamma?",
    "What issue is customer ABC Corp having?",
    "What was the company's revenue in 2024?",
]

q_cols = st.columns(len(sample_questions))
preset_q = None
for idx, q in enumerate(sample_questions):
    with q_cols[idx]:
        if st.button(q, key=f"sq_{idx}", use_container_width=True):
            preset_q = q

st.divider()

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "citations" in message and message["citations"]:
            st.markdown("**Sources Used:**")
            for citation in message["citations"]:
                st_type = citation.get("source_type", "doc")
                icon = "📄"
                if "slack" in st_type.lower():
                    icon = "💬"
                elif "ticket" in st_type.lower():
                    icon = "🎫"
                
                title = citation.get("title", "Source")
                doc_id = citation.get("document_id", "")
                st.markdown(f"`{icon} {title}`")

# Handle preset question click or direct user input
user_query = st.chat_input(f"Ask a question as {profile['name']}...") or preset_q

if user_query:
    # 1. Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.write(user_query)

    # 2. Process query via backend API with active user_id
    with st.chat_message("assistant"):
        with st.spinner(f"Authenticating as {profile['name']} & searching authorized knowledge base..."):
            res = client.send_question(user_query, user_id=selected_user_id)

            if res.get("success"):
                data = res["data"]
                answer = data.get("answer", "")
                citations = data.get("citations", [])

                st.write(answer)

                if citations:
                    st.markdown("### 📚 Authorized Sources")
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

