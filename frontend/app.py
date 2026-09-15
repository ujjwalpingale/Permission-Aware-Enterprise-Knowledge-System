import sys
import importlib
import textwrap
from pathlib import Path
import streamlit as st

# Add frontend directory to path
FRONTEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(FRONTEND_DIR))

import services.api_client
importlib.reload(services.api_client)
from services.api_client import APIClient

def render_html(html_str: str):
    """Renders HTML in Streamlit cleanly without any markdown code block formatting artifacts."""
    clean_lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    st.markdown("\n".join(clean_lines), unsafe_allow_html=True)

st.set_page_config(
    page_title="Enterprise Knowledge Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS matching Figma Prototype Theme
st.markdown(
    """
    <style>
    /* Global Background & Typography */
    .stApp {
        background-color: #0b0c10 !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Force visibility of text across all Streamlit components */
    .stApp p, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #e2e8f0;
    }
    div[data-testid="stMarkdownContainer"] p {
        color: #e2e8f0 !important;
    }
    label[data-testid="stWidgetLabel"] p {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }

    /* Custom Streamlit Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0d0e14 !important;
        border-right: 1px solid #1e2230 !important;
        padding-top: 1rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
        display: none !important;
    }
    #MainMenu, footer {
        visibility: hidden;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 99999 !important;
    }
    button[data-testid="stHeaderIconButton"], 
    button[data-testid="stSidebarCollapseButton"], 
    button[data-testid="stSidebarExpandButton"] {
        color: #94a3b8 !important;
        background-color: #12141c !important;
        border: 1px solid #1e2230 !important;
        border-radius: 6px !important;
    }
    .main .block-container {
        padding: 1.5rem 2rem !important;
        max-width: 1200px !important;
    }

    /* Streamlit Bordered Container Styling */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #12141c !important;
        border: 1px solid #1e2230 !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4) !important;
    }

    /* Common Card Styles */
    .dark-card {
        background-color: #12141c;
        border: 1px solid #1e2230;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    .dark-card-hover {
        background-color: #12141c;
        border: 1px solid #1e2230;
        border-radius: 10px;
        padding: 16px;
        transition: all 0.2s ease;
    }
    .dark-card-hover:hover {
        border-color: #3b82f6;
        background-color: #161925;
    }

    /* Badges */
    .badge-accessible {
        background-color: #052e16;
        color: #34d399;
        border: 1px solid #059669;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .badge-doc {
        background-color: #1e1b4b;
        color: #818cf8;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-ticket {
        background-color: #311042;
        color: #c084fc;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-slack {
        background-color: #064e3b;
        color: #34d399;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-dept {
        background-color: #1e1b4b;
        color: #818cf8;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }

    /* User Avatars */
    .avatar-aj { background-color: #2563eb; color: white; border-radius: 50%; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; }
    .avatar-bw { background-color: #059669; color: white; border-radius: 50%; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; }
    .avatar-cs { background-color: #ea580c; color: white; border-radius: 50%; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; }
    .avatar-admin { background-color: #7c3aed; color: white; border-radius: 50%; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; }

    /* Pipeline Flow Box */
    .pipeline-box {
        background-color: #12141c;
        border: 1px solid #1e2230;
        border-radius: 12px;
        padding: 12px 24px;
        display: inline-flex;
        align-items: center;
        gap: 16px;
        color: #94a3b8;
        font-size: 13px;
    }
    .pipeline-step {
        display: flex;
        align-items: center;
        gap: 6px;
        color: #e2e8f0;
        font-weight: 500;
    }

    /* Custom Streamlit Button Styling */
    div.stButton > button {
        background-color: #161925 !important;
        color: #e2e8f0 !important;
        border: 1px solid #232738 !important;
        border-radius: 8px !important;
        padding: 10px 16px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:hover {
        border-color: #3b82f6 !important;
        background-color: #1e2336 !important;
        color: #ffffff !important;
    }
    div.stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
    }

    /* Input styling */
    div.stTextInput > div > div > input {
        background-color: #0d0e14 !important;
        color: white !important;
        border: 1px solid #1f2333 !important;
        border-radius: 8px !important;
    }
    div.stSelectbox > div > div {
        background-color: #0d0e14 !important;
        color: white !important;
        border: 1px solid #1f2333 !important;
        border-radius: 8px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize API Client
client = APIClient()

# Initialize Session States
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user_id" not in st.session_state:
    st.session_state.current_user_id = "user_001"
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Ask Assistant"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Demo User Profiles Reference
DEMO_USER_PROFILES = {
    "user_001": {
        "id": "user_001",
        "name": "Alice Johnson",
        "role": "Account Manager",
        "department": "Sales",
        "accounts": "ABC Corp, XYZ Corp",
        "email": "alice.johnson@corp.internal",
        "avatar": "AJ",
        "avatar_cls": "avatar-aj",
    },
    "user_002": {
        "id": "user_002",
        "name": "Bob Williams",
        "role": "Engineer",
        "department": "Engineering",
        "accounts": "XYZ Corp",
        "email": "bob.williams@corp.internal",
        "avatar": "BW",
        "avatar_cls": "avatar-bw",
    },
    "user_003": {
        "id": "user_003",
        "name": "Charlie Smith",
        "role": "Support Agent",
        "department": "Support",
        "accounts": "ABC Corp",
        "email": "charlie.smith@corp.internal",
        "avatar": "CS",
        "avatar_cls": "avatar-cs",
    },
    "admin_001": {
        "id": "admin_001",
        "name": "Admin",
        "role": "Administrator",
        "department": "Administration",
        "accounts": "All Accounts (*)",
        "email": "admin@corp.internal",
        "avatar": "A",
        "avatar_cls": "avatar-admin",
    },
}

current_user = DEMO_USER_PROFILES.get(st.session_state.current_user_id, DEMO_USER_PROFILES["user_001"])

# ============================================================================
# ALWAYS RENDER SIDEBAR
# ============================================================================
with st.sidebar:
    render_html(
        """
        <div style="padding:16px 12px; border-bottom:1px solid #1e2230; display:flex; align-items:center; gap:10px; margin-bottom:16px;">
            <div style="width:32px; height:32px; background:linear-gradient(135deg, #4f46e5, #7c3aed); border-radius:8px; display:flex; align-items:center; justify-content:center;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            </div>
            <div>
                <div style="color:white; font-weight:700; font-size:15px; margin:0;">Enterprise</div>
                <div style="color:#64748b; font-size:11px; margin:0;">Knowledge</div>
            </div>
        </div>
        """
    )

    if st.session_state.authenticated:
        st.markdown('<div style="font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; margin:12px 12px 8px 12px;">NAVIGATION</div>', unsafe_allow_html=True)
        
        nav_options = [
            ("Ask Assistant", "💬"),
            ("Search Knowledge", "🔍"),
            ("Documents", "📄"),
            ("My Access", "👤"),
        ]

        for nav_name, nav_icon in nav_options:
            is_act = (st.session_state.current_tab == nav_name)
            btn_type = "primary" if is_act else "secondary"
            if st.button(f"{nav_icon}  {nav_name}", key=f"nav_{nav_name}", type=btn_type, use_container_width=True):
                st.session_state.current_tab = nav_name
                st.rerun()

        st.markdown('<br><div style="font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; margin:12px 12px 8px 12px;">KNOWLEDGE SOURCES</div>', unsafe_allow_html=True)
        render_html(
            """
            <div style="font-size:13px; color:#94a3b8; padding:6px 12px; display:flex; align-items:center; gap:8px;">
                <span style="color:#3b82f6;">●</span> Project Documentation
            </div>
            <div style="font-size:13px; color:#94a3b8; padding:6px 12px; display:flex; align-items:center; gap:8px;">
                <span style="color:#a855f7;">●</span> Support Tickets
            </div>
            <div style="font-size:13px; color:#94a3b8; padding:6px 12px; display:flex; align-items:center; gap:8px;">
                <span style="color:#22c55e;">●</span> Slack Conversations
            </div>
            """
        )

        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # User Footer Card in Sidebar
        render_html(
            f"""
            <div style="background-color:#12141c; border:1px solid #1e2230; border-radius:10px; padding:12px; margin-top:auto;">
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                    <div class="{current_user['avatar_cls']}" style="width:32px; height:32px; font-size:12px;">{current_user['avatar']}</div>
                    <div>
                        <div style="color:white; font-weight:600; font-size:13px;">{current_user['name']}</div>
                        <div style="color:#64748b; font-size:11px;">{current_user['role']}</div>
                    </div>
                </div>
            </div>
            """
        )
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    else:
        st.markdown('<div style="font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; margin:12px 12px 8px 12px;">SELECT DEMO USER</div>', unsafe_allow_html=True)
        for u_id, u_data in DEMO_USER_PROFILES.items():
            if st.button(f"👤 {u_data['name']} ({u_data['role']})", key=f"sb_login_{u_id}", use_container_width=True):
                st.session_state.current_user_id = u_id
                st.session_state.authenticated = True
                st.rerun()

# ============================================================================
# SCREEN 1: LOGIN & DEMO USER SELECTION (UNAUTHENTICATED)
# ============================================================================
if not st.session_state.authenticated:
    st.markdown("<br>", unsafe_allow_html=True)
    l_col1, l_col2, l_col3 = st.columns([0.5, 2, 0.5])

    with l_col2:
        render_html(
            """
            <div style="text-align:center; margin-bottom:24px;">
                <div style="display:inline-flex; align-items:center; justify-content:center; width:52px; height:52px; background:linear-gradient(135deg, #4f46e5, #7c3aed); border-radius:14px; margin-bottom:16px;">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                </div>
                <h2 style="color:white; font-size:24px; font-weight:700; margin:0 0 6px 0;">Welcome to Enterprise Knowledge Assistant</h2>
                <p style="color:#94a3b8; font-size:14px; margin:0;">Search and understand your organization's knowledge securely.</p>
            </div>
            """
        )

        # Login Form Card
        with st.container(border=True):
            email_in = st.text_input("Email address", value="alice.johnson@corp.internal")
            pass_in = st.text_input("Password", type="password", value="••••••••")
            if st.button("Sign In", type="primary", use_container_width=True):
                st.session_state.authenticated = True
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Demo Users Selector Card
        with st.container(border=True):
            st.markdown(
                '<div style="font-size:11px; font-weight:700; color:#64748b; letter-spacing:1px; margin-bottom:16px;">DEMO USERS</div>',
                unsafe_allow_html=True,
            )

            for u_id, u_data in DEMO_USER_PROFILES.items():
                btn_col1, btn_col2 = st.columns([4, 1])
                with btn_col1:
                    st.markdown(
                        f"""
                        <div style="display:flex; align-items:center; gap:12px; padding:4px 0;">
                            <div class="{u_data['avatar_cls']}" style="width:36px; height:36px; font-size:13px;">{u_data['avatar']}</div>
                            <div>
                                <div style="color:white; font-weight:600; font-size:14px;">{u_data['name']}</div>
                                <div style="color:#64748b; font-size:12px;">{u_data['role']} · {u_data['department']}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with btn_col2:
                    if st.button("Select", key=f"login_{u_id}", use_container_width=True):
                        st.session_state.current_user_id = u_id
                        st.session_state.authenticated = True
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center; color:#64748b; font-size:12px;">🔒 Your access is controlled by your organization\'s permissions.</div>',
            unsafe_allow_html=True,
        )

# ============================================================================
# SCREEN 2: AUTHENTICATED MAIN APPLICATION
# ============================================================================
else:
    # ------------------------------------------------------------------------
    # MAIN CANVAS AREA
    # ------------------------------------------------------------------------

    # ====================================================================
    # TAB 1: ASK ASSISTANT
    # ====================================================================
    if st.session_state.current_tab == "Ask Assistant":
        head_c1, head_c2 = st.columns([3, 1])
        with head_c1:
            st.markdown(
                """
                <h2 style="color:white; font-size:22px; font-weight:700; margin:0 0 4px 0;">Ask Assistant</h2>
                <p style="color:#94a3b8; font-size:13px; margin:0;">Answers generated from knowledge you're authorized to access</p>
                """,
                unsafe_allow_html=True,
            )
        with head_c2:
            st.markdown('<div style="text-align:right;"><span class="badge-accessible">● Permission-aware</span></div>', unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#1e2230; margin:16px 0 24px 0;'>", unsafe_allow_html=True)

        # Center Hero Content
        render_html(
            f"""
            <div style="text-align:center; padding:24px 0 16px 0;">
                <div style="display:inline-flex; align-items:center; justify-content:center; width:48px; height:48px; background:linear-gradient(135deg, #4f46e5, #7c3aed); border-radius:12px; margin-bottom:12px;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                </div>
                <h1 style="color:white; font-size:28px; font-weight:700; margin:0 0 6px 0;">Good afternoon, {current_user['name'].split()[0]}</h1>
                <p style="color:#94a3b8; font-size:14px; margin:0 0 20px 0;">What would you like to know?</p>
                <div class="pipeline-box">
                    <span class="pipeline-step">👤 You</span> ➔
                    <span class="pipeline-step">🔒 Auth</span> ➔
                    <span class="pipeline-step">🛡️ Permissions</span> ➔
                    <span class="pipeline-step">🔍 Retrieval</span> ➔
                    <span class="pipeline-step">✨ AI</span> ➔
                    <span class="pipeline-step">📝 Answer</span>
                </div>
            </div>
            """
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:11px; font-weight:700; color:#64748b; letter-spacing:1px; text-align:center; margin-bottom:12px;">SUGGESTED QUESTIONS</div>', unsafe_allow_html=True)

        # Suggested Questions 2x2 Grid
        sq1, sq2 = st.columns(2)
        preset_q = None
        with sq1:
            if st.button("What technologies are used in Project Alpha?", use_container_width=True):
                preset_q = "What technologies are used in Project Alpha?"
            if st.button("What issues were reported for ABC Corp?", use_container_width=True):
                preset_q = "What issues were reported for ABC Corp?"
        with sq2:
            if st.button("What is the current status of Project Beta?", use_container_width=True):
                preset_q = "What is the current status of Project Beta?"
            if st.button("What information is available about Project Gamma?", use_container_width=True):
                preset_q = "What information is available about Project Gamma?"

        st.markdown("<br>", unsafe_allow_html=True)

        # Render Chat Messages
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
                        st.markdown(f"`{icon} {citation.get('title', 'Source')}`")

        # Chat Input Box
        user_query = st.chat_input("Ask anything about projects, tickets, or internal conversations...") or preset_q

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.write(user_query)

            with st.chat_message("assistant"):
                with st.spinner(f"Searching authorized knowledge base as {current_user['name']}..."):
                    res = client.send_question(user_query, user_id=current_user['id'])
                    if res.get("success"):
                        data = res["data"]
                        answer = data.get("answer", "")
                        citations = data.get("citations", [])
                        st.write(answer)
                        if citations:
                            st.markdown("### 📚 Authorized Sources")
                            for c in citations:
                                st.markdown(f"📄 **{c.get('title')}** `({c.get('document_id')})`")
                        st.session_state.messages.append({"role": "assistant", "content": answer, "citations": citations})
                    else:
                        st.error(res.get("error", "Error processing request."))

    # ====================================================================
    # TAB 2: SEARCH KNOWLEDGE
    # ====================================================================
    elif st.session_state.current_tab == "Search Knowledge":
        st.markdown('<h2 style="color:white; font-size:22px; font-weight:700; margin:0 0 16px 0;">Search Knowledge</h2>', unsafe_allow_html=True)
        search_query = st.text_input("Search bar", placeholder="🔍 Search projects, tickets, conversations...", label_visibility="collapsed")

        f_col, r_col = st.columns([1, 3])

        with f_col:
            with st.container(border=True):
                st.markdown('<div style="font-size:11px; font-weight:700; color:#64748b; letter-spacing:1px; margin-bottom:8px;">SOURCE TYPE</div>', unsafe_allow_html=True)
                src_type = st.selectbox("Source Type", ["All", "Project Documentation", "Support Ticket", "Slack Conversation"], label_visibility="collapsed")
                
                st.markdown('<br><div style="font-size:11px; font-weight:700; color:#64748b; letter-spacing:1px; margin-bottom:8px;">DEPARTMENT</div>', unsafe_allow_html=True)
                dept_type = st.selectbox("Department", ["All", "Engineering", "Support", "Sales"], label_visibility="collapsed")
                
                st.markdown('<br>', unsafe_allow_html=True)
                avail_check = st.checkbox("Available to me", value=True)

        with r_col:
            st.markdown('<div style="font-size:13px; color:#64748b; margin-bottom:12px;">4 results found</div>', unsafe_allow_html=True)
            
            results_data = [
                {
                    "title": "Project Alpha Documentation",
                    "badge_cls": "badge-doc",
                    "badge_text": "Project Documentation",
                    "meta": "Engineering · ABC Corp",
                    "desc": "Project Alpha is an enterprise e-commerce platform built for ABC Corp. The platform handles high-volume transaction processing and integrates with their existing ERP infrastructure.",
                    "date": "2026-09-10"
                },
                {
                    "title": "Ticket #001 — Payment Processing Failure",
                    "badge_cls": "badge-ticket",
                    "badge_text": "Support Ticket",
                    "meta": "Support · ABC Corp",
                    "desc": "Customer reported payment processing failure during peak checkout window. Issue traced to a race condition in the inventory lock service.",
                    "date": "2026-09-08"
                },
                {
                    "title": "Project Alpha — Slack Conversation",
                    "badge_cls": "badge-slack",
                    "badge_text": "Slack Conversation",
                    "meta": "Engineering · ABC Corp",
                    "desc": "Engineering team discussion about Project Alpha's Phase 2 delivery timeline and the payment module QA blockers.",
                    "date": "2026-09-12"
                },
                {
                    "title": "Project Beta Documentation",
                    "badge_cls": "badge-doc",
                    "badge_text": "Project Documentation",
                    "meta": "Engineering · XYZ Corp",
                    "desc": "Project Beta is a data analytics pipeline for XYZ Corp, processing real-time telemetry from IoT devices across their manufacturing facilities.",
                    "date": "2026-09-05"
                },
            ]

            for item in results_data:
                render_html(
                    f"""
                    <div class="dark-card" style="margin-bottom:12px; padding:16px;">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                            <div>
                                <div style="color:white; font-size:16px; font-weight:700; margin-bottom:4px;">{item['title']}</div>
                                <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                                    <span class="{item['badge_cls']}">{item['badge_text']}</span>
                                    <span style="color:#64748b; font-size:12px;">{item['meta']}</span>
                                </div>
                            </div>
                            <span class="badge-accessible">ACCESSIBLE</span>
                        </div>
                        <p style="color:#94a3b8; font-size:13px; margin:0 0 8px 0; line-height:1.4;">{item['desc']}</p>
                        <div style="color:#475569; font-size:11px;">Updated {item['date']}</div>
                    </div>
                    """
                )

    # ====================================================================
    # TAB 3: DOCUMENTS
    # ====================================================================
    elif st.session_state.current_tab == "Documents":
        render_html(
            """
            <h2 style="color:white; font-size:22px; font-weight:700; margin:0 0 4px 0;">Documents</h2>
            <p style="color:#94a3b8; font-size:13px; margin:0 0 16px 0;">Knowledge base documents you have access to</p>
            """
        )

        d_cols = st.columns(4)
        doc_cards = [
            {"type": "DOCUMENTATION", "badge_cls": "badge-doc", "title": "Project Alpha Documentation", "desc": "Project Alpha is an enterprise e-commerce platform built for ABC Corp...", "meta": "ABC Corp · Engineering"},
            {"type": "TICKET", "badge_cls": "badge-ticket", "title": "Ticket #001 — Payment Processing Failure", "desc": "Customer reported payment processing failure during peak checkout window...", "meta": "ABC Corp · Support"},
            {"type": "SLACK", "badge_cls": "badge-slack", "title": "Project Alpha — Slack Conversation", "desc": "Engineering team discussion about Project Alpha's Phase 2 delivery timeline...", "meta": "ABC Corp · Engineering"},
            {"type": "DOCUMENTATION", "badge_cls": "badge-doc", "title": "Project Beta Documentation", "desc": "Project Beta is a data analytics pipeline for XYZ Corp, processing real-time...", "meta": "XYZ Corp · Engineering"},
        ]

        for idx, d in enumerate(doc_cards):
            with d_cols[idx]:
                render_html(
                    f"""
                    <div class="dark-card" style="height:220px; display:flex; flex-direction:column; justify-content:space-between; padding:16px;">
                        <div>
                            <span class="{d['badge_cls']}">{d['type']}</span>
                            <div style="color:white; font-size:14px; font-weight:700; margin:8px 0 6px 0; line-height:1.3;">{d['title']}</div>
                            <p style="color:#94a3b8; font-size:12px; line-height:1.4; margin:0;">{d['desc']}</p>
                        </div>
                        <div>
                            <hr style="border-color:#1e2230; margin:8px 0;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="color:#64748b; font-size:11px;">{d['meta']}</span>
                                <span style="color:#34d399; font-size:11px; font-weight:600;">✓ Accessible</span>
                            </div>
                        </div>
                    </div>
                    """
                )

    # ====================================================================
    # TAB 4: MY ACCESS
    # ====================================================================
    elif st.session_state.current_tab == "My Access":
        render_html(
            """
            <h2 style="color:white; font-size:22px; font-weight:700; margin:0 0 4px 0;">My Access</h2>
            <p style="color:#94a3b8; font-size:13px; margin:0 0 16px 0;">Your current permissions and knowledge access</p>
            """
        )

        a_col1, a_col2 = st.columns(2)

        with a_col1:
            render_html(
                f"""
                <div class="dark-card" style="margin-bottom:16px;">
                    <div style="font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; margin-bottom:12px;">PROFILE</div>
                    <div style="display:flex; align-items:center; gap:16px; margin-bottom:16px;">
                        <div class="{current_user['avatar_cls']}" style="width:48px; height:48px; font-size:18px;">{current_user['avatar']}</div>
                        <div>
                            <div style="color:white; font-size:18px; font-weight:700;">{current_user['name']}</div>
                            <div style="color:#94a3b8; font-size:13px; margin-bottom:4px;">{current_user['role']}</div>
                            <span class="badge-dept">{current_user['department']}</span>
                        </div>
                    </div>
                    <div style="font-size:11px; color:#64748b; margin-bottom:4px;">Email</div>
                    <div style="background-color:#0d0e14; border:1px solid #1f2333; border-radius:6px; padding:8px 12px; color:white; font-size:13px;">{current_user['email']}</div>
                </div>
                """
            )

        with a_col2:
            accounts_html = ""
            for acc in current_user['accounts'].split(","):
                acc_clean = acc.strip()
                first_letter = acc_clean[0] if acc_clean else "A"
                accounts_html += f"""
                <div style="background-color:#0d0e14; border:1px solid #1f2333; border-radius:6px; padding:8px 12px; display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="background-color:#1e2230; color:#818cf8; width:22px; height:22px; border-radius:4px; display:inline-flex; align-items:center; justify-content:center; font-size:11px; font-weight:700;">{first_letter}</span>
                        <span style="color:white; font-size:13px; font-weight:600;">{acc_clean}</span>
                    </div>
                    <span style="color:#34d399;">✓</span>
                </div>
                """

            render_html(
                f"""
                <div class="dark-card" style="margin-bottom:16px;">
                    <div style="font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; margin-bottom:12px;">ACCESSIBLE ACCOUNTS</div>
                    {accounts_html}
                    <div style="font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; margin:16px 0 8px 0;">DEPARTMENT</div>
                    <span class="badge-dept" style="padding:6px 12px; font-size:12px;">🏢 {current_user['department']}</span>
                </div>
                """
            )

        render_html(
            """
            <div class="dark-card" style="margin-bottom:16px;">
                <div style="font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; margin-bottom:12px;">KNOWLEDGE ACCESS</div>
                <div style="background-color:#0d0e14; border:1px solid #1f2333; border-radius:6px; padding:10px 14px; display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="color:white; font-size:13px;">● Project Documentation</span>
                    <span style="color:#34d399;">✓</span>
                </div>
                <div style="background-color:#0d0e14; border:1px solid #1f2333; border-radius:6px; padding:10px 14px; display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="color:white; font-size:13px;">● Support Tickets</span>
                    <span style="color:#34d399;">✓</span>
                </div>
                <div style="background-color:#0d0e14; border:1px solid #1f2333; border-radius:6px; padding:10px 14px; display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:white; font-size:13px;">● Slack Conversations</span>
                    <span style="color:#34d399;">✓</span>
                </div>
            </div>
            """
        )

        render_html(
            """
            <div class="dark-card">
                <div style="font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; margin-bottom:12px;">ACCESS RULES</div>
                <div style="display:flex; gap:12px;">
                    <div style="background-color:#0d0e14; border:1px solid #1f2333; border-radius:6px; padding:10px 16px; color:#cbd5e1; font-size:13px;">🔒 Role-based access</div>
                    <div style="background-color:#0d0e14; border:1px solid #1f2333; border-radius:6px; padding:10px 16px; color:#cbd5e1; font-size:13px;">👤 Account-based access</div>
                    <div style="background-color:#0d0e14; border:1px solid #1f2333; border-radius:6px; padding:10px 16px; color:#cbd5e1; font-size:13px;">🏢 Department-based access</div>
                </div>
            </div>
            """
        )
