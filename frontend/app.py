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
    page_title="Enterprise AI Knowledge Hub",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Modern Custom CSS with Comfortably Scaled Font Sizes & Crisp Symbols
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* Global Background & Typography */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #111827 0%, #070a12 75%) !important;
        color: #f8fafc !important;
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
        font-size: 17px !important;
    }

    /* Preserve Streamlit Material Icons */
    span[data-testid="stIconMaterial"], 
    span[data-testid="stIconCustom"],
    i[class*="material-icons"],
    .material-symbols-outlined {
        font-family: 'Material Symbols Outlined', 'Material Icons' !important;
        font-style: normal !important;
        font-weight: normal !important;
    }

    /* Force text color & font family across standard typography elements */
    .stApp p, 
    .stApp span:not([data-testid="stIconMaterial"]):not([data-testid="stIconCustom"]):not(.material-symbols-outlined), 
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #f8fafc;
    }
    div[data-testid="stMarkdownContainer"] p {
        color: #cbd5e1 !important;
        font-size: 17px !important;
        line-height: 1.75 !important;
    }
    label[data-testid="stWidgetLabel"] p {
        color: #e2e8f0 !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        letter-spacing: 0.4px !important;
        margin-bottom: 6px !important;
    }

    /* Fix Checkbox Alignment */
    div[data-testid="stCheckbox"] label[data-testid="stWidgetLabel"] p {
        margin-bottom: 0px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stCheckbox"] {
        padding-top: 4px !important;
        padding-bottom: 4px !important;
    }

    /* Custom Streamlit Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        padding-top: 1rem !important;
        min-width: 310px !important;
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
        background-color: #111827 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 8px !important;
    }
    .main .block-container {
        padding: 2.5rem 3.5rem !important;
        max-width: 1360px !important;
    }

    /* Streamlit Bordered Container Styling */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(17, 24, 39, 0.75) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 30px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
    }

    /* Common Card Styles */
    .glass-card {
        background: rgba(17, 24, 39, 0.7);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 26px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .glass-card-hover:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 14px 35px rgba(99, 102, 241, 0.2);
    }

    /* Badges */
    .badge-accessible {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-radius: 20px;
        padding: 6px 16px;
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 0.5px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .badge-doc {
        background: rgba(99, 102, 241, 0.18);
        color: #a5b4fc;
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 6px;
        padding: 5px 14px;
        font-size: 14px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-dept {
        background: rgba(139, 92, 246, 0.18);
        color: #c084fc;
        border: 1px solid rgba(139, 92, 246, 0.35);
        border-radius: 6px;
        padding: 5px 14px;
        font-size: 14px;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge-admin {
        background: rgba(236, 72, 153, 0.18);
        color: #f472b6;
        border: 1px solid rgba(236, 72, 153, 0.35);
        border-radius: 6px;
        padding: 5px 14px;
        font-size: 14px;
        font-weight: 700;
        text-transform: uppercase;
    }

    /* User Avatars */
    .avatar-user {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
        color: white;
        border-radius: 50%;
        font-weight: 800;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }

    /* Metric Header Cards */
    .metric-card {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 16px 18px;
        display: flex;
        align-items: center;
        gap: 14px;
        min-height: 76px;
        overflow: hidden;
    }
    .metric-icon {
        width: 44px;
        height: 44px;
        min-width: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
    }
    .metric-card-content {
        min-width: 0;
        flex: 1;
    }
    .metric-card-value {
        color: white;
        font-size: 13px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Pipeline Flow Box */
    .pipeline-box {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 14px;
        padding: 18px 32px;
        display: inline-flex;
        align-items: center;
        gap: 16px;
        color: #94a3b8;
        font-size: 15px;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.4);
    }
    .pipeline-step {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #f8fafc;
        font-weight: 700;
        font-size: 15px;
    }

    /* Custom Streamlit Button Styling */
    div.stButton > button {
        background: rgba(30, 41, 59, 0.85) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        border-radius: 12px !important;
        padding: 14px 24px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        white-space: nowrap !important;
        min-height: 50px !important;
        line-height: 1.4 !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div.stButton > button:hover {
        border-color: #6366f1 !important;
        background: rgba(49, 46, 129, 0.8) !important;
        color: #ffffff !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    div.stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 50%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.45) !important;
    }
    div.stButton > button[data-testid="baseButton-primary"]:hover {
        box-shadow: 0 6px 28px rgba(99, 102, 241, 0.65) !important;
        transform: translateY(-1px) !important;
    }

    /* Delete Button Styling */
    div.stButton > button[key^="del_doc_"] {
        background: rgba(153, 27, 27, 0.25) !important;
        color: #fca5a5 !important;
        border: 1px solid rgba(239, 68, 68, 0.4) !important;
        border-radius: 10px !important;
        font-size: 14px !important;
        padding: 8px 16px !important;
        min-height: 40px !important;
    }
    div.stButton > button[key^="del_doc_"]:hover {
        background: rgba(220, 38, 38, 0.45) !important;
        color: #ffffff !important;
        border-color: #ef4444 !important;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3) !important;
    }

    /* File Uploader Custom Styling Fix (100% Fix for text overlap uploadUpload) */
    section[data-testid="stFileUploaderDropzone"] {
        background-color: rgba(11, 15, 25, 0.95) !important;
        border: 1.5px dashed rgba(99, 102, 241, 0.4) !important;
        border-radius: 12px !important;
        padding: 18px 24px !important;
    }
    section[data-testid="stFileUploaderDropzone"]:hover {
        border-color: #6366f1 !important;
        background-color: rgba(17, 24, 39, 0.95) !important;
    }
    section[data-testid="stFileUploaderDropzone"] button {
        background: rgba(30, 41, 59, 0.9) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        padding: 8px 18px !important;
        font-size: 14px !important;
        min-height: 40px !important;
        line-height: 1.4 !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
    }
    /* Hide the first icon child span inside file uploader button to eliminate duplicate icon text 'upload' */
    section[data-testid="stFileUploaderDropzone"] button span:first-child:not(:only-child),
    section[data-testid="stFileUploaderDropzone"] button span[data-testid="stIconMaterial"],
    div[data-testid="stFileUploader"] span[data-testid="stIconMaterial"] {
        display: none !important;
    }

    /* Input styling */
    div.stTextInput > div > div > input {
        background-color: rgba(11, 15, 25, 0.95) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        font-size: 16px !important;
    }
    div.stTextInput > div > div > input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.3) !important;
    }
    div.stSelectbox > div > div {
        background-color: rgba(11, 15, 25, 0.95) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        border-radius: 12px !important;
        font-size: 16px !important;
    }

    /* Alert Banners Styling */
    div[data-testid="stAlert"] {
        background: rgba(15, 23, 42, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 14px !important;
        color: #f8fafc !important;
        padding: 16px 20px !important;
    }

    /* Streamlit Chat Message & Avatar Styling */
    div[data-testid="stChatMessage"] {
        background: rgba(17, 24, 39, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 14px !important;
        padding: 18px 22px !important;
        margin-bottom: 16px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    }
    div[data-testid="stChatMessageContent"] p {
        color: #f8fafc !important;
        font-size: 16px !important;
        line-height: 1.6 !important;
    }

    /* Monospace Code formatting */
    .mono-code {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 15px !important;
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
        <div style="padding:18px 14px; border-bottom:1px solid rgba(255,255,255,0.08); display:flex; align-items:center; gap:12px; margin-bottom:18px;">
            <div style="width:42px; height:42px; background:linear-gradient(135deg, #6366f1, #8b5cf6, #d946ef); border-radius:12px; display:flex; align-items:center; justify-content:center; box-shadow:0 4px 18px rgba(99,102,241,0.45);">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
            </div>
            <div>
                <div style="color:white; font-weight:800; font-size:16px; letter-spacing:-0.3px; margin:0;">Secure Knowledge AI</div>
                <div style="color:#94a3b8; font-size:12px; font-weight:600; margin:0;">Enterprise Hub</div>
            </div>
        </div>
        """
    )



    if st.session_state.authenticated and st.session_state.user:
        st.markdown('<div style="font-size:11px; font-weight:800; color:#64748b; letter-spacing:1px; margin:16px 12px 10px 12px;">NAVIGATION</div>', unsafe_allow_html=True)
        
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
            <div style="background:rgba(17,24,39,0.85); border:1px solid rgba(255,255,255,0.1); border-radius:14px; padding:16px; margin-top:auto;">
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
                    <div class="avatar-user" style="width:42px; height:42px; font-size:16px;">{initials}</div>
                    <div style="overflow:hidden;">
                        <div style="color:white; font-weight:700; font-size:15px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{user_info.get('full_name')}</div>
                        <div style="color:#818cf8; font-size:13px; font-weight:600; font-family:'JetBrains Mono',monospace;">{role_label}</div>
                    </div>
                </div>
            </div>
            """
        )
        if st.button("Sign Out", key="btn_logout", use_container_width=True):
            handle_logout()
    else:
        st.markdown('<div style="font-size:14px; color:#94a3b8; padding:12px; text-align:center;">Please authenticate to access authorized knowledge.</div>', unsafe_allow_html=True)


# ============================================================================
# SCREEN 1: AUTHENTICATION UI (UNAUTHENTICATED)
# ============================================================================
if not st.session_state.authenticated:
    st.markdown("<br>", unsafe_allow_html=True)
    l_col1, l_col2, l_col3 = st.columns([0.3, 2.4, 0.3])

    with l_col2:
        render_html(
            """
            <div style="text-align:center; margin-bottom:32px;">
                <div style="display:inline-flex; align-items:center; justify-content:center; width:64px; height:64px; background:linear-gradient(135deg, #6366f1, #8b5cf6, #d946ef); border-radius:20px; margin-bottom:18px; box-shadow:0 10px 30px rgba(99,102,241,0.5);">
                    <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                </div>
                <h1 style="color:white; font-size:32px; font-weight:800; letter-spacing:-0.5px; margin:0 0 10px 0;">Enterprise Knowledge Assistant</h1>
                <p style="color:#94a3b8; font-size:16px; max-width:560px; margin:0 auto; line-height:1.6;">Instant AI answers powered exclusively by company documents you are authorized to see. Fully secure and private.</p>
            </div>
            """
        )

        auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔑 Sign In", "🏢 Register Organization", "👤 Register Employee"])

        # TAB 1: SIGN IN
        with auth_tab1:
            with st.container(border=True):
                st.markdown('<div style="font-size:17px; font-weight:700; color:white; margin-bottom:16px;">Sign in to your enterprise account</div>', unsafe_allow_html=True)
                login_email = st.text_input("Email address", placeholder="e.g. admin@corp.com", key="login_email")
                login_pass = st.text_input("Password", type="password", key="login_pass")
                
                if st.button("Sign In", type="primary", use_container_width=True):
                    if not login_email or not login_pass:
                        st.error("Please enter email and password.")
                    else:
                        with st.spinner("Signing in..."):
                            res = client.login(login_email, login_pass)
                            if res.get("success"):
                                token = res["data"]["access_token"]
                                st.session_state.access_token = token
                                
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
                st.markdown('<div style="font-size:17px; font-weight:700; color:white; margin-bottom:4px;">Register Organization & Administrator</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size:14px; color:#94a3b8; margin-bottom:16px;">Create a new company workspace and setup your administrator account.</div>', unsafe_allow_html=True)
                
                c_name = st.text_input("Company Name", placeholder="Acme Corp", key="reg_c_name")
                a_name = st.text_input("Admin Full Name", placeholder="Jane Doe", key="reg_a_name")
                a_email = st.text_input("Admin Email Address", placeholder="admin@acme.com", key="reg_a_email")
                a_pass = st.text_input("Admin Password", type="password", key="reg_a_pass")

                if st.button("Create Organization Account", type="primary", use_container_width=True):
                    if not c_name or not a_name or not a_email or not a_pass:
                        st.error("All registration fields are required.")
                    else:
                        with st.spinner("Setting up organization workspace..."):
                            res = client.register_company(c_name, a_name, a_email, a_pass)
                            if res.get("success"):
                                data = res["data"]
                                st.session_state.reg_invite_info = data
                                st.success(f"Company '{data.get('company_name')}' registered successfully!")
                            else:
                                st.error(res.get("error", "Company registration failed."))

            if st.session_state.reg_invite_info:
                info = st.session_state.reg_invite_info
                render_html(
                    f"""
                    <div style="background:rgba(30,27,75,0.85); border:1px solid #6366f1; border-radius:16px; padding:20px; margin-top:18px;">
                        <div style="color:#a5b4fc; font-size:13px; font-weight:800; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px;">🔐 IMPORTANT: Organization Invite Details</div>
                        <div style="color:white; font-size:14px; margin-bottom:12px;">Share these details with team members so they can join <b>{info.get('company_name')}</b>:</div>
                        <div style="background:#070a12; border:1px solid rgba(99,102,241,0.4); border-radius:10px; padding:14px; font-family:'JetBrains Mono',monospace; font-size:14px; color:#34d399; margin-bottom:10px; line-height:1.8;">
                            Organization ID: <span style="color:#ffffff;">{info.get('company_id')}</span><br>
                            Invite Code: <span style="color:#34d399; font-weight:700;">{info.get('invite_code')}</span>
                        </div>
                        <div style="color:#94a3b8; font-size:12px;">Admin Email: {info.get('admin_email')}</div>
                    </div>
                    """
                )

        # TAB 3: REGISTER EMPLOYEE
        with auth_tab3:
            with st.container(border=True):
                st.markdown('<div style="font-size:17px; font-weight:700; color:white; margin-bottom:4px;">Join Your Team Workspace</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size:14px; color:#94a3b8; margin-bottom:16px;">Enter the Organization ID and Invite Code provided by your administrator.</div>', unsafe_allow_html=True)
                
                emp_name = st.text_input("Full Name", placeholder="Bob Smith", key="reg_emp_name")
                emp_email = st.text_input("Email Address", placeholder="bob@acme.com", key="reg_emp_email")
                emp_pass = st.text_input("Password", type="password", key="reg_emp_pass")
                emp_comp_id = st.text_input("Organization ID", placeholder="Paste Organization ID here", key="reg_emp_comp_id")
                emp_invite = st.text_input("Organization Invite Code", placeholder="INV-XXXXXXXX", key="reg_emp_invite")
                emp_role = st.selectbox("Department Role", options=["engineer", "hr", "sales", "support"], format_func=lambda x: {"engineer": "Engineering", "hr": "Human Resources", "sales": "Sales & Marketing", "support": "Customer Support"}.get(x, x), key="reg_emp_role")

                if st.button("Create Employee Account", type="primary", use_container_width=True):
                    if not emp_name or not emp_email or not emp_pass or not emp_comp_id or not emp_invite:
                        st.error("All employee registration fields are required.")
                    else:
                        with st.spinner("Verifying invite credentials..."):
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
            '<div style="text-align:center; color:#64748b; font-size:13px;">🛡️ Encrypted enterprise workspace. Access is restricted by verified department permissions.</div>',
            unsafe_allow_html=True,
        )

# ============================================================================
# SCREEN 2: AUTHENTICATED MAIN APPLICATION DASHBOARD
# ============================================================================
else:
    user = st.session_state.user or {}
    token = st.session_state.access_token

    # Metric Bar Header
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        render_html(
            f"""
            <div class="metric-card">
                <div class="metric-icon" style="background:rgba(99,102,241,0.18); color:#818cf8;">🏢</div>
                <div class="metric-card-content">
                    <div style="font-size:11px; font-weight:800; color:#64748b; text-transform:uppercase; letter-spacing:0.5px;">ORGANIZATION</div>
                    <div class="metric-card-value" title="{user.get('company_id')}">{user.get('company_id')}</div>
                </div>
            </div>
            """
        )
    with m_col2:
        role_badge = "badge-admin" if user.get("role") == "admin" else "badge-dept"
        role_disp = "ADMINISTRATOR" if user.get("role") == "admin" else user.get("role", "").upper()
        render_html(
            f"""
            <div class="metric-card">
                <div class="metric-icon" style="background:rgba(139,92,246,0.18); color:#c084fc;">🔑</div>
                <div class="metric-card-content">
                    <div style="font-size:11px; font-weight:800; color:#64748b; text-transform:uppercase; letter-spacing:0.5px;">YOUR ROLE</div>
                    <div><span class="{role_badge}">{role_disp}</span></div>
                </div>
            </div>
            """
        )
    with m_col3:
        render_html(
            """
            <div class="metric-card">
                <div class="metric-icon" style="background:rgba(16,185,129,0.18); color:#34d399;">🛡️</div>
                <div class="metric-card-content">
                    <div style="font-size:11px; font-weight:800; color:#64748b; text-transform:uppercase; letter-spacing:0.5px;">SECURITY LEVEL</div>
                    <div style="color:#34d399; font-size:14px; font-weight:700;">Access Protected</div>
                </div>
            </div>
            """
        )
    with m_col4:
        render_html(
            """
            <div class="metric-card">
                <div class="metric-icon" style="background:rgba(6,182,212,0.18); color:#22d3ee;">✨</div>
                <div class="metric-card-content">
                    <div style="font-size:11px; font-weight:800; color:#64748b; text-transform:uppercase; letter-spacing:0.5px;">AI ASSISTANT</div>
                    <div style="color:#22d3ee; font-size:14px; font-weight:700;">Gemini Enterprise</div>
                </div>
            </div>
            """
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ====================================================================
    # TAB 1: ASK ASSISTANT
    # ====================================================================
    if st.session_state.current_tab == "Ask Assistant":
        head_c1, head_c2 = st.columns([3, 1])
        with head_c1:
            st.markdown(
                """
                <h2 style="color:white; font-size:28px; font-weight:800; letter-spacing:-0.4px; margin:0 0 6px 0;">Ask Assistant</h2>
                <p style="color:#94a3b8; font-size:16px; margin:0;">Instant AI answers powered by your company's authorized knowledge library</p>
                """,
                unsafe_allow_html=True,
            )
        with head_c2:
            st.markdown('<div style="text-align:right;"><span class="badge-accessible">🛡️ Protected Access</span></div>', unsafe_allow_html=True)

        st.markdown("<hr style='border-color:rgba(255,255,255,0.1); margin:18px 0 26px 0;'>", unsafe_allow_html=True)

        # Center Hero Content
        first_name = user.get("full_name", "User").split()[0]
        render_html(
            f"""
            <div style="text-align:center; padding:16px 0 24px 0;">
                <h1 style="color:white; font-size:30px; font-weight:800; margin:0 0 10px 0;">Welcome, {first_name} 👋</h1>
                <p style="color:#94a3b8; font-size:16px; margin:0 0 24px 0;">Ask any question about your team's projects, internal policies, or documentation.</p>
                <div class="pipeline-box">
                    <span class="pipeline-step">🔑 Verified Identity</span> ➜
                    <span class="pipeline-step">🛡️ Access Control</span> ➜
                    <span class="pipeline-step">🔍 Knowledge Search</span> ➜
                    <span class="pipeline-step">✨ AI Processing</span> ➜
                    <span class="pipeline-step">📝 Instant Answer</span>
                </div>
            </div>
            """
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Render Chat Messages History
        for message in st.session_state.messages:
            msg_avatar = "👤" if message["role"] == "user" else "✨"
            with st.chat_message(message["role"], avatar=msg_avatar):
                st.write(message["content"])
                if "citations" in message and message["citations"]:
                    st.markdown("**Referenced Sources:**")
                    for citation in message["citations"]:
                        doc_title = citation.get("title", "Untitled Document")
                        doc_id = citation.get("document_id", "N/A")
                        st.markdown(f"`📄 {doc_title} (Ref: #{doc_id[:8]})`")

        # Chat Input Box
        user_query = st.chat_input("Ask a question about your authorized enterprise knowledge base...")

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user", avatar="👤"):
                st.write(user_query)

            with st.chat_message("assistant", avatar="✨"):
                with st.spinner("Searching authorized knowledge base and generating answer..."):
                    res = client.send_question(user_query, access_token=token)
                    handle_unauthorized_error(res)

                    if res.get("success"):
                        data = res["data"]
                        answer = data.get("answer", "")
                        citations = data.get("citations", [])
                        st.write(answer)
                        if citations:
                            st.markdown("### 📚 Referenced Sources")
                            for c in citations:
                                st.markdown(f"📄 **{c.get('title')}** `(Ref: #{c.get('document_id', '')[:8]})`")
                        st.session_state.messages.append({"role": "assistant", "content": answer, "citations": citations})
                    else:
                        st.error(res.get("error", "Failed to process query."))

    # ====================================================================
    # TAB 2: SEARCH KNOWLEDGE
    # ====================================================================
    elif st.session_state.current_tab == "Search Knowledge":
        st.markdown('<h2 style="color:white; font-size:26px; font-weight:800; margin:0 0 6px 0;">Knowledge Library</h2>', unsafe_allow_html=True)
        st.markdown('<p style="color:#94a3b8; font-size:15px; margin:0 0 24px 0;">Search and explore company documents available to your team.</p>', unsafe_allow_html=True)

        doc_res = client.get_documents(access_token=token)
        handle_unauthorized_error(doc_res)

        if doc_res.get("success"):
            docs = doc_res["data"]
            st.markdown(f'<div style="font-size:15px; color:#94a3b8; margin-bottom:18px;"><b>{len(docs)}</b> authorized documents available for your account.</div>', unsafe_allow_html=True)
            
            for d in docs:
                roles_list = d.get("allowed_roles", [])
                role_names = [r.title() for r in roles_list]
                roles_str = ", ".join(role_names) if role_names else "All Departments"
                render_html(
                    f"""
                    <div class="glass-card glass-card-hover" style="margin-bottom:16px; padding:22px;">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                            <div>
                                <div style="color:white; font-size:19px; font-weight:700; margin-bottom:8px;">{d.get('title')}</div>
                                <div style="display:flex; align-items:center; gap:12px; margin-bottom:10px;">
                                    <span class="badge-doc">{d.get('file_type', 'doc').upper()}</span>
                                    <span style="color:#cbd5e1; font-size:15px;">Department Access: <b>{roles_str}</b></span>
                                </div>
                            </div>
                            <span class="badge-accessible">✓ Full Access</span>
                        </div>
                        <div style="color:#64748b; font-size:14px; font-family:'JetBrains Mono',monospace;">Document Ref: #{d.get('id', '')[:8]}</div>
                    </div>
                    """
                )
                if user.get("role") == "admin":
                    if st.button("🗑️ Delete Document", key=f"del_doc_lib_{d.get('id')}", use_container_width=True):
                        with st.spinner("Deleting document from repository & vector index..."):
                            del_res = client.delete_document(d.get("id"), token)
                            handle_unauthorized_error(del_res)
                            if del_res.get("success"):
                                st.success(f"Document '{d.get('title')}' deleted successfully!")
                                st.rerun()
                            else:
                                st.error(del_res.get("error", "Failed to delete document."))
        else:
            st.warning("No documents available or failed to load documents.")

    # ====================================================================
    # TAB 3: DOCUMENTS
    # ====================================================================
    elif st.session_state.current_tab == "Documents":
        st.markdown(
            """
            <h2 style="color:white; font-size:26px; font-weight:800; margin:0 0 6px 0;">Company Document Repository</h2>
            <p style="color:#94a3b8; font-size:15px; margin:0 0 24px 0;">Centralized document library with automatic permission controls.</p>
            """,
            unsafe_allow_html=True,
        )

        # ADMIN ONLY: Upload Document UI Form
        if user.get("role") == "admin":
            with st.container(border=True):
                st.markdown('<div style="font-size:17px; font-weight:700; color:white; margin-bottom:6px;">📤 Upload New Document</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size:14px; color:#94a3b8; margin-bottom:18px;">Add PDF, Markdown, or text files to your organization\'s knowledge library.</div>', unsafe_allow_html=True)

                up_col1, up_col2 = st.columns([2, 2])
                with up_col1:
                    up_file = st.file_uploader("Select document file (.md, .pdf, .txt, .json)", type=["md", "markdown", "pdf", "txt", "json"])
                    up_title = st.text_input("Document Title (Optional)", placeholder="e.g. Q3 Engineering Roadmap")

                with up_col2:
                    st.markdown("<label style='font-size:15px; font-weight:700; color:#e2e8f0;'>Who can view this document?</label>", unsafe_allow_html=True)
                    role_eng = st.checkbox("Engineering Team 💻", value=True)
                    role_hr = st.checkbox("Human Resources 👥", value=False)
                    role_sales = st.checkbox("Sales Team 💼", value=False)
                    role_support = st.checkbox("Support Team 🎧", value=False)

                if st.button("Upload Document", type="primary", use_container_width=True):
                    selected_roles = []
                    if role_eng: selected_roles.append("engineer")
                    if role_hr: selected_roles.append("hr")
                    if role_sales: selected_roles.append("sales")
                    if role_support: selected_roles.append("support")

                    if not up_file:
                        st.error("Please select a file to upload.")
                    elif not selected_roles:
                        st.error("At least one department role must be selected.")
                    else:
                        with st.spinner("Uploading document to company repository..."):
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
                                st.success(f"Document '{doc_data.get('title')}' uploaded successfully!")
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
                        role_names = [r.title() for r in roles_list]
                        roles_str = ", ".join(role_names) if role_names else "All Departments"
                        indexed_status = "✓ Search Ready" if d.get("is_indexed") else "⏳ Processing"
                        
                        render_html(
                            f"""
                            <div class="glass-card glass-card-hover" style="margin-bottom:18px; padding:22px;">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                                    <span class="badge-doc">{d.get('file_type', 'doc').upper()}</span>
                                    <span style="color:#34d399; font-size:13px; font-weight:700;">{indexed_status}</span>
                                </div>
                                <div style="color:white; font-size:18px; font-weight:700; margin:6px 0;">{d.get('title')}</div>
                                <div style="color:#64748b; font-size:13px; font-family:'JetBrains Mono',monospace; margin-bottom:12px;">Ref: #{d.get('id', '')[:8]}</div>
                                <div style="color:#cbd5e1; font-size:14px; margin-bottom:14px;">Department Access: <b>{roles_str}</b></div>
                            </div>
                            """
                        )
                        if user.get("role") == "admin":
                            if st.button("🗑️ Delete Document", key=f"del_doc_repo_{d.get('id')}", use_container_width=True):
                                with st.spinner("Deleting document from repository & vector index..."):
                                    del_res = client.delete_document(d.get("id"), token)
                                    handle_unauthorized_error(del_res)
                                    if del_res.get("success"):
                                        st.success(f"Document '{d.get('title')}' deleted successfully!")
                                        st.rerun()
                                    else:
                                        st.error(del_res.get("error", "Failed to delete document."))
        else:
            st.error(doc_res.get("error", "Failed to retrieve documents."))

    # ====================================================================
    # TAB 4: MY ACCESS
    # ====================================================================
    elif st.session_state.current_tab == "My Access":
        st.markdown(
            """
            <h2 style="color:white; font-size:26px; font-weight:800; margin:0 0 6px 0;">My Profile & Access</h2>
            <p style="color:#94a3b8; font-size:15px; margin:0 0 24px 0;">Your verified employee profile and active security permissions.</p>
            """,
            unsafe_allow_html=True,
        )

        a_col1, a_col2 = st.columns(2)

        with a_col1:
            initials = (user.get("full_name", "U")[0]).upper()
            render_html(
                f"""
                <div class="glass-card" style="margin-bottom:18px;">
                    <div style="font-size:11px; font-weight:800; color:#64748b; letter-spacing:1px; margin-bottom:16px;">USER PROFILE</div>
                    <div style="display:flex; align-items:center; gap:18px; margin-bottom:18px;">
                        <div class="avatar-user" style="width:56px; height:56px; font-size:22px;">{initials}</div>
                        <div>
                            <div style="color:white; font-size:20px; font-weight:800;">{user.get('full_name')}</div>
                            <div style="color:#94a3b8; font-size:13px; font-family:'JetBrains Mono',monospace;">Employee ID: {user.get('id', '')[:8]}</div>
                            <div style="margin-top:6px;"><span class="badge-dept">{user.get('role')}</span></div>
                        </div>
                    </div>
                    <div style="font-size:12px; color:#94a3b8; margin-bottom:6px;">Email Address</div>
                    <div style="background:rgba(11,15,25,0.95); border:1px solid rgba(255,255,255,0.12); border-radius:10px; padding:12px 16px; color:white; font-size:15px;">{user.get('email')}</div>
                </div>
                """
            )

        with a_col2:
            render_html(
                f"""
                <div class="glass-card" style="margin-bottom:18px;">
                    <div style="font-size:11px; font-weight:800; color:#64748b; letter-spacing:1px; margin-bottom:16px;">ORGANIZATION & ACCESS LEVEL</div>
                    <div style="font-size:12px; color:#94a3b8; margin-bottom:6px;">Organization Account ID</div>
                    <div style="background:rgba(11,15,25,0.95); border:1px solid rgba(255,255,255,0.12); border-radius:10px; padding:12px 16px; color:#34d399; font-family:'JetBrains Mono',monospace; font-size:14px; margin-bottom:16px;">{user.get('company_id')}</div>
                    
                    <div style="font-size:12px; color:#94a3b8; margin-bottom:6px;">Department Role</div>
                    <div style="background:rgba(11,15,25,0.95); border:1px solid rgba(255,255,255,0.12); border-radius:10px; padding:12px 16px; color:#818cf8; font-family:'JetBrains Mono',monospace; font-size:14px;">{user.get('role', '').title()}</div>
                </div>
                """
            )

        render_html(
            """
            <div class="glass-card">
                <div style="font-size:11px; font-weight:800; color:#64748b; letter-spacing:1px; margin-bottom:16px;">ACTIVE ENTERPRISE GUARANTEES</div>
                <div style="display:flex; gap:16px;">
                    <div style="background:rgba(11,15,25,0.95); border:1px solid rgba(255,255,255,0.12); border-radius:12px; padding:14px 22px; color:#f1f5f9; font-size:14px; font-weight:600;">🔒 Automated Permission Enforcement</div>
                    <div style="background:rgba(11,15,25,0.95); border:1px solid rgba(255,255,255,0.12); border-radius:12px; padding:14px 22px; color:#f1f5f9; font-size:14px; font-weight:600;">🏢 Isolated Company Workspace</div>
                    <div style="background:rgba(11,15,25,0.95); border:1px solid rgba(255,255,255,0.12); border-radius:12px; padding:14px 22px; color:#f1f5f9; font-size:14px; font-weight:600;">🛡️ Verified Enterprise Auth</div>
                </div>
            </div>
            """
        )
