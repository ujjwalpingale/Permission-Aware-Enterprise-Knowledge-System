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
    .badge-dept {
        background-color: #1e1b4b;
        color: #818cf8;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-admin {
        background-color: #4c1d95;
        color: #c084fc;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
    }

    /* User Avatars */
    .avatar-user {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border-radius: 50%;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }

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

# Initialize Session States safely
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Ask Assistant"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "reg_invite_info" not in st.session_state:
    st.session_state.reg_invite_info = None


def handle_logout():
    """Clears authentication session state and resets dashboard."""
    st.session_state.authenticated = False
    st.session_state.access_token = None
    st.session_state.user = None
    st.session_state.messages = []
    st.session_state.reg_invite_info = None
    st.rerun()


def handle_unauthorized_error(res: dict):
    """Handles HTTP 401 Unauthorized errors by resetting session."""
    if res.get("unauthorized"):
        st.error("Session expired or token invalid. Please sign in again.")
        handle_logout()


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
                <div style="color:#64748b; font-size:11px; margin:0;">Knowledge System</div>
            </div>
        </div>
        """
    )

    # Live Health Check
    health = client.check_health()
    if health.get("online"):
        st.markdown('<div style="font-size:11px; color:#34d399; padding:0 12px 12px 12px;">● Backend Online (FastAPI)</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size:11px; color:#f87171; padding:0 12px 12px 12px;">● Backend Offline ({health.get("error", "Error")})</div>', unsafe_allow_html=True)

    if st.session_state.authenticated and st.session_state.user:
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

        st.markdown("<br><br>", unsafe_allow_html=True)
        
        user_info = st.session_state.user
        role_label = user_info.get("role", "").upper()
        initials = (user_info.get("full_name", "U")[0]).upper()

        # User Footer Card in Sidebar
        render_html(
            f"""
            <div style="background-color:#12141c; border:1px solid #1e2230; border-radius:10px; padding:12px; margin-top:auto;">
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
                    <div class="avatar-user" style="width:32px; height:32px; font-size:13px;">{initials}</div>
                    <div>
                        <div style="color:white; font-weight:600; font-size:13px;">{user_info.get('full_name')}</div>
                        <div style="color:#94a3b8; font-size:11px;">{role_label}</div>
                    </div>
                </div>
            </div>
            """
        )
        if st.button("🚪 Logout", use_container_width=True):
            handle_logout()
    else:
        st.markdown('<div style="font-size:11px; color:#64748b; padding:12px;">Please authenticate to access authorized knowledge.</div>', unsafe_allow_html=True)


# ============================================================================
# SCREEN 1: AUTHENTICATION UI (UNAUTHENTICATED)
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
                <h2 style="color:white; font-size:24px; font-weight:700; margin:0 0 6px 0;">Enterprise Knowledge System</h2>
                <p style="color:#94a3b8; font-size:14px; margin:0;">Permission-aware RAG pipeline with pre-retrieval authorization.</p>
            </div>
            """
        )

        auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔑 Sign In", "🏢 Register Company", "👤 Register Employee"])

        # TAB 1: SIGN IN
        with auth_tab1:
            with st.container(border=True):
                st.markdown('<div style="font-size:14px; font-weight:700; color:white; margin-bottom:12px;">Sign in to your account</div>', unsafe_allow_html=True)
                login_email = st.text_input("Email address", placeholder="e.g. admin@corp.com", key="login_email")
                login_pass = st.text_input("Password", type="password", key="login_pass")
                
                if st.button("Sign In", type="primary", use_container_width=True):
                    if not login_email or not login_pass:
                        st.error("Please enter email and password.")
                    else:
                        with st.spinner("Authenticating..."):
                            res = client.login(login_email, login_pass)
                            if res.get("success"):
                                token = res["data"]["access_token"]
                                st.session_state.access_token = token
                                
                                # Fetch user info from GET /auth/me
                                me_res = client.get_me(token)
                                if me_res.get("success"):
                                    st.session_state.user = me_res["data"]
                                    st.session_state.authenticated = True
                                    st.rerun()
                                else:
                                    st.error(f"Failed to load user profile: {me_res.get('error')}")
                            else:
                                st.error(res.get("error", "Authentication failed."))

        # TAB 2: REGISTER COMPANY (ADMIN)
        with auth_tab2:
            with st.container(border=True):
                st.markdown('<div style="font-size:14px; font-weight:700; color:white; margin-bottom:4px;">Bootstrap Company & Admin Account</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size:12px; color:#94a3b8; margin-bottom:12px;">Creates a new enterprise tenant and initial Admin account.</div>', unsafe_allow_html=True)
                
                c_name = st.text_input("Company Name", placeholder="Acme Corp", key="reg_c_name")
                a_name = st.text_input("Admin Full Name", placeholder="Jane Doe", key="reg_a_name")
                a_email = st.text_input("Admin Email Address", placeholder="admin@acme.com", key="reg_a_email")
                a_pass = st.text_input("Admin Password", type="password", key="reg_a_pass")

                if st.button("Register Company & Admin", type="primary", use_container_width=True):
                    if not c_name or not a_name or not a_email or not a_pass:
                        st.error("All registration fields are required.")
                    else:
                        with st.spinner("Registering company..."):
                            res = client.register_company(c_name, a_name, a_email, a_pass)
                            if res.get("success"):
                                data = res["data"]
                                st.session_state.reg_invite_info = data
                                st.success(f"Company '{data.get('company_name')}' registered successfully!")
                            else:
                                st.error(res.get("error", "Company registration failed."))

            # Display generated Invite Code box if company registration was successful
            if st.session_state.reg_invite_info:
                info = st.session_state.reg_invite_info
                render_html(
                    f"""
                    <div style="background-color:#1e1b4b; border:1px solid #4338ca; border-radius:10px; padding:16px; margin-top:16px;">
                        <div style="color:#818cf8; font-size:12px; font-weight:700; text-transform:uppercase; margin-bottom:6px;">IMPORTANT: Company Invite Code</div>
                        <div style="color:white; font-size:13px; margin-bottom:8px;">Share these details with employees to register for <b>{info.get('company_name')}</b>:</div>
                        <div style="background-color:#0d0e14; border:1px solid #312e81; border-radius:6px; padding:10px; font-family:monospace; font-size:14px; color:#34d399; margin-bottom:8px;">
                            Company ID: <b>{info.get('company_id')}</b><br>
                            Invite Code: <b>{info.get('invite_code')}</b>
                        </div>
                        <div style="color:#94a3b8; font-size:11px;">Admin Email: {info.get('admin_email')}</div>
                    </div>
                    """
                )

        # TAB 3: REGISTER EMPLOYEE
        with auth_tab3:
            with st.container(border=True):
                st.markdown('<div style="font-size:14px; font-weight:700; color:white; margin-bottom:4px;">Register as Employee</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size:12px; color:#94a3b8; margin-bottom:12px;">Requires Company ID and Invite Code provided by your Company Admin.</div>', unsafe_allow_html=True)
                
                emp_name = st.text_input("Full Name", placeholder="Bob Smith", key="reg_emp_name")
                emp_email = st.text_input("Email Address", placeholder="bob@acme.com", key="reg_emp_email")
                emp_pass = st.text_input("Password", type="password", key="reg_emp_pass")
                emp_comp_id = st.text_input("Company ID", placeholder="Paste Company ID here", key="reg_emp_comp_id")
                emp_invite = st.text_input("Company Invite Code", placeholder="INV-XXXXXXXX", key="reg_emp_invite")
                emp_role = st.selectbox("Role", options=["engineer", "hr", "sales", "support"], key="reg_emp_role")

                if st.button("Register Employee Account", type="primary", use_container_width=True):
                    if not emp_name or not emp_email or not emp_pass or not emp_comp_id or not emp_invite:
                        st.error("All employee registration fields are required.")
                    else:
                        with st.spinner("Registering employee..."):
                            res = client.register_employee(
                                full_name=emp_name,
                                email=emp_email,
                                password=emp_pass,
                                company_id=emp_comp_id,
                                role=emp_role,
                                invite_code=emp_invite,
                            )
                            if res.get("success"):
                                st.success("Employee account created successfully! Please switch to 'Sign In' tab to log in.")
                            else:
                                st.error(res.get("error", "Employee registration failed."))

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center; color:#64748b; font-size:12px;">🔒 Document authorization & multi-tenant boundaries are strictly enforced by the server backend.</div>',
            unsafe_allow_html=True,
        )

# ============================================================================
# SCREEN 2: AUTHENTICATED MAIN APPLICATION DASHBOARD
# ============================================================================
else:
    user = st.session_state.user or {}
    token = st.session_state.access_token

    # ====================================================================
    # TAB 1: ASK ASSISTANT
    # ====================================================================
    if st.session_state.current_tab == "Ask Assistant":
        head_c1, head_c2 = st.columns([3, 1])
        with head_c1:
            st.markdown(
                """
                <h2 style="color:white; font-size:22px; font-weight:700; margin:0 0 4px 0;">Ask Assistant</h2>
                <p style="color:#94a3b8; font-size:13px; margin:0;">Answers generated strictly from knowledge you are authorized to access</p>
                """,
                unsafe_allow_html=True,
            )
        with head_c2:
            st.markdown('<div style="text-align:right;"><span class="badge-accessible">● Permission-aware</span></div>', unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#1e2230; margin:16px 0 24px 0;'>", unsafe_allow_html=True)

        # Center Hero Content
        first_name = user.get("full_name", "User").split()[0]
        render_html(
            f"""
            <div style="text-align:center; padding:16px 0 16px 0;">
                <div style="display:inline-flex; align-items:center; justify-content:center; width:48px; height:48px; background:linear-gradient(135deg, #4f46e5, #7c3aed); border-radius:12px; margin-bottom:12px;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                </div>
                <h1 style="color:white; font-size:26px; font-weight:700; margin:0 0 6px 0;">Welcome, {first_name} ({user.get('role', '').upper()})</h1>
                <p style="color:#94a3b8; font-size:14px; margin:0 0 16px 0;">What would you like to ask the knowledge base?</p>
                <div class="pipeline-box">
                    <span class="pipeline-step">👤 JWT User</span> ➔
                    <span class="pipeline-step">🔒 Chroma Pre-Filter</span> ➔
                    <span class="pipeline-step">🔍 Retrieval</span> ➔
                    <span class="pipeline-step">✨ Gemini LLM</span> ➔
                    <span class="pipeline-step">📝 Answer</span>
                </div>
            </div>
            """
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Render Chat Messages History
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if "citations" in message and message["citations"]:
                    st.markdown("**Authorized Sources Used:**")
                    for citation in message["citations"]:
                        doc_title = citation.get("title", "Untitled Document")
                        doc_id = citation.get("document_id", "N/A")
                        st.markdown(f"`📄 {doc_title} (ID: {doc_id})`")

        # Chat Input Box
        user_query = st.chat_input("Ask a question about your organization's knowledge base...")

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.write(user_query)

            with st.chat_message("assistant"):
                with st.spinner("Executing pre-retrieval authorization search & generating answer..."):
                    res = client.send_question(user_query, access_token=token)
                    handle_unauthorized_error(res)

                    if res.get("success"):
                        data = res["data"]
                        answer = data.get("answer", "")
                        citations = data.get("citations", [])
                        st.write(answer)
                        if citations:
                            st.markdown("### 📚 Authorized Sources")
                            for c in citations:
                                st.markdown(f"📄 **{c.get('title')}** `(ID: {c.get('document_id')})`")
                        st.session_state.messages.append({"role": "assistant", "content": answer, "citations": citations})
                    else:
                        st.error(res.get("error", "Failed to process query."))

    # ====================================================================
    # TAB 2: SEARCH KNOWLEDGE
    # ====================================================================
    elif st.session_state.current_tab == "Search Knowledge":
        st.markdown('<h2 style="color:white; font-size:22px; font-weight:700; margin:0 0 4px 0;">Search Knowledge</h2>', unsafe_allow_html=True)
        st.markdown('<p style="color:#94a3b8; font-size:13px; margin:0 0 16px 0;">Permission-aware vector search is integrated directly into the Ask Assistant RAG pipeline.</p>', unsafe_allow_html=True)

        search_query = st.text_input("Query terms", placeholder="Enter query terms...", label_visibility="collapsed")
        if search_query:
            st.info("💡 To receive a grounded AI answer using your authorized company documents, ask your question in the 'Ask Assistant' tab!")

        # Fetch real company documents for live view
        doc_res = client.get_documents(access_token=token)
        handle_unauthorized_error(doc_res)

        if doc_res.get("success"):
            docs = doc_res["data"]
            st.markdown(f'<div style="font-size:13px; color:#64748b; margin-bottom:12px;">{len(docs)} authorized company documents found</div>', unsafe_allow_html=True)
            for d in docs:
                roles_str = ", ".join(d.get("allowed_roles", []))
                render_html(
                    f"""
                    <div class="dark-card" style="margin-bottom:12px; padding:16px;">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                            <div>
                                <div style="color:white; font-size:16px; font-weight:700; margin-bottom:4px;">{d.get('title')}</div>
                                <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                                    <span class="badge-doc">{d.get('file_type', 'doc').upper()}</span>
                                    <span style="color:#64748b; font-size:12px;">Roles: {roles_str}</span>
                                </div>
                            </div>
                            <span class="badge-accessible">ACCESSIBLE</span>
                        </div>
                        <div style="color:#475569; font-size:11px;">Document ID: {d.get('id')}</div>
                    </div>
                    """
                )
        else:
            st.warning("No documents available or failed to load documents.")

    # ====================================================================
    # TAB 3: DOCUMENTS
    # ====================================================================
    elif st.session_state.current_tab == "Documents":
        st.markdown(
            """
            <h2 style="color:white; font-size:22px; font-weight:700; margin:0 0 4px 0;">Company Documents</h2>
            <p style="color:#94a3b8; font-size:13px; margin:0 0 16px 0;">Company documents returned by authoritative backend authorization engine.</p>
            """,
            unsafe_allow_html=True,
        )

        # ADMIN ONLY: Upload Document UI Form
        if user.get("role") == "admin":
            with st.container(border=True):
                st.markdown('<div style="font-size:14px; font-weight:700; color:white; margin-bottom:4px;">📤 Admin Upload New Document</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size:12px; color:#94a3b8; margin-bottom:12px;">Persists binary document payload to MySQL LONGBLOB and indexes vector embeddings in ChromaDB with explicit boolean role flags.</div>', unsafe_allow_html=True)

                up_col1, up_col2 = st.columns([2, 2])
                with up_col1:
                    up_file = st.file_uploader("Select document file (.md, .pdf, .txt, .json)", type=["md", "markdown", "pdf", "txt", "json"])
                    up_title = st.text_input("Document Title (Optional)", placeholder="e.g. Q3 Engineering Roadmap")

                with up_col2:
                    st.markdown("<label style='font-size:13px; font-weight:600; color:#94a3b8;'>Permitted Employee Roles</label>", unsafe_allow_html=True)
                    role_eng = st.checkbox("Engineer", value=True)
                    role_hr = st.checkbox("HR", value=False)
                    role_sales = st.checkbox("Sales", value=False)
                    role_support = st.checkbox("Support", value=False)

                if st.button("Upload and Ingest Document", type="primary", use_container_width=True):
                    selected_roles = []
                    if role_eng: selected_roles.append("engineer")
                    if role_hr: selected_roles.append("hr")
                    if role_sales: selected_roles.append("sales")
                    if role_support: selected_roles.append("support")

                    if not up_file:
                        st.error("Please select a file to upload.")
                    elif not selected_roles:
                        st.error("At least one employee role permission must be selected.")
                    else:
                        with st.spinner("Uploading binary file to MySQL LONGBLOB and indexing in ChromaDB..."):
                            file_bytes = up_file.getvalue()
                            up_res = client.upload_document(
                                file_name=up_file.name,
                                file_bytes=file_bytes,
                                allowed_roles=selected_roles,
                                access_token=token,
                                title=up_title,
                            )
                            handle_unauthorized_error(up_res)

                            if up_res.get("success"):
                                doc_data = up_res["data"].get("document", {})
                                st.success(f"Document '{doc_data.get('title')}' uploaded successfully! (Indexed in ChromaDB: {doc_data.get('is_indexed')})")
                                st.rerun()
                            else:
                                st.error(up_res.get("error", "Document upload failed."))

            st.markdown("<br>", unsafe_allow_html=True)

        # FETCH AUTHORIZED DOCUMENTS FROM GET /documents
        doc_res = client.get_documents(access_token=token)
        handle_unauthorized_error(doc_res)

        if doc_res.get("success"):
            docs = doc_res["data"]
            if not docs:
                st.info("No authorized documents currently stored for your company/role.")
            else:
                d_cols = st.columns(3)
                for idx, d in enumerate(docs):
                    col_idx = idx % 3
                    with d_cols[col_idx]:
                        roles_list = d.get("allowed_roles", [])
                        roles_str = ", ".join(roles_list) if roles_list else "All Roles"
                        indexed_status = "✓ Indexed" if d.get("is_indexed") else "⏳ Indexing"
                        
                        render_html(
                            f"""
                            <div class="dark-card" style="margin-bottom:16px; padding:16px;">
                                <span class="badge-doc">{d.get('file_type', 'doc').upper()}</span>
                                <div style="color:white; font-size:15px; font-weight:700; margin:8px 0 4px 0;">{d.get('title')}</div>
                                <div style="color:#94a3b8; font-size:12px; margin-bottom:8px;">ID: {d.get('id')}</div>
                                <div style="color:#64748b; font-size:11px; margin-bottom:12px;">Allowed Roles: {roles_str}</div>
                                <hr style="border-color:#1e2230; margin:8px 0;">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <span style="color:#64748b; font-size:11px;">Company: {d.get('company_id')}</span>
                                    <span style="color:#34d399; font-size:11px; font-weight:600;">{indexed_status}</span>
                                </div>
                            </div>
                            """
                        )
        else:
            st.error(doc_res.get("error", "Failed to retrieve documents."))

    # ====================================================================
    # TAB 4: MY ACCESS
    # ====================================================================
    elif st.session_state.current_tab == "My Access":
        st.markdown(
            """
            <h2 style="color:white; font-size:22px; font-weight:700; margin:0 0 4px 0;">My Access Profile</h2>
            <p style="color:#94a3b8; font-size:13px; margin:0 0 16px 0;">Authoritative user identity and permissions loaded from MySQL backend.</p>
            """,
            unsafe_allow_html=True,
        )

        a_col1, a_col2 = st.columns(2)

        with a_col1:
            initials = (user.get("full_name", "U")[0]).upper()
            render_html(
                f"""
                <div class="dark-card" style="margin-bottom:16px;">
                    <div style="font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; margin-bottom:12px;">AUTHENTICATED IDENTITY (JWT)</div>
                    <div style="display:flex; align-items:center; gap:16px; margin-bottom:16px;">
                        <div class="avatar-user" style="width:48px; height:48px; font-size:18px;">{initials}</div>
                        <div>
                            <div style="color:white; font-size:18px; font-weight:700;">{user.get('full_name')}</div>
                            <div style="color:#94a3b8; font-size:13px; margin-bottom:4px;">User ID: {user.get('id')}</div>
                            <span class="badge-dept">{user.get('role')}</span>
                        </div>
                    </div>
                    <div style="font-size:11px; color:#64748b; margin-bottom:4px;">Email Address</div>
                    <div style="background-color:#0d0e14; border:1px solid #1f2333; border-radius:6px; padding:8px 12px; color:white; font-size:13px; margin-bottom:12px;">{user.get('email')}</div>
                </div>
                """
            )

        with a_col2:
            render_html(
                f"""
                <div class="dark-card" style="margin-bottom:16px;">
                    <div style="font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; margin-bottom:12px;">TENANT & AUTHORIZATION CONTEXT</div>
                    <div style="font-size:11px; color:#64748b; margin-bottom:4px;">Company ID (Multi-Tenant Isolation)</div>
                    <div style="background-color:#0d0e14; border:1px solid #1f2333; border-radius:6px; padding:8px 12px; color:#34d399; font-family:monospace; font-size:13px; margin-bottom:12px;">{user.get('company_id')}</div>
                    
                    <div style="font-size:11px; color:#64748b; margin-bottom:4px;">Assigned Role (Permission Engine Key)</div>
                    <div style="background-color:#0d0e14; border:1px solid #1f2333; border-radius:6px; padding:8px 12px; color:#818cf8; font-family:monospace; font-size:13px;">{user.get('role')}</div>
                </div>
                """
            )

        render_html(
            """
            <div class="dark-card">
                <div style="font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; margin-bottom:12px;">SECURITY BOUNDARIES</div>
                <div style="display:flex; gap:12px;">
                    <div style="background-color:#0d0e14; border:1px solid #1f2333; border-radius:6px; padding:10px 16px; color:#cbd5e1; font-size:13px;">🔒 Pre-Retrieval Vector Filtering</div>
                    <div style="background-color:#0d0e14; border:1px solid #1f2333; border-radius:6px; padding:10px 16px; color:#cbd5e1; font-size:13px;">🏢 Multi-Tenant Company Boundary</div>
                    <div style="background-color:#0d0e14; border:1px solid #1f2333; border-radius:6px; padding:10px 16px; color:#cbd5e1; font-size:13px;">🛡️ JWT Server-Side Verification</div>
                </div>
            </div>
            """
        )
