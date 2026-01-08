import streamlit as st
import database as db
import pandas as pd

# Page Config
st.set_page_config(
    page_title="VyaparMind",
    page_icon="🧠",
    layout="wide"
)

import ui_components as ui

# Initialize DB
db.init_db()

# Session State for Authentication
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# --- AUTHENTICATION FLOW ---
if not st.session_state["authenticated"]:
    # Custom CSS for Premium Split-Screen Landing Page
    st.markdown("""
        <style>
        /* --- MUST BE FIRST --- */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        
        /* --- GLOBAL RESETS --- */
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stHeader"] { visibility: hidden; }
        
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #ffffff;
        }

        /* --- REMOVE STREAMLIT PADDING --- */
        div.block-container {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }
        div[data-testid="stAppViewContainer"] {
            overflow: hidden;
            height: 100vh;
        }

        /* --- SPLIT LAYOUT GRID --- */
        [data-testid="stHorizontalBlock"] {
            gap: 0 !important;
            height: 100vh;
            min-height: 100vh;
            align-items: stretch;
        }
        
        /* --- COLUMN 1: LEFT PANEL (DARK) --- */
        div[data-testid="stColumn"]:nth-of-type(1) {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            position: relative;
            padding: 2rem;
            height: 100%; /* Force Full Height */
        }
        
        /* Pattern Overlay for Col 1 */
        div[data-testid="stColumn"]:nth-of-type(1)::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: radial-gradient(#334155 1px, transparent 1px);
            background-size: 40px 40px;
            opacity: 0.15;
            z-index: 0;
            pointer-events: none;
        }
        
        /* --- COLUMN 2: RIGHT PANEL (LIGHT) --- */
        div[data-testid="stColumn"]:nth-of-type(2) {
            background-color: #ffffff;
            display: flex;
            flex-direction: column;
            justify-content: center; /* Vertical Center */
            padding: 4rem;
            height: 100%; /* Force Full Height */
        }

        /* --- CONTENT STYLING --- */
        .brand-content {
            z-index: 10;
            text-align: center;
            color: white;
            max-width: 85%;
            margin-top: -5vh; /* Visual correction to appear perfectly centered */
        }

        .brand-logo-img {
            margin-bottom: -5rem; 
            width: clamp(350px, 45vw, 500px); /* LARGER BASE SIZE */
            display: block; 
            margin-left: auto;
            margin-right: auto;
        }

        .brand-title {
            font-size: clamp(4rem, 8vw, 6.5rem); /* SIGNIFICANTLY LARGER */
            font-weight: 800;
            letter-spacing: -2px;
            margin-bottom: 0.5rem;
            color: #ffffff; 
            background: none;
            -webkit-text-fill-color: initial;
            position: relative; 
            z-index: 20;
            line-height: 1;
        }

        .brand-tagline {
            font-size: clamp(1.1rem, 1.5vw, 1.8rem);
            font-weight: 700;
            color: #fbbf24;
            letter-spacing: 6px; /* More spacing for luxury feel */
            text-transform: uppercase;
            margin-bottom: 2rem;
            opacity: 0.95;
        }

        .brand-desc {
            font-size: clamp(1.2rem, 1.5vw, 1.6rem); /* Larger Body Text */
            color: #f1f5f9; /* Near White for better contrast */
            font-weight: 400; /* Regular weight instead of light */
            line-height: 1.6;
        }
        
        /* Auth Card Area */
        .auth-card {
            width: 100%;
            max-width: 500px; /* Wider card */
            margin: auto; 
            padding: 1rem;
        }
        
        /* Auth Headings */
        .auth-header {
            font-size: clamp(2.5rem, 4vw, 3.5rem); /* MUCH LARGER WELCOME */
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }
        .auth-sub {
            font-size: clamp(1rem, 1.2vw, 1.3rem);
            color: #64748b;
            margin-top: -5px;
            margin-bottom: 2.5rem;
        }

        /* Components overrides */
        div.stButton > button {
            background: #0f172a !important;
            color: white !important;
            border-radius: 12px; /* Softer corners */
            height: 4rem; /* Taller button */
            font-size: 1.2rem !important;
            font-weight: 700;
            letter-spacing: 0.5px;
            width: 100%;
            margin-top: 1.5rem;
            transition: all 0.2s;
        }
        div.stButton > button:hover {
            background: #1e293b !important;
            transform: translateY(-2px);
            box-shadow: 0 10px 20px -10px rgba(15, 23, 42, 0.5);
        }

        div[data-testid="stTextInput"] input {
            background-color: #f8fafc !important;
            border: 2px solid #e2e8f0 !important; /* Thicker border */
            padding: 1.2rem;
            border-radius: 12px;
            color: #0f172a !important;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }
        div[data-testid="stTextInput"] input:focus {
            background-color: white !important;
            border-color: #0f172a !important;
            box-shadow: 0 0 0 4px rgba(15, 23, 42, 0.1);
        }
        div[data-testid="stTextInput"] label {
            font-size: 1rem !important;
            font-weight: 600 !important;
            color: #334155 !important;
        }
        
        div.stTabs [data-baseweb="tab"] {
            font-size: 1.2rem;
            font-weight: 600;
            padding-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Use columns with gap 0
    col1, col2 = st.columns([1, 1], gap="small")
    
    with col1:
        # Prepare logo
        try:
            logo_choice = db.get_setting('app_logo') or "Ascending Lotus"
            logo_file = "logo_no_text_3.svg" if logo_choice == "Ascending Lotus" else "logo_no_text_1.svg"
            import base64
            with open(logo_file, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
            logo_html = f'<img src="data:image/svg+xml;base64,{data}" class="brand-logo-img">'
        except:
            logo_html = '<h1 style="font-size: 5rem;">🧠</h1>'

        # Render Left Panel Content
        st.markdown(f"""
            <div class="brand-content">
                {logo_html}
                <div class="brand-title">Vyapar<span style="color: #fbbf24">Mind</span></div>
                <div class="brand-tagline">Growth • Purity • Success</div>
                <p class="brand-desc">
                    The intelligent operating system for modern business.<br>
                    Seamless POS, real-time inventory, and predictive analytics.
                </p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        # RIGHT PANEL
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        # Combined HTML for Headers to ensure CSS styling works
        st.markdown("""
            <div class="auth-header">Welcome Back</div>
            <div class="auth-sub">Enter your credentials to access the workspace.</div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            login_user = st.text_input("Username / Email", key="login_user", placeholder="admin")
            login_pass = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("Sign In", use_container_width=True):
                success, msg = db.verify_user(login_user, login_pass)
                if success:
                    st.session_state["authenticated"] = True
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
                    
        with tab2:
            st.markdown("<br>", unsafe_allow_html=True)
            new_user = st.text_input("New Username", key="new_user")
            new_email = st.text_input("Email Address", key="new_email")
            new_pass = st.text_input("Choose Password", type="password", key="new_pass")
            
            if st.button("Create Account", use_container_width=True):
                if new_user and new_pass:
                    success, msg = db.create_user(new_user, new_pass, new_email)
                    if success:
                        st.success(msg)
                        st.info("Account created!")
                    else:
                        st.error(msg)
                else:
                    st.warning("All fields required")
        
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- MAIN APPLICATION ---
    # Show Sidebar with Logout
    ui.render_sidebar()
    if st.sidebar.button("Logout", type="primary"):
        st.session_state["authenticated"] = False
        st.rerun()

    # Main Page Content
    st.title("🧠 VyaparMind: Intelligent Retail")

    st.markdown("""
    ### Welcome to your Retail Management System
    Use the sidebar to navigate between modules.

    **Quick Status:**
    """)

    # Quick Stats (if DB has data)
    try:
        conn = db.get_connection()
        product_count = pd.read_sql_query("SELECT COUNT(*) as count FROM products", conn).iloc[0]['count']
        transaction_count = pd.read_sql_query("SELECT COUNT(*) as count FROM transactions", conn).iloc[0]['count']
        conn.close()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Products", product_count)
        col2.metric("Total Transactions", transaction_count)
        col3.metric("System Status", "Online 🟢")

    except Exception as e:
        st.error(f"Database Error: {e}")

    st.divider()
    st.info("👈 Select **Inventory**, **POS**, or **Dashboard** from the sidebar to begin.")
