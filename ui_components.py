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
        [data-testid="stSidebarUserContent"] {
            order: 1;
            padding-top: 1rem;
            display: flex;
            flex-direction: column;
            align-items: center; 
            text-align: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid #E6E7E8; /* SABIC Divider */
            padding-bottom: 1rem;
            width: 100%; 
        }
        [data-testid="stSidebarNav"] {
            order: 2;
        }
        
        [data-testid="stSidebarUserContent"] img {
             margin-left: auto;
             margin-right: auto;
        }

        /* Remove excess padding */
        section[data-testid="stSidebar"] div[class*="css-1d391kg"] {
            padding-top: 1rem;
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
            background-color: #041E42 !important; /* SABIC Navy */
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
        </style>
    """, unsafe_allow_html=True)
