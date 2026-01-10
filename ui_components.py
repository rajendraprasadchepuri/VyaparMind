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
    import os
    if logo_choice and logo_choice != "Ascending Lotus" and os.path.exists(logo_choice):
        logo_file = logo_choice
    elif logo_choice == "Ascending Lotus":
         logo_file = "logo_no_text_3.svg"
    else:
         logo_file = "logo_no_text_1.svg" # Fallback
         
    # Center the logo in sidebar
    col1, col2, col3 = st.sidebar.columns([1, 4, 1])
    with col2:
        st.image(logo_file, use_container_width=True)
    
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
        .stButton>button, div.stFormSubmitButton > button {
            background-color: #009FDF !important; /* SABIC Blue */
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0px !important; /* SABIC SHARP CORNERS */
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        .stButton>button:hover, div.stFormSubmitButton > button:hover {
            background-color: #041E42 !important; /* SABIC Navy for Hover */
            color: white;
            box-shadow: none;
        }

        /* --- GLOBAL LAYOUT FIXES --- */
        
        /* 1. Prevent Tables from overflowing into other columns */
        div.stDataFrame {
            width: 100% !important;
            max-width: 100% !important;
            overflow-x: auto !important;
            display: block !important;
        }
        
        /* 2. Ensure Columns have breathing room */
        [data-testid="stHorizontalBlock"] {
            gap: 1rem !important;
        }

        /* 3. Metric Cards shouldn't bulge */
        [data-testid="stMetric"] {
            overflow-wrap: break-word;
            white-space: normal !important;
        }

        /* --- RESPONSIVENESS IMPROVEMENTS (MOBILE) --- */
        @media screen and (max-width: 768px) {
             /* Force metrics to stack or wrap better */
            [data-testid="stMetric"] {
                min-width: 100% !important;
                margin-bottom: 10px !important;
            }
            
            /* Adjust Top Header Spacing */
            .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            
            /* Sidebar robustness on mobile */
            section[data-testid="stSidebar"] {
                width: 250px !important;
            }
            
            /* CRITICAL: Force Columns to Wrap on Mobile */
            /* This effectively turns multi-column layouts into stacked or wrapped grids */
            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
            }
            [data-testid="stColumn"] {
                min-width: 100% !important; /* Force stack on very small screens */
                flex: 1 1 100% !important;
            }
            
            /* Reset gap for stacked items */
            [data-testid="stHorizontalBlock"] {
                gap: 0.5rem !important;
            }
        }

        /* Tabs & Expander Polish */
        div.stTabs [data-baseweb="tab"] {
            font-size: 1rem !important;
            font-weight: 700 !important;
            color: #4D4D4D !important;
        }
        div.stTabs [data-baseweb="tab"]:hover {
            color: #009FDF !important;
        }
        div.stTabs [aria-selected="true"] {
            color: #009FDF !important;
            border-bottom-color: #009FDF !important;
        }

        [data-testid="stExpander"] {
            border: 1px solid #E6E7E8 !important;
            background-color: #FFFFFF !important;
            border-radius: 2px !important;
        }
        [data-testid="stExpander"] summary {
            font-weight: 700 !important;
            color: #4D4D4D !important;
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
        .block-container .stButton > button, .block-container div.stFormSubmitButton > button {
            /* These will keep the Main Buttons (Vote, Submit) prominent and blue */
            background-color: #009FDF !important; 
            color: white !important;
        }
        /* POS Specific: Ensure Search/Find Buttons match Input Height */
        div[data-testid="stForm"] div[data-testid="stColumn"] button {
             margin-top: 0px !important; 
             height: 2.75rem !important; /* Matches default TextInput height roughly */
             padding-top: 0px !important;
             padding-bottom: 0px !important;
             align-self: flex-end !important;
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
            "🍽️ TableLink": "16_TableLink.py",
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
        },
        "System": {
            "🛡️ Super Admin": "99_SuperAdmin.py"
        }
    }
    
    # Tiers & Roles Config (Mirroring DB Logic for UI consistency)
    TIERS = {
        'Starter': ['1_Inventory.py', '2_POS.py', '3_Settings.py', '4_Dashboard.py'],
        'Professional': ['*'],
        'Business': ['1_Inventory.py', '2_POS.py', '3_Settings.py', '4_Dashboard.py', '6_FreshFlow.py', '7_VendorTrust.py', '8_VoiceAudit.py'],
        'Enterprise': ['*']
    }
    
    # Mapping "Feature Name" (DB) -> "File Basename" (FileSystem)
    MODULE_MAP = {
        "Inventory": "1_Inventory.py",
        "POS Terminal": "2_POS.py",
        "Settings": "3_Settings.py",
        "Dashboard": "4_Dashboard.py",
        "FreshFlow": "6_FreshFlow.py",
        "VendorTrust": "7_VendorTrust.py",
        "VoiceAudit": "8_VoiceAudit.py",
        "IsoBar": "9_IsoBar.py",
        "ShiftSmart": "10_ShiftSmart.py",
        "ChurnGuard": "11_ChurnGuard.py",
        "GeoViz": "12_GeoViz.py",
        "StockSwap": "13_StockSwap.py",
        "ShelfSense": "14_ShelfSense.py",
        "CrowdStock": "15_CrowdStock.py",
        "TableLink": "16_TableLink.py"
    }

    ROLES = {
        'staff': ['2_POS.py', '8_VoiceAudit.py'], 
        'manager': ['1_Inventory.py', '2_POS.py', '6_FreshFlow.py', '7_VendorTrust.py', '8_VoiceAudit.py', '4_Dashboard.py'],
        'admin': ['*'],
        'super_admin': ['*']
    }

    if sub_plan in TIERS:
        allowed_sub = TIERS[sub_plan]
    else:
        # Custom Plan Logic
        import database as db
        feats = db.get_plan_features(sub_plan)
        if feats:
            allowed_sub = ["4_Dashboard.py", "3_Settings.py"] # Always allowed basics
            for f in feats:
                if f in MODULE_MAP:
                    allowed_sub.append(MODULE_MAP[f])
        else:
            # Fallback for completely unknown/legacy plans
            allowed_sub = ['4_Dashboard.py', '3_Settings.py'] # Minimal access

    # Override: Super Admin gets all access regardless of plan setting
    if user_role == 'super_admin':
        allowed_sub = ['*']

    allowed_role = ROLES.get(user_role, [])
    
    current_page = st.session_state.get("current_page", "")

    # Render Groups
    for group, pages in PAGES.items():
        # Super Admin Filter: ONLY show 'System' group
        if user_role == 'super_admin' and group != 'System':
            continue

        # Pre-check visibility
        visible_pages = []
        for label, file_path in pages.items():
             # Special Hide for non-super_admin
             if "SuperAdmin" in file_path and user_role != "super_admin":
                 continue
                 
             is_role = '*' in allowed_role or file_path in allowed_role
             is_sub = '*' in allowed_sub or file_path in allowed_sub
             if is_role and is_sub:
                 visible_pages.append((label, file_path))
        
        if visible_pages:
            st.sidebar.caption(group.upper())
            for label, file_path in visible_pages:
                if st.sidebar.button(label, key=f"nav_{file_path}", use_container_width=True):
                     st.switch_page(f"pages/{file_path}")
        
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
                    margin-bottom: 1rem !important; 
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
        # Using vertical_alignment="center" natively to avoid CSS conflicts
        c_spacer, c_user, c_logout = st.columns([4, 2.5, 1], gap="small", vertical_alignment="center")

        
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


# --- SHARED DIALOGS ---
import textwrap
from datetime import datetime
import base64
import os
import database as db

@st.dialog("🧾 Bill Receipt")
def show_receipt_dialog(items, total_amount, subtotal, tax_amount, transaction_id=None, customer_info=None, points_redeemed=0, footer_msg=None):
    """
    Shared Receipt Dialog for POS and TableLink.
    
    Args:
        items (list): List of dicts with 'name', 'qty', 'total' (and optional 'price')
        total_amount (float): Final payable amount
        subtotal (float): Amount before tax
        tax_amount (float): Total tax amount
        transaction_id (str): Optional ID
        customer_info (str/dict): Optional customer details
        points_redeemed (float): Discount from points
        footer_msg (str): Custom footer message
    """
    
    # 1. Store Settings & Logo
    store_name = db.get_setting('store_name') or "Chings Chinese Restaurant"
    store_addr = db.get_setting('store_address') or "Telephone Colony, Hyderabad, India"
    store_phone = db.get_setting('store_phone') or "9876543210"
    
    if not footer_msg:
        footer_msg = "Thank you for dining with us!"

    # Logo Logic
    try:
        logo_choice = db.get_setting('app_logo') or "Ascending Lotus"
    except:
        logo_choice = "Ascending Lotus"

    if logo_choice and logo_choice != "Ascending Lotus" and os.path.exists(logo_choice):
        logo_file = logo_choice
    elif logo_choice == "Ascending Lotus":
         logo_file = "logo_no_text_3.svg"
    else:
         logo_file = "logo_no_text_1.svg"

    logo_b64 = ""
    try:
        if os.path.exists(logo_file):
            with open(logo_file, "rb") as image_file:
                logo_b64 = base64.b64encode(image_file.read()).decode()
    except:
        pass

    if logo_b64:
        mime = "image/svg+xml" if logo_file.endswith(".svg") else "image/png"
        logo_html = f'<img src="data:{mime};base64,{logo_b64}" style="max-height: 80px; width: auto;">'
    else:
        logo_html = '<span style="font-size: 40px;">🍚</span>'

    # 2. Metadata
    if not transaction_id:
        import secrets
        transaction_id = secrets.token_hex(4)
        
    date_str = datetime.now().strftime('%d-%b-%Y %H:%M:%S')

    # 3. HTML Construction
    # Use simple flat strings to avoid indentation issues
    html_bill = f"""
<div style="font-family: 'Courier New', monospace; padding: 20px; background: #fff; color: #000; border: 1px solid #ddd; max-width: 400px; margin: auto;">
<!-- Header -->
<div style="text-align: center; margin-bottom: 20px;">
<div style="display: flex; justify-content: center; margin-bottom: 10px;">
{logo_html}
</div>
<h2 style="margin: 0; font-weight: bold; font-size: 24px; text-transform: uppercase;">{store_name}</h2>
<p style="margin: 5px 0; font-size: 12px;">{store_addr}<br>Ph: {store_phone}</p>
</div>

<hr style="border-top: 1px dashed #000; margin: 10px 0;">

<!-- Metadata -->
<div style="font-size: 14px; margin-bottom: 10px;">
<strong>Receipt #:</strong> {transaction_id}<br>
<strong>Date:</strong> {date_str}
"""
    
    if customer_info:
        # customer_info can be a string or dict, handle string simple
        html_bill += f"<br><strong>Customer:</strong> {customer_info}"

    html_bill += f"""
</div>

<hr style="border-top: 1px dashed #000; margin: 10px 0;">

<!-- Table -->
<table style="width: 100%; font-size: 14px; border-collapse: collapse;">
<thead>
<tr style="border-bottom: 1px dashed #000;">
<th style="text-align: left; padding: 5px 0;">Item</th>
<th style="text-align: center; padding: 5px 0;">Qty</th>
<th style="text-align: right; padding: 5px 0;">Rate</th>
<th style="text-align: right; padding: 5px 0;">Amt</th>
</tr>
</thead>
<tbody>
"""
    
    for i in items:
        # Handle cases where dict keys might differ slightly between POS and TableLink
        name = i.get('name', 'Item')
        qty = i.get('qty', 0)
        total = i.get('total', 0.0)
        # rate calc
        rate = total / qty if qty > 0 else 0
        
        html_bill += f"""
<tr>
<td style="text-align: left; padding: 5px 0;">{name}</td>
<td style="text-align: center; padding: 5px 0;">{qty}</td>
<td style="text-align: right; padding: 5px 0;">₹{rate:.2f}</td>
<td style="text-align: right; padding: 5px 0;">₹{total:.2f}</td>
</tr>
"""

    html_bill += f"""
</tbody>
</table>

<hr style="border-top: 1px dashed #000; margin: 10px 0;">

<!-- Totals -->
<div style="text-align: right; font-size: 14px; line-height: 1.6;">
Subtotal: ₹{subtotal:.2f}<br>
CGST (2.5%): ₹{tax_amount/2:.2f}<br>
SGST (2.5%): ₹{tax_amount/2:.2f}<br>
"""
    if points_redeemed > 0:
        html_bill += f"<div style='color: green;'>Loyalty Disc: -₹{points_redeemed:.2f}</div>"

    html_bill += f"""
<div style="font-size: 20px; font-weight: bold; margin-top: 10px;">TOTAL: ₹{total_amount:.2f}</div>
</div>

<hr style="border-top: 2px solid #000; margin: 10px 0;">
<div style="text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 20px;">
NET PAYABLE: ₹{total_amount:.2f}
</div>

<hr style="border-top: 1px dashed #000; margin: 10px 0;">

<div style="text-align: center; font-size: 12px; margin-top: 20px;">
{footer_msg}
</div>
</div>
"""
    

    # A. Print Styles (Hidden by default, active on print)
    
    # B. Wrap HTML in printable class
    # We prepend the wrapper div start
    receipt_html_wrapped = f'<div id="printable-receipt-container" class="printable-receipt">{html_bill}</div>'
    
    st.markdown(receipt_html_wrapped, unsafe_allow_html=True)
    st.markdown("---")
    
    # C. Print Button (HTML/JS) 
    # Strategy change: Open a new window, write the receipt HTML there, and print IT.
    # This avoids all the CSS hiding issues with Streamlit's complex DOM.
    print_btn_html = """
    <script>
        function triggerPrint() {
            try {
                // 1. Get receipt content from Parent Frame
                var receiptParams = window.parent.document.getElementById('printable-receipt-container');
                
                if (!receiptParams) {
                    // Fallback to class name if ID fails
                    var elements = window.parent.document.getElementsByClassName('printable-receipt');
                    if (elements.length > 0) {
                         receiptParams = elements[0];
                    }
                }
                
                if (receiptParams) {
                    var content = receiptParams.innerHTML;
                    
                    // 2. Open new window
                    var printWindow = window.open('', '', 'height=600,width=400');
                    
                    // 3. Write HTML
                    printWindow.document.write('<html><head><title>Receipt</title>');
                    printWindow.document.write('<style>body{ font-family: "Courier New", monospace; margin: 0; padding: 0; }</style>');
                    printWindow.document.write('</head><body>');
                    printWindow.document.write(content);
                    printWindow.document.write('</body></html>');
                    
                    // 4. Print and Close
                    printWindow.document.close();
                    printWindow.focus();
                    
                    // Small timeout to ensure render
                    setTimeout(function() {
                        printWindow.print();
                        printWindow.close();
                    }, 500);
                    
                } else {
                    alert("Could not find receipt content to print.");
                }

            } catch (e) {
                console.error("Print Error: " + e);
                alert("Auto-print failed. Please use Ctrl+P.");
            }
        }
    </script>
    <div style="display: flex; justify-content: center; gap: 10px;">
        <button onclick="triggerPrint()" style="
            background-color: #009FDF; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            font-size: 16px; 
            cursor: pointer; 
            border-radius: 4px; 
            font-weight: bold;
            display: flex; align-items: center; gap: 5px;">
            🖨️ Print Bill
        </button>
    </div>
    """
    st.components.v1.html(print_btn_html, height=60)
    
    # Option: We can still offer a close button using Streamlit native if desired, 
    # but user said "Change close preview to print bill", so we focus on that.
    # The Dialog X button exists for closing.

