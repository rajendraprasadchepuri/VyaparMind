import streamlit as st
import database as db
import pandas as pd

# Page Config
st.set_page_config(
    page_title="VyaparMind",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import ui_components as ui

# Initialize DB
db.init_db()

# Session State for Authentication
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# --- AUTHENTICATION FLOW ---
if not st.session_state["authenticated"]:
    # --- CUSTOM CSS: PREMIUM SPLIT-SCREEN ---
    st.markdown("""
        <style>
        /* --- MUST BE FIRST --- */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        
        /* --- GLOBAL RESETS --- */
        [data-testid="stSidebar"] { display: none; } /* HIDDEN on Login Page */
        [data-testid="stHeader"] { visibility: hidden; }
        
        html, body, [class*="css"] {
            font-family: 'Arial', 'Helvetica', sans-serif; /* Corporate Sans */
            background-color: #ffffff;
        }

        /* --- REMOVE STREAMLIT PADDING --- */
        div.block-container {
            padding: 0 !important;
            padding-top: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
            min-height: 100vh;
        }
        
        /* Remove top header decoration */
        header[data-testid="stHeader"] {
            display: none !important;
        }
        
        div[data-testid="stAppViewContainer"] {
            overflow: auto; /* Allow scrolling if content is tall */
            height: 100vh; /* Base height */
            background: transparent !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        
        /* Force root containers to have no spacing */
        div[class*="stApp"] {
            margin: 0 !important;
            padding: 0 !important;
        }

        /* --- SPLIT LAYOUT GRID --- */
        [data-testid="stHorizontalBlock"] {
            gap: 0 !important;
            min-height: 100vh; /* Grow with content */
            height: auto;
            align-items: stretch;
            padding-top: 0 !important;
        }

        /* --- INTERNAL SPACING RESET --- */
        [data-testid="stVerticalBlock"] {
            gap: 0 !important;
            padding-top: 0 !important;
        }
        
        /* --- COLUMN 1: LEFT PANEL (SABIC THEME) --- */
        div[data-testid="stColumn"]:nth-of-type(1) {
            padding-top: 0 !important;
            /* Official SABIC Palette Gradient: White to Very Light Grey */
            background: linear-gradient(135deg, #FFFFFF 0%, #E6E7E8 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            position: relative;
            padding: 2rem; /* Internal content padding - not top offset */
            min-height: 100vh; 
            height: auto;
        }

        /* Ensure inner blocks respect height for centering */
        div[data-testid="stColumn"]:nth-of-type(1) > div {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            width: 100%;
        }
        
        /* Pattern Overlay for Col 1 (Subtle for Light Mode) */
        div[data-testid="stColumn"]:nth-of-type(1)::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: radial-gradient(#cbd5e1 1px, transparent 1px); /* Darker dots */
            background-size: 40px 40px;
            opacity: 0.3;
            z-index: 0;
            pointer-events: none;
        }
        
        /* --- COLUMN 2: RIGHT PANEL (LIGHT) --- */
        /* --- COLUMN 2: RIGHT PANEL (LIGHT) --- */
        div[data-testid="stColumn"]:nth-of-type(2) {
            padding-top: 0 !important; /* Remove Streamlit default 64px */
            background-color: #ffffff;
            display: flex;
            flex-direction: column;
            justify-content: center !important; /* Force Vertical Center */
            padding: 4rem; /* Content padding */
            min-height: 100vh; /* Ensure it covers full height */
            height: auto;
        }
        
        /* Ensure inner blocks respect height */
        div[data-testid="stColumn"]:nth-of-type(2) > div {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        /* --- CONTENT STYLING --- */
        .brand-content {
            z-index: 10;
            text-align: center;
            color: #0f172a; /* Inverted to Dark */
            max-width: 100%; /* Removed 85% constraint to allow large logo */
            /* Removed negative margin for strict centering */
        }

        .brand-logo-img {
            margin-bottom: -90px;
            width: 450px !important; /* FORCED OVERRIDE */
            max-width: none !important;
            height: auto !important;
            display: block; 
            margin-left: auto;
            margin-right: auto;
        }

        .brand-title {
            font-size: 4rem; 
            font-weight: 700; 
            letter-spacing: -1px; 
            margin-bottom: 0.5rem;
            color: #009FDF; /* Theme Primary Blue */
            background: none;
            -webkit-text-fill-color: initial;
            position: relative; 
            z-index: 20;
            line-height: 1;
        }

        .brand-tagline {
            font-size: 1.1rem;
            font-weight: 700;
            color: #E35205; /* Theme Accent Orange */
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 2rem;
            opacity: 1;
        }

        .brand-desc {
            font-size: 1.1rem;
            color: #4D4D4D; /* SABIC Dark Grey Text */
            font-weight: 500; 
            line-height: 1.6;
            max-width: 600px;
            margin: auto;
        }
        
        /* Auth Card Area */
        .auth-card {
            width: 100%;
            max-width: 480px; /* Slightly narrower for focus */
            margin: auto; 
            padding: 1rem;
        }
        
        /* Auth Headings */
        .auth-header {
            font-size: 3rem; /* Still large but balanced */
            font-weight: 800;
            color: #4D4D4D; /* SABIC Dark Grey */
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }
        .auth-sub {
            font-size: 1.1rem;
            color: #64748b;
            margin-top: -5px;
            margin-bottom: 3rem; /* More gap */
        }

        /* Components overrides */
        div.stButton > button {
            background: #009FDF !important; /* SABIC Primary Blue */
            color: white !important;
            border-radius: 0px; /* SHARP CORNERS */
            height: 3.5rem; 
            font-size: 1.1rem !important;
            font-weight: 700;
            letter-spacing: 0.5px;
            width: 100%;
            margin-top: 1.5rem;
            transition: all 0.2s;
            border: none;
        }
        div.stButton > button:hover {
            background: #041E42 !important; /* SABIC Navy for Hover */
            transform: none; 
            box-shadow: none; 
        }

        /* UI DESIGNER: Corporate Accent Style */
        div[data-testid="stTextInput"] input {
            background-color: #F8FAFC !important; /* Subtle Slate for distinction */
            border: 1px solid #CBD5E1 !important; /* Clean light border */
            border-left: 5px solid #009FDF !important; /* SIGNATURE ACCENT: Primary Blue */
            padding: 12px 16px;
            border-radius: 2px; /* Minimal radius, almost sharp but smooth */
            color: #1E293B !important; /* Deep Slate Text */
            font-size: 1rem;
            font-weight: 500;
            height: 50px; 
            margin-bottom: 0.5rem;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        }
        
        div[data-testid="stTextInput"] input:focus {
            background-color: #FFFFFF !important;
            border-color: #009FDF !important;
            box-shadow: 0 4px 12px rgba(0, 159, 223, 0.15) !important; /* Elegant Glow */
            transform: translateY(-1px); /* Micro-interaction lift */
        }
        div[data-testid="stTextInput"] input:focus {
            background-color: white !important;
            border-color: #009FDF !important; /* SABIC Blue Focus */
            box-shadow: none;
        }
        div[data-testid="stTextInput"] label {
            font-size: 0.9rem !important;
            font-weight: 600 !important;
            color: #4D4D4D !important; /* SABIC Dark Grey */
            margin-bottom: 0.2rem;
        }
        
        div.stTabs [data-baseweb="tab"] {
            font-size: 1rem;
            font-weight: 600;
            padding-bottom: 0.8rem;
        }

        /* --- MOTION GRAPHICS ENGINE: FINAL MIX (Bloom + Flow) --- */
        
        /* 1. BLOOM KEYFRAMES (Intro) */
        @keyframes organic-bloom-center { 0% { transform: scaleY(0); opacity: 0; } 100% { transform: scaleY(1); opacity: 1; } }
        @keyframes organic-bloom-side { 0% { transform: scale(0) rotate(0deg); opacity: 0; } 100% { transform: scale(1) rotate(0deg); opacity: 1; } }
        @keyframes organic-pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }

        /* 2. FLOW KEYFRAMES (Loop) - Must include scale(1) to maintain Bloom state */
        @keyframes organic-flow-left { 
            0%, 100% { transform: scale(1) rotate(0deg); } 
            50% { transform: scale(1) rotate(-3deg); } 
        }
        @keyframes organic-flow-right { 
            0%, 100% { transform: scale(1) rotate(0deg); } 
            50% { transform: scale(1) rotate(3deg); } 
        }
        @keyframes organic-flow-center { 
            0%, 100% { transform: scale(1) skewX(0deg); } 
            50% { transform: scale(1) skewX(2deg); } 
        }

        /* 3. CHAINED ANIMATIONS */
        .motion-FinalMix .petal-center { 
            animation: 
                organic-bloom-center 1s ease-out forwards, 
                organic-flow-center 4s ease-in-out 1s infinite; /* Flow starts after 1s */
            transform-origin: bottom center;
        }
        .motion-FinalMix .petal-left { 
            animation: 
                organic-bloom-side 1s ease-out 0.2s forwards, 
                organic-flow-left 3s ease-in-out 1.2s infinite; /* Flow starts after 1.2s */
            opacity: 0; /* Hidden initially for delay */
            transform-origin: bottom right;
        }
        .motion-FinalMix .petal-right { 
            animation: 
                organic-bloom-side 1s ease-out 0.3s forwards, 
                organic-flow-right 3.2s ease-in-out 1.3s infinite; /* Flow starts after 1.3s */
            opacity: 0; /* Hidden initially for delay */
            transform-origin: bottom left;
        }
        .motion-FinalMix .logo-core { 
            animation: organic-pulse 3s infinite ease-in-out 1.5s; 
            transform-box: fill-box; 
        }

        /* General Container Float */
        .brand-logo-container svg {
            width: 450px !important;
            height: auto;
            display: block;
            margin: auto;
            /* Constant float for the whole container */
            animation: hover-float 4s ease-in-out infinite alternate;
        }
        @keyframes hover-float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-8px); }
            100% { transform: translateY(0px); }
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
            
            # MOTION GRAPHICS: Final Mix (Bloom + Flow)
            motion_class = "motion-FinalMix"
            
            # Inject Inline SVG
            with open(logo_file, "r") as f:
                svg_content = f.read().replace('\n', '').replace('\r', '')
            logo_html = f'<div class="brand-logo-container {motion_class}" style="margin-bottom: -90px;">{svg_content}</div>'
        except:
            logo_html = '<h1 style="font-size: 5rem;">🧠</h1>'

        # Render Left Panel Content
        st.markdown(f"""
            <div class="brand-content">
                {logo_html}
                <div class="brand-title">Vyapar<span style="color: #FFCD00">Mind</span></div>
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
