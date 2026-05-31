import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import streamlit.components.v1 as components

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
            
            if(bInput && !bInput.dataset.hooked) {{
                bInput.focus();
                bInput.dataset.hooked = "true";
                bInput.addEventListener('keydown', function(e) {{
                    if(e.key === 'Enter') {{
                        setTimeout(function() {{ if(qInput) {{ qInput.focus(); qInput.select(); }} }}, 300);
                    }}
                }});
            }}
            
            if(qInput && !qInput.dataset.hooked) {{
                qInput.dataset.hooked = "true";
                qInput.addEventListener('keydown', function(e) {{
                    if(e.key === 'Enter') {{
                        var saveBtn = parentDoc.querySelector('button[kind="primary"]');
                        if(saveBtn) {{ setTimeout(function() {{ saveBtn.click(); }}, 100); }}
                    }}
                }});
            }}
        }}
        setInterval(setupPosNavigation, 500);
        </script>
    """, height=0)

    st.markdown('<div class="group-box"><div class="group-title">📋 Active Item Details</div>', unsafe_allow_html=True)

    if st.session_state.active_item:
        item = st.session_state.active_item
        s_match = st.session_state.stock_df[st.session_state.stock_df.iloc[:, 0].astype(str).str.strip().replace(r'\.0$', '', regex=True) == item['SAP']]
        
        live_stock = "-"
        if not s_match.empty:
            p_col = [c for c in st.session_state.stock_df.columns if str(c[0]).strip() == st.session_state.selected_plant]
            if p_col: 
                live_stock = str(s_match.iloc[0][p_col[0]]).split('.')[0]

        sales_info = "No sales history recorded"
        if not s_match.empty:
            sales_cols = [c for c in st.session_state.stock_df.columns if "Total Sales" in str(c[0])]
            if sales_cols:
                month_map = {str(sc[1]).strip(): sc for sc in sales_cols}
                sales_segments = []
                for m_name, m_col in month_map.items():
                    try: val_g = f"{float(s_match.iloc[0][m_col]):g}"
                    except: val_g = "0"
                    sales_segments.append(f"<b>{m_name}:</b> {val_g}")
                sales_info = " &nbsp;|&nbsp; ".join(sales_segments)

        st.markdown(f"""
            <table style="width:100%; border-collapse: collapse; font-size:13px; background-color: white;">
                <tr style="border-bottom: 1px solid #ddd;"><td style="padding: 6px; font-weight:bold; width:30%;">SAP Code:</td><td style="padding: 6px; font-family: monospace; color:#007acc;">{item['SAP']}</td></tr>
                <tr style="border-bottom: 1px solid #ddd;"><td style="padding: 6px; font-weight:bold;">Description:</td><td style="padding: 6px; font-weight:bold; color:#111;">{item['Name']}</td></tr>
                <tr style="border-bottom: 1px solid #ddd;"><td style="padding: 6px; font-weight:bold;">Company / Supplier:</td><td style="padding: 6px; color:#555; font-weight:bold;">{item['Supplier']} <small style='color:#888;'>({item['Supplier_ID']})</small></td></tr>
                <tr style="border-bottom: 1px solid #ddd;"><td style="padding: 6px; font-weight:bold;">Live Stock:</td><td style="padding: 6px; font-weight:bold; color:#2ea44f;">{live_stock}</td></tr>
                <tr>
                    <td style="padding: 6px; font-weight:bold;">Sales History:</td>
                    <td style="padding: 6px; background-color: #fcf8e3; color: #c09853; font-size: 12px; border-radius:4px;">{sales_info}</td>
                </tr>
            </table>
        """, unsafe_allow_html=True)
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            u_sel = st.selectbox("Unit (UOM):", unit_options, index=unit_options.index(item['Unit']) if item['Unit'] in unit_options else 0)
        with col_f2:
            if mode in ["internal", "damage", "recipe"]:
                o_sel = st.selectbox("Order Group:", list(order_options.keys()))
            else:
                st.text_input("Posting Date:", value=datetime.now().strftime('%d.%m.%Y'), disabled=True)
                
        st.write("")
        if st.button("💾 Save Item & Scan Next (Enter)", type="primary", use_container_width=True, key=f"save_btn_{st.session_state.barcode_key}") or qty_input > 0:
            if qty_input > 0:
                duplicate = False
                for idx, ex in enumerate(current_list):
                    if ex['SAP'] == item['SAP']:
                        current_list[idx]['Qty'] = str(float(ex['Qty']) + qty_input)
                        duplicate = True
                        break
                if not duplicate:
                    new_row = {
                        "SAP": item['SAP'], "Unit": u_sel, "Qty": str(qty_input),
                        "Plant": st.session_state.selected_plant, "Supplier_ID": item['Supplier_ID'], "Name": item['Name'], "Supplier": item['Supplier']
                    }
                    if mode in ["internal", "damage", "recipe"]: new_row["Order"] = order_options.get(o_sel)
                    current_list.append(new_row)
            
            st.session_state.active_item = None
            st.session_state.barcode_key += 1
            st.rerun()
    else:
        st.markdown("<p style='text-align:center; color:#777; padding:15px;'>System ready. Waiting for the next barcode scan...</p>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ==============================================================================
    # 📊 PREVIEW PANEL: Review, Edit, & Export to Excel/TXT
    # ==============================================================================
    if current_list:
        st.write("")
        show_preview = st.checkbox("👁️ Open Review Panel & Export Data (Excel / TXT)", value=False)
        
        if show_preview:
            st.markdown('<div class="group-box"><div class="group-title">📊 Total Scanned List Review</div>', unsafe_allow_html=True)
            st.write("✏️ **Modify quantities or delete items from the current session:**")
            
            updated_list = []
            for idx, entry in enumerate(current_list):
                col_i1, col_i2, col_i3, col_i4 = st.columns([3, 1.5, 1.5, 1])
                with col_i1:
                    st.markdown(f"<div style='padding-top:5px; font-size:13px;'><b>{entry['Name']}</b><br><small style='color:#666;'>SAP: {entry['SAP']} | Supplier: {entry.get('Supplier', '-')}</small></div>", unsafe_allow_html=True)
                with col_i2:
                    new_qty = st.number_input(f"Qty", min_value=0.001, value=float(entry['Qty']), step=0.001, format="%g", key=f"edit_qty_{idx}")
                    entry['Qty'] = str(new_qty)
                with col_i3:
                    st.markdown(f"<div style='padding-top:28px; text-align:center; font-weight:bold; color:#007acc;'>{entry['Unit']}</div>", unsafe_allow_html=True)
                with col_i4:
                    st.write("")
                    st.write("")
                    if st.button("❌", key=f"del_{idx}", help="Remove item"):
                        current_list.pop(idx)
                        setattr(st.session_state, f"scanned_{mode}", current_list)
                        st.rerun()
                updated_list.append(entry)
            
            setattr(st.session_state, f"scanned_{mode}", updated_list)
            st.divider()
            
            c_m1, c_m2, c_m3 = st.columns(3)
            with c_m1: st.markdown(f'<div class="metric-blue"><div class="metric-title">Unique Items</div><div class="metric-value">{len(current_list)}</div></div>', unsafe_allow_html=True)
            with c_m2: st.markdown(f'<div class="metric-green"><div class="metric-title">TOTAL ORDER</div><div class="metric-value">{len(current_list)}</div></div>', unsafe_allow_html=True)
            with c_m3:
                if mode == "purchase":
                    suppliers_count = len(set([i.get('Supplier_ID', '') for i in current_list if i.get('Supplier_ID')]))
                    st.markdown(f'<div class="metric-orange"><div class="metric-title">Suppliers Count</div><div class="metric-value">{suppliers_count}</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="metric-orange"><div class="metric-title">Suppliers Count</div><div class="metric-value">-</div></div>', unsafe_allow_html=True)
            
            st.write("")
            if st.button("🗑️ Clear Entire List & Reset Table", type="secondary", use_container_width=True):
                setattr(st.session_state, f"scanned_{mode}", [])
                st.session_state.active_item = None
                st.rerun()
                
            # SAP Structures Generation Mapping
            final_rows = []
            today = datetime.now()
            curr_idx = 0
            last_v = None
            
            for it in current_list:
                if mode == "internal":
                    final_rows.append({'SAP': it['SAP'], 'N1': '', 'N2': '', 'QUTY': it['Qty'], 'UNT': it['Unit'], 'LOC': '1000', 'COST CNTER': it['Plant'], 'ORDER': it.get('Order',''), 'N3': '', 'N4': '', 'N5': '', 'N6': '', 'N7': '', 'MOV TYP': 'ZX1', 'N9': '', 'N10': '', 'PLANT': it['Plant']})
                elif mode == "damage":
                    final_rows.append({'ITEM': it['SAP'], 'N1': '', 'N2': '', 'QUTY': it['Qty'], 'UON': it['Unit'], 'LOC': '1000', 'PLANT_MAIN': it['Plant'], 'ORDER': it.get('Order',''), 'N3': '', 'N4': '', 'N5': '', 'N6': '', 'N7': '', 'DAMAGE TYPE': 'Z51', 'N11': '', 'N12': '', 'PLANT': it['Plant']})
                elif mode == "recipe":
                    final_rows.append({'ITEM': it['SAP'], 'N1': '', 'N2': '', 'QUTY': it['Qty'], 'N3': '', 'LOC': '1000', 'N4': '', 'N5': '', 'N6': '', 'MOV': '317', 'N7': '', 'N8': '', 'PLANT': it['Plant']})
                elif mode == "purchase":
                    if it['Supplier_ID'] != last_v: curr_idx += 1; last_v = it['Supplier_ID']
                    try: p_grp_val = str(int(it['Plant']) - 1000) if int(it['Plant']) > 1000 else '104'
                    except: p_grp_val = '104'
                    final_rows.append({'Indicator': curr_idx, 'Doc Type': 'ZLPO', 'Vendor': it['Supplier_ID'], 'P.Org': '1100', 'P. Grp': p_grp_val, 'Company Code': '1000', 'Doc Date': today.strftime('%d.%m.%Y'), 'Material': it['SAP'], 'Quantity': it['Qty'], 'UOM': it['Unit'], 'Plant': it['Plant'], 'Storage Location': '1000', 'Delivery Date': (today + timedelta(days=2)).strftime('%d.%m.%Y'), 'Return': ''})
                    
            df_final = pd.DataFrame(final_rows)
            
            st.divider()
            
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                buffer_xlsx = io.BytesIO()
                with pd.ExcelWriter(buffer_xlsx, engine='openpyxl') as writer: df_final.to_excel(writer, index=False)
                st.download_button(label="🟢 Preview & Export List (Excel)", data=buffer_xlsx.getvalue(), file_name=f"AliSystem_{mode}_{today.strftime('%Y%m%d')}.xlsx", use_container_width=True)
            with col_dl2:
                buffer_txt = io.BytesIO()
                df_final.to_csv(buffer_txt, sep='\t', index=False)
                st.download_button(label="📥 Download TXT File for SAP", data=buffer_txt.getvalue(), file_name=f"AliSystem_{mode}_{today.strftime('%Y%m%d')}.txt", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("The scanned list is currently empty. No items added yet.")
