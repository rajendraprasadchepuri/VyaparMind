import streamlit as st

def render_sidebar():
    """Renders the common sidebar elements (Logo, Branding, Selector)"""
    
    # --- Theme & Branding ---
    import database as db
    try:
        logo_choice = db.get_setting('app_logo') or "Ascending Lotus"
    except:
        logo_choice = "Ascending Lotus"

    # Logo
    if logo_choice == "Ascending Lotus":
         logo_file = "logo_no_text_3.svg"
    else:
         logo_file = "logo_no_text_1.svg" # Fixed: Use an existing file
         
    st.sidebar.image(logo_file, width=200) 
    
    # Dynamic Store Name
    import database as db
    try:
        store_name = db.get_setting('store_name') or "VyaparMind"
    except:
        store_name = "VyaparMind"
        
    if store_name == "VyaparMind":
        st.sidebar.markdown(f"## **<span style='color:#009FDF'>Vyapar</span><span style='color:#FFCD00'>Mind</span>**", unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"## **{store_name}**")
    st.sidebar.caption("Growth • Purity • Success")
    st.sidebar.markdown("---")

    # Apply Custom CSS for SABIC Theme (Industrial UI)
    st.markdown("""
        <style>
        /* Global Font & Colors using SABIC Tokens */
        html, body, [class*="css"] {
            font-family: 'Arial', 'Helvetica', sans-serif;
            background-color: #E6E7E8; /* SABIC Light Grey Background */
            color: #4D4D4D; /* SABIC Deep Grey Text */
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #C6C8CA; /* SABIC Light Grey Border */
        }

        /* ---------------------------------------------------- */
        /* KEY FIX: Move Logo ABOVE the Navigation Links        */
        /* ---------------------------------------------------- */
        [data-testid="stSidebar"] > div {
            display: flex;
            flex-direction: column;
        }
        
        /* User Content Container (Logo, Title, Logout) */
        [data-testid="stSidebarUserContent"] {
            order: 1;
            padding-top: 2rem;
            padding-bottom: 1rem;
            padding-left: 1rem; 
            padding-right: 1rem;
            display: flex;
            flex-direction: column;
            align-items: center; 
            text-align: center;
            width: 100%; 
            gap: 0.75rem; /* UNIFORM SPACING CONTROL */
        }

        /* Navigation Links */
        [data-testid="stSidebarNav"] {
            order: 2;
            padding-top: 1rem;
            border-top: 1px solid #E6E7E8; /* Separator between Header and Nav */
        }
        
        /* Logo Image */
        [data-testid="stSidebarUserContent"] img {
             margin-left: auto;
             margin-right: auto;
             margin-bottom: 0.5rem; /* Small gap below logo */
             max-width: 160px !important; /* Slightly smaller for balance */
        }
        
        /* Store Name (H2) */
        [data-testid="stSidebarUserContent"] h2 {
            margin-bottom: -0.5rem !important; /* Pull caption closer */
            padding-top: 0 !important;
            font-size: 1.4rem !important;
        }
        
        /* Caption */
        [data-testid="stSidebarUserContent"] .stCaption {
             margin-top: 0 !important;
             color: #888;
             font-size: 0.85rem;
        }

        /* Hide the default Streamlit Horizontal Rule to use CSS Border instead if preferred, 
           or style it to have 0 margin */
        [data-testid="stSidebarUserContent"] hr {
            margin: 0.5rem 0 !important;
            width: 100%;
        }

        /* Remove excess padding from inner containers */
        section[data-testid="stSidebar"] div[class*="css-1d391kg"] {
            padding-top: 0rem;
        }
        
        /* Card Styling for Metrics & Charts - SQUARE CORNERS */
        div[data-testid="stMetric"], div[data-testid="stContainer"], div.stDataFrame {
            background-color: #FFFFFF;
            border-radius: 0px !important; /* SABIC SHARP CORNERS */
            padding: 15px;
            box-shadow: none; /* Flat Industrial Look */
            border: 1px solid #E6E7E8;
            transition: none; /* No whimsical animations */
        }
        div[data-testid="stMetric"]:hover {
            border-color: #009FDF; /* Blue Border on Hover */
            transform: none;
            box-shadow: none;
        }

        /* Main Buttons - SQUARE & SABIC BLUE */
        .stButton>button {
            background-color: #009FDF !important; /* SABIC Blue */
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0px !important; /* SABIC SHARP CORNERS */
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        .stButton>button:hover {
            background-color: #041E42 !important; /* SABIC Navy for Hover */
            color: white;
            box-shadow: none;
        }

        /* Metric Value Color */
        div[data-testid="stMetricValue"] {
            color: #009FDF; /* SABIC Blue */
            font-weight: 700;
        }
        
        /* Headings */
        h1, h2, h3 {
            color: #4D4D4D; /* SABIC Dark Grey for Text */
            font-family: 'Arial', 'Helvetica', sans-serif;
            font-weight: 700;
        }
        
        /* Streamlit Nav Links */
        .st-emotion-cache-6qob1r {
            background-color: transparent;
        }

        /* HIDE 'app' (first item) from Sidebar Navigation */
        [data-testid="stSidebarNav"] > ul > li:first-child {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)



def require_auth():
    """Enforces authentication on pages"""
    if not st.session_state.get("authenticated", False):
        st.switch_page("app.py")

def render_top_header():
    """Renders the top right header with Username and Logout. 
       MUST BE CALLED BEFORE st.title()"""
    if st.session_state.get("authenticated", False):
        
        # CSS to reduce top padding so header sits high
        st.markdown("""
            <style>
                .block-container {
                    padding-top: 1rem !important; 
                }
                /* Compact Button */
                div[data-testid="stButton"] button {
                    height: 2.2rem;
                    min-height: 2.2rem;
                    padding-top: 0.2rem;
                    padding-bottom: 0.2rem;
                }
            </style>
        """, unsafe_allow_html=True)

        # Uses columns to push content to the far right
        # Spacing: [Spacer, User Label, Logout Button]
        c_spacer, c_user, c_logout = st.columns([6, 2, 1])
        
        with c_user:
            username = st.session_state.get('username', 'Admin User') 
            # Right aligned text
            st.markdown(f"<div style='text-align: right; white-space: nowrap; font-weight: 600; color: #4D4D4D; padding-top: 5px;'>👤 {username}</div>", unsafe_allow_html=True)
            
        with c_logout:
            if st.button("Logout", key="top_logout_btn", type="primary", use_container_width=True):
                st.session_state["authenticated"] = False
                st.session_state["username"] = None
                st.rerun()
        
        # No divider, keep it clean/tight

