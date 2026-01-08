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
        
    st.sidebar.markdown(f"## **{store_name}**")
    st.sidebar.caption("Growth • Purity • Success")
    st.sidebar.markdown("---")

    # Apply Custom CSS for Lotus Theme (Advanced UI)
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
            background-color: #f7f9fc;
        }
        
        /* Sidebar Styling: Clean & White */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e0e0e0;
        }

        /* ---------------------------------------------------- */
        /* KEY FIX: Move Logo ABOVE the Navigation Links        */
        /* ---------------------------------------------------- */
        /* 1. Target the internal container of the sidebar */
        [data-testid="stSidebar"] > div {
            display: flex;
            flex-direction: column;
        }
        
        /* 2. Move the User Content (Logo + My Widgets) to the TOP (Order 1) */
        /*    AND Center Align everything for professional look */
        [data-testid="stSidebarUserContent"] {
            order: 1;
            padding-top: 1rem;
            display: flex;
            flex-direction: column;
            align-items: center; /* Center horizontally */
            text-align: center;  /* Center text */
        }
        
        /* 3. Move the Navigation to the BOTTOM (Order 2) */
        [data-testid="stSidebarNav"] {
            order: 2;
        }
        
        /* Optional: Add spacing between logo and nav */
        [data-testid="stSidebarUserContent"] {
            margin-bottom: 2rem;
            border-bottom: 1px solid #f0f0f0;
            padding-bottom: 1rem;
            width: 100%; /* Ensure full width for centering to work */
        }
        
        /* Force Image centering if needed */
        [data-testid="stSidebarUserContent"] img {
             margin-left: auto;
             margin-right: auto;
        }

        /* Remove excess padding */
        section[data-testid="stSidebar"] div[class*="css-1d391kg"] {
            padding-top: 1rem;
        }
        
        /* Card Styling for Metrics & Charts */
        div[data-testid="stMetric"], div[data-testid="stContainer"], div.stDataFrame {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.04);
            transition: transform 0.2s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.08);
        }

        /* Main Gradient Buttons */
        .stButton>button {
            background: linear-gradient(135deg, #004e92 0%, #000428 100%);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 500;
            letter-spacing: 0.5px;
        }
        .stButton>button:hover {
            opacity: 0.9;
            box-shadow: 0 4px 12px rgba(0, 78, 146, 0.3);
            border: none;
            color: white;
        }

        /* Metric Value Color */
        div[data-testid="stMetricValue"] {
            color: #004e92;
            font-weight: 600;
        }
        
        /* Headings */
        h1, h2, h3 {
            color: #000428;
        }
        </style>
    """, unsafe_allow_html=True)
