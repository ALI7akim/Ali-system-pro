import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection

# Page Configuration
st.set_page_config(page_title="ALI SYSTEM PRO", page_icon="📦", layout="centered")

# Custom Classic Computer Styling (Classic UI)
st.markdown("""
    <style>
    .main { background-color: #f0f0f0 !important; }
    .main .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 850px; }
    
    /* Colored Metrics */
    .metric-blue { background-color: #007acc; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #005999; }
    .metric-green { background-color: #2ea44f; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #227d3c; }
    .metric-orange { background-color: #f37023; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #d05616; }
    .metric-title { font-size: 13px; margin-bottom: 2px; color: white !important; }
    .metric-value { font-size: 20px; font-weight: bold; color: white !important; }
    
    /* Box Containers */
    .group-box {
        border: 1px solid #b8b8b8;
        background-color: #ececec;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 12px;
    }
    .group-title {
        font-size: 14px;
        font-weight: bold;
        color: #111111;
        margin-bottom: 10px;
        border-bottom: 2px solid #007acc;
        padding-bottom: 4px;
    }
    .computer-label { font-size: 12px; font-weight: bold; color: #444444; margin-bottom: 2px; }
    .stButton>button { border-radius: 4px !important; font-weight: bold !important; height: 40px; }
    </style>
""", unsafe_allow_html=True)

# --- File Loading Functions ---
@st.cache_data
def load_master_file(uploaded_file):
    if uploaded_file.name.endswith('x'): df = pd.read_excel(uploaded_file)
    else: df = pd.read_csv(uploaded_file)
    return df.astype(str).apply(lambda x: x.str.strip())

@st.cache_data
def load_stock_file(uploaded_file):
    if uploaded_file.name.endswith('x'): df_s = pd.read_excel(uploaded_file, header=[0, 1], dtype=str)
    else: df_s = pd.read_csv(uploaded_file, header=[0, 1], dtype=str)
    df_s.iloc[:, 0] = df_s.iloc[:, 0].str.strip().replace(r'\.0$', '', regex=True)
    plants = sorted(list(set([str(c[0]).strip() for c in df_s.columns if str(c[0]).strip().isdigit()])))
    return df_s, plants

# --- Initialize Session State Variables ---
for key in ["scanned_purchase", "scanned_internal", "scanned_damage", "scanned_recipe"]:
    if key not in st.session_state: st.session_state[key] = []
if "master_df" not in st.session_state: st.session_state.master_df = None
if "stock_df" not in st.session_state: st.session_state.stock_df = None
if "plants" not in st.session_state: st.session_state.plants = []
if "active_item" not in st.session_state: st.session_state.active_item = None

# App Navigation & Dynamic Keys
if "app_page" not in st.session_state: st.session_state.app_page = "setup"
if "selected_plant" not in st.session_state: st.session_state.selected_plant = ""
if "selected_tab" not in st.session_state: st.session_state.selected_tab = "Purchase Req"
if "barcode_key" not in st.session_state: st.session_state.barcode_key = 0

# --- Sidebar (System Files Upload) ---
with st.sidebar:
    st.header("⚙️ System Files")
    master_file = st.file_uploader("1️⃣ Barcode Master File (EXPORT BARCODE)", type=["xlsx", "xls", "csv"])
    stock_file = st.file_uploader("2️⃣ Stock Status File (Stock Status)", type=["xlsx", "xls", "csv"])
    
    if master_file:
        try: st.session_state.master_df = load_master_file(master_file); st.success("✅ Barcodes Loaded Successfully")
        except Exception as e: st.error(f"Error: {e}")
    if stock_file:
        try: st.session_state.stock_df, st.session_state.plants = load_stock_file(stock_file); st.success("✅ Stock Data Loaded Successfully")
        except Exception as e: st.error(f"Error: {e}")

# Protected Runtime Check
if st.session_state.master_df is None or st.session_state.stock_df is None:
    st.warning("⚠️ Please upload both the Barcode Master and Stock Status files from the sidebar to begin.")
    st.stop()

# Static System Options
unit_options = ["AU", "BAG", "BOX", "CAR", "G", "KG", "M", "ML", "PAC", "PC"]
order_options = {
    "500000 Customer Service": "500000", "500001 Fruit and vegetable": "500001",
    "500002 Deli section": "500002", "500003 General sections": "500003",
    "500004 Branch Office": "500004"
}

# ==============================================================================
# 🏢 PAGE 1: Configuration Setup (Plant & Tab Selection)
# ==============================================================================
if st.session_state.app_page == "setup":
    st.markdown('<div class="group-box"><div class="group-title">🏢 Step 1: Select Work Destination & Plant</div>', unsafe_allow_html=True)
    
    plant_idx = 0
    if st.session_state.selected_plant in st.session_state.plants:
        plant_idx = st.session_state.plants.index(st.session_state.selected_plant)
    plant_selected = st.selectbox("🏬 Choose Current Plant:", st.session_state.plants, index=plant_idx)
    
    tab_list = ["Purchase Req", "Internal Sale", "Damage Issue", "Recipe Issue"]
    tab_idx = tab_list.index(st.session_state.selected_tab) if st.session_state.selected_tab in tab_list else 0
    tab_selected = st.radio("📂 Choose Current Section:", tab_list, index=tab_idx, horizontal=True)
    
    st.write("")
    if st.button("🚀 Proceed to Scanning Screen 📥", type="primary", use_container_width=True):
        st.session_state.selected_plant = plant_selected
        st.session_state.selected_tab = tab_selected
        st.session_state.app_page = "scan"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 🔍 PAGE 2: Active Scanning Screen (Barcode & Qty on Same Row)
# ==============================================================================
elif st.session_state.app_page == "scan":
    mode = {"Purchase Req": "purchase", "Internal Sale": "internal", "Damage Issue": "damage", "Recipe Issue": "recipe"}[st.session_state.selected_tab]
    current_list = getattr(st.session_state, f"scanned_{mode}")
    
    c_nav1, c_nav2 = st.columns([1, 2])
    with c_nav1:
        if st.button("🔙 Change Plant / Section", use_container_width=True):
            st.session_state.app_page = "setup"
            st.session_state.active_item = None
            st.rerun()
    with c_nav2:
        st.markdown(f"<div style='text-align:right; font-size:14px; padding-top:8px; color:#555;'>📍 Plant: <b>{st.session_state.selected_plant}</b> | Section: <b>{st.session_state.selected_tab}</b></div>", unsafe_allow_html=True)
    
    st.divider()

    modes_list = ["Barcode", "SAP", "Orion"]
    if mode == "damage": modes_list.insert(0, "Short")
    search_mode = st.radio("Search Mode:", modes_list, horizontal=True)

    # Barcode Change Event Handler
    def on_barcode_change():
        input_key = f"barcode_input_{st.session_state.barcode_key}"
        raw_val = str(st.session_state[input_key]).strip()
        raw_val = ''.join(filter(str.isdigit, raw_val))
        if not raw_val or raw_val == "0" or raw_val == "": return
        
        if search_mode == "Short" and len(raw_val) >= 6: raw_val = raw_val[2:6]
        sap_code = None
        
        if search_mode == "Orion":
            col = next((c for c in st.session_state.stock_df.columns if 'Orion Item Code' in str(c).strip()), None)
            if col:
                m_stock = st.session_state.stock_df[st.session_state.stock_df[col].astype(str).str.strip().replace(r'\.0$', '', regex=True) == raw_val]
                if not m_stock.empty: sap_code = str(m_stock.iloc[0, 0]).strip().replace('.0', '')
        else:
            s_col = 'Item Barcode' if search_mode in ["Short", "Barcode"] else 'Item Code'
            m_temp = st.session_state.master_df.copy()
            act_col = next((c for c in m_temp.columns if s_col.lower() in str(c).lower()), s_col)
            m_temp[act_col] = m_temp[act_col].astype(str).str.strip().replace(r'\.0$', '', regex=True)
            m_master = m_temp[m_temp[act_col] == raw_val]
            if not m_master.empty: sap_code = str(m_master.iloc[0]['Item Code']).strip().replace('.0', '')

        if sap_code:
            row = st.session_state.master_df[st.session_state.master_df['Item Code'].astype(str).str.strip().replace(r'\.0$', '', regex=True) == sap_code].iloc[0]
            st.session_state.active_item = {
                "SAP": sap_code, "Name": str(row['Item Name']), "Supplier": str(row['Supplier Name']),
                "Factor": str(row['Factor']).split('.')[0], "Unit": str(row['UOM CODE']), "Supplier_ID": str(row['Supplier']).split('.')[0]
            }
        else:
            st.session_state.active_item = None

    # Barcode and Quantity Input Fields Side-by-Side
    col_inputs1, col_inputs2 = st.columns([2, 1])
    
    with col_inputs1:
        barcode_val = st.text_input("🔍 Scan Barcode or Enter Code (Digits Only) + Press Enter:", 
                        value="",
                        key=f"barcode_input_{st.session_state.barcode_key}", 
                        on_change=on_barcode_change)
        
    with col_inputs2:
        qty_input = st.number_input("✏️ Quantity:", min_value=0.0, value=0.0, step=0.001, format="%g", key=f"qty_input_{st.session_state.barcode_key}")

    # Injecting JavaScript Navigation Component
    components.html(f"""
        <script>
        function setupPosNavigation() {{
            var parentDoc = window.parent.document;
            var bInput = parentDoc.querySelector('input[data-testid="stTextInput"]');
            var qInput = parentDoc.querySelector('input[data-testid="stNumberInput"]');
            
            if(bInput && !
