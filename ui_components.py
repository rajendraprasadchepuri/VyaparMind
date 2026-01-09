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
            padding-top: 0rem !important; /* Aggressively reduced */
            padding-bottom: 1rem;
            padding-left: 1rem; 
            padding-right: 1rem;
            display: flex;
            flex-direction: column;
            align-items: center; 
            text-align: center;
            width: 100%; 
            gap: 0rem !important; /* REMOVED GAP */
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
             margin-bottom: -1rem !important; /* Pull content closer */
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


        /* HIDE Native Navigation completely */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* --- SIDEBAR SPECIFIC BUTTON STYLING --- */
        /* Target buttons ONLY inside the sidebar */
        [data-testid="stSidebar"] .stButton > button {
            width: 100%;
            border: none;
            background-color: transparent !important; /* Transparent by default */
            color: #4D4D4D !important; /* Dark Grey Text */
            text-align: left;
            padding: 0.5rem 0.5rem;
            font-weight: 600;
            border-radius: 4px !important;
            border-left: 3px solid transparent !important;
            transition: all 0.2s ease;
            box-shadow: none !important;
            margin-bottom: 2px;
        }

        /* Hover Effect for Sidebar Links */
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: #F0F2F5 !important;
            border-left: 3px solid #009FDF !important; /* Blue accent on recoil */
            color: #009FDF !important;
            padding-left: 0.8rem; /* Slide effect */
        }
        
        /* Locked Button Style (Disabled) */
        [data-testid="stSidebar"] .stButton > button:disabled {
            background-color: transparent !important;
            color: #999 !important;
            border: none !important;
            opacity: 0.6;
            cursor: not-allowed;
            font-style: italic;
        }
        
        /* Sidebar Group Headers */
        [data-testid="stSidebar"] .stCaption {
            font-size: 0.75rem;
            font-weight: 800;
            color: #888;
            letter-spacing: 1px;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
        }
        
        /* Ensure Main Content Buttons stay properly styled (Reset override if any leak) */
        .block-container .stButton > button {
            /* These will keep the Main Buttons (Vote, Submit) prominent and blue */
            background-color: #009FDF; 
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- CUSTOM NAVIGATION LOGIC ---
    # We rebuild the nav manually to support RBAC/Tiers
    
    user_role = st.session_state.get('role', 'staff')
    
    # 1. Fetch Subscription
    try:
        sub_plan = db.get_setting('subscription_plan') or 'Starter'
    except:
        sub_plan = 'Starter'
    
    st.sidebar.markdown(f"**Plan**: <span style='color:#009FDF'>{sub_plan}</span> | **Role**: {user_role.title()}", unsafe_allow_html=True)
    if sub_plan != "Enterprise":
        if st.sidebar.button("🚀 Upgrade to Enterprise"):
            st.switch_page("pages/3_Settings.py") # Redirect to settings to upgrade
    
    st.sidebar.markdown("---")
    
    # Define All Pages Map
    # Key: Label, Value: File Path (basename)
    # We group them for clarity
    PAGES = {
        "Operations": {
            "📊 Dashboard": "4_Dashboard.py",
            "💳 POS Terminal": "2_POS.py",
            "📦 Inventory": "1_Inventory.py",
            "🍏 FreshFlow (Zero-Waste)": "6_FreshFlow.py",
            "🚚 VendorTrust": "7_VendorTrust.py",
            "🗣️ VoiceAudit": "8_VoiceAudit.py",
        },
        "Intelligence": {
            "🌡️ IsoBar (Forecast)": "9_IsoBar.py",
            "👥 ShiftSmart (Staff)": "10_ShiftSmart.py",
            "🗺️ GeoViz (Heatmap)": "12_GeoViz.py",
        },
        "Innovation": {
            "🛡️ ChurnGuard": "11_ChurnGuard.py",
            "🕸️ StockSwap": "13_StockSwap.py",
            "🧬 ShelfSense": "14_ShelfSense.py",
            "🔮 CrowdStock": "15_CrowdStock.py",
        },
        "Admin": {
            "⚙️ Settings": "3_Settings.py"
        }
    }
    
    # Tiers & Roles Config (Mirroring DB Logic for UI consistency)
    TIERS = {
        'Starter': ['1_Inventory.py', '2_POS.py', '3_Settings.py', '4_Dashboard.py'],
        'Business': ['1_Inventory.py', '2_POS.py', '3_Settings.py', '4_Dashboard.py', '6_FreshFlow.py', '7_VendorTrust.py', '8_VoiceAudit.py'],
        'Enterprise': ['*']
    }
    ROLES = {
        'staff': ['2_POS.py', '8_VoiceAudit.py'], 
        'manager': ['1_Inventory.py', '2_POS.py', '6_FreshFlow.py', '7_VendorTrust.py', '8_VoiceAudit.py', '4_Dashboard.py'],
        'admin': ['*']
    }

    allowed_sub = TIERS.get(sub_plan, [])
    allowed_role = ROLES.get(user_role, [])
    
    current_page = st.session_state.get("current_page", "")

    # Render Groups
    for group, pages in PAGES.items():
        st.sidebar.caption(group.upper())
        for label, file_path in pages.items():
            
            # Check Permission
            is_role_allowed = '*' in allowed_role or file_path in allowed_role
            is_sub_allowed = '*' in allowed_sub or file_path in allowed_sub
            
            if is_role_allowed:
                if is_sub_allowed:
                    # Unlocked Page
                    if st.sidebar.button(label, key=f"nav_{file_path}", use_container_width=True):
                         st.switch_page(f"pages/{file_path}")
                else:
                    # Locked by Subscription
                    st.sidebar.button(f"🔒 {label}", key=f"lock_{file_path}", disabled=True, use_container_width=True)
            else:
                # Hidden for Role (Don't show Admin pages to Staff)
                pass 
                
        st.sidebar.markdown("") # Spacer



def require_auth():
    """Enforces authentication on pages"""
    if not st.session_state.get("authenticated", False):
        st.switch_page("app.py")

def render_top_header():
    """Renders the top right header with Username and Logout. 
       MUST BE CALLED BEFORE st.title()"""
    if st.session_state.get("authenticated", False):
        
        # REVERTED FLOAT: Back to standard flow but optimized spacing
        st.markdown("""
            <style>
                /* Reduce top padding slightly, but keep enough for aesthetics */
                .block-container {
                    padding-top: 2rem !important; 
                }
                
                /* Ensure Header Container has proper spacing */
                div[data-testid="stHorizontalBlock"]:nth-of-type(1) {
                    margin-bottom: 1rem !important; /* Positive margin to prevent overlap */
                    align-items: center;
                }
                
                /* Username styling */
                #user-label {
                    text-align: right; 
                    white-space: nowrap; 
                    font-weight: 600; 
                    color: #4D4D4D; 
                    margin-right: 10px;
                    padding-top: 4px;
                }
                
                /* Compact Button - Scoped to Header Block Only */
                div[data-testid="stHorizontalBlock"]:nth-of-type(1) button {
                    height: 2.2rem !important;
                    min-height: 2.2rem !important;
                    padding: 0px 20px !important;
                    border-radius: 4px !important;
                    font-size: 0.9rem !important;
                    font-weight: 600 !important;
                    box-shadow: none !important;
                    line-height: normal !important; /* Ensure text creates 1 line */
                }
            </style>
        """, unsafe_allow_html=True)

        # Uses columns to push content to the far right. 
        # Ratios: Spacer (4), User Label (2.5), Logout Button (1)
        # Relaxed spacer to ensure content has enough width to not clip
        c_spacer, c_user, c_logout = st.columns([4, 2.5, 1], gap="small")

        
        with c_user:
            username = st.session_state.get('username')
            if not username or str(username) == 'None':
                username = 'Admin User'
            st.markdown(f"<div id='user-label'>👤 {username}</div>", unsafe_allow_html=True)
            
        with c_logout:
            if st.button("Logout", key="top_logout_btn", type="primary", use_container_width=True):
                st.session_state["authenticated"] = False
                st.session_state["username"] = None
                st.rerun()

