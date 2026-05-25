import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# إعدادات الصفحة لتناسب جميع الشاشات
st.set_page_config(page_title="ALI SYSTEM PRO", page_icon="📦", layout="centered")

# دمج الأنماط وتصغير الفراغات الرأسية لجعل الواجهة مضغوطة وعملية جداً
st.markdown("""
    <style>
    /* تقليل الفراغات العلوية والسفلية في الصفحة */
    .main .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 800px; }
    h1 { text-align: center; color: #1E3A8A; font-size: 24px !important; margin-bottom: 5px !important; padding-bottom: 0px !important; }
    .stRadio > div { margin-bottom: 0px !important; padding: 0px !important; }
    .stDivider { margin-top: 10px !important; margin-bottom: 10px !important; }
    
    /* لوحة بيانات الصنف المدمجة والمريحة للعين */
    .item-box {
        background-color: #f0f7ff;
        border: 1px solid #bae6fd;
        border-radius: 8px;
        padding: 12px;
        margin-top: 5px;
        margin-bottom: 10px;
    }
    .item-title { color: #0369a1; font-size: 15px; font-weight: bold; margin-bottom: 6px; }
    .item-details { color: #1e293b; font-size: 13px; font-weight: 500; }
    
    /* تنسيق بطاقات المبيعات المصغرة */
    div[data-testid="stMetricValue"] { font-size: 16px !important; font-weight: bold !important; color: #0284c7 !important; }
    div[data-testid="stMetricLabel"] { font-size: 12px !important; color: #475569 !important; }
    div[data-testid="metric-container"] { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 4px 8px; border-radius: 6px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("📦 ALI SYSTEM PRO")

# --- دالات القراءة السريعة المحفوظة في الذاكرة (Caching) ---
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

# --- تهيئة الذاكرة المؤقتة للجلسة (Session State) ---
if "scanned_purchase" not in st.session_state: st.session_state.scanned_purchase = []
if "scanned_internal" not in st.session_state: st.session_state.scanned_internal = []
if "scanned_damage" not in st.session_state: st.session_state.scanned_damage = []
if "scanned_recipe" not in st.session_state: st.session_state.scanned_recipe = []
if "master_df" not in st.session_state: st.session_state.master_df = None
if "stock_df" not in st.session_state: st.session_state.stock_df = None
if "plants" not in st.session_state: st.session_state.plants = []

if "search_input_val" not in st.session_state: st.session_state.search_input_val = ""
if "qty_input_val" not in st.session_state: st.session_state.qty_input_val = "1"
if "active_item" not in st.session_state: st.session_state.active_item = None

# --- القائمة الجانبية (إدارة الملفات) ---
with st.sidebar:
    st.header("⚙️ ملفات النظام")
    master_file = st.file_uploader("1️⃣ ملف الباركودات", type=["xlsx", "xls", "csv"])
    stock_file = st.file_uploader("2️⃣ ملف المخزون", type=["xlsx", "xls", "csv"])
    
    if master_file:
        try: st.session_state.master_df = load_master_file(master_file); st.success("✅ تم تحميل الباركودات")
        except Exception as e: st.error(f"خطأ: {e}")
        
    if stock_file:
        try: st.session_state.stock_df, st.session_state.plants = load_stock_file(stock_file); st.success("✅ تم تحميل المخزون")
        except Exception as e: st.error(f"خطأ: {e}")

    if st.button("🗑️ مسح جميع القوائم الحالية", type="primary"):
        st.session_state.scanned_purchase = []
        st.session_state.scanned_internal = []
        st.session_state.scanned_damage = []
        st.session_state.scanned_recipe = []
        st.session_state.search_input_val = ""
        st.session_state.active_item = None
        st.rerun()

# حماية النظام
if st.session_state.master_df is None or st.session_state.stock_df is None:
    st.warning("⚠️ يرجى رفع الملفات من القائمة الجانبية للبدء.")
    st.stop()

unit_options = ["AU", "BAG", "BOX", "CAR", "G", "KG", "M", "ML", "PAC", "PC"]
order_options = {
    "500000 Customer Service": "500000", "500001 Fruit and vegetable": "500001",
    "500002 Deli section": "500002", "500003 General sections": "500003",
    "500004 Branch Office": "500004"
}

# أقسام العمل والخيارات الأساسية في أسطر مضغوطة
current_tab = st.radio("القسم الحالي:", ["Purchase Req", "Internal Sale", "Damage Issue", "Recipe Issue"], horizontal=True)
mode = {"Purchase Req": "purchase", "Internal Sale": "internal", "Damage Issue": "damage", "Recipe Issue": "recipe"}[current_tab]
current_list = getattr(st.session_state, f"scanned_{mode}")

col_p, col_d = st.columns(2)
with col_p: plant_selected = st.selectbox("🏬 الفرع (Plant):", st.session_state.plants)
with col_d: 
    if mode == "internal": date_input = st.text_input("📅 التاريخ:", value=datetime.now().strftime('%d.%m.%Y'))
    else: st.text_input("📝 حالة القائمة:", value=f"الأصناف الحالية: {len(current_list)}", disabled=True)

modes_list = ["Barcode", "SAP", "Orion"]
if mode == "damage": modes_list.insert(0, "Short")
search_mode = st.radio("طريقة البحث:", modes_list, horizontal=True)

# --- دالات معالجة الإدخال السريع ---
def handle_barcode_entry():
    val = st.session_state.barcode_field.strip()
    if not val: return
    if search_mode == "Short" and len(val) >= 6: val = val[2:6]
    
    sap_code = None
    if search_mode == "Orion":
        col = next((c for c in st.session_state.stock_df.columns if 'Orion Item Code' in str(c).strip()), None)
        if col:
            m_stock = st.session_state.stock_df[st.session_state.stock_df[col].astype(str).str.strip().replace(r'\.0$', '', regex=True) == val]
            if not m_stock.empty: sap_code = str(m_stock.iloc[0, 0]).strip().replace('.0', '')
    else:
        s_col = 'Item Barcode' if search_mode in ["Short", "Barcode"] else 'Item Code'
        m_temp = st.session_state.master_df.copy()
        act_col = next((c for c in m_temp.columns if s_col.lower() in str(c).lower()), s_col)
        m_temp[act_col] = m_temp[act_col].astype(str).str.strip().replace(r'\.0$', '', regex=True)
        m_master = m_temp[m_temp[act_col] == val]
        if not m_master.empty: sap_code = str(m_master.iloc[0]['Item Code']).strip().replace('.0', '')

    if sap_code:
        row = st.session_state.master_df[st.session_state.master_df['Item Code'].astype(str).str.strip().replace(r'\.0$', '', regex=True) == sap_code].iloc[0]
        st.session_state.active_item = {
            "SAP": sap_code, "Name": str(row['Item Name']), "Supplier": str(row['Supplier Name']),
            "Factor": str(row['Factor']).split('.')[0], "Unit": str(row['UOM CODE']), "Supplier_ID": str(row['Supplier']).split('.')[0]
        }
    else:
        st.session_state.active_item = None

def handle_quantity_entry():
    if not st.session_state.active_item: return
    try: qty_input = float(st.session_state.qty_field.strip())
    except ValueError: qty_input = 0.0
        
    if qty_input > 0:
        duplicate = False
        for idx, ex in enumerate(current_list):
            if ex['SAP'] == st.session_state.active_item['SAP']:
                current_list[idx]['Qty'] = str(float(ex['Qty']) + qty_input)
                duplicate = True
                break
        if not duplicate:
            new_row = {
                "SAP": st.session_state.active_item['SAP'], "Unit": st.session_state.get('unit_field', st.session_state.active_item['Unit']), 
                "Qty": str(qty_input), "Plant": plant_selected, "Supplier_ID": st.session_state.active_item['Supplier_ID'], "Name": st.session_state.active_item['Name']
            }
            if mode in ["internal", "damage", "recipe"]: new_row["Order"] = order_options.get(st.session_state.get('order_field', ''))
            if mode == "internal": new_row["Date"] = date_input
            current_list.append(new_row)
            
        st.session_state.active_item = None
        st.session_state.search_input_val = ""

# حقل إدخال الكود الأساسي
st.text_input("🔍 امسح الباركود أو اكتب الكود هنا واضغط Enter:", key="barcode_field", on_change=handle_barcode_entry)

# --- عرض بيانات الصنف والتحكم المدمج ---
if st.session_state.active_item:
    item = st.session_state.active_item
    s_match = st.session_state.stock_df[st.session_state.stock_df.iloc[:, 0].astype(str).str.strip().replace(r'\.0$', '', regex=True) == item['SAP']]
    
    live_stock = "0"
    if not s_match.empty:
        p_col = [c for c in st.session_state.stock_df.columns if str(c[0]).strip() == plant_selected]
        if p_col: live_stock = str(s_match.iloc[0][p_col[0]]).split('.')[0]
    
    # 🌟 تصميم مدمج وممتاز يظهر الاسم بالكامل بدون أي قطع
    st.markdown(f"""
    <div class="item-box">
        <div class="item-title">📋 {item['Name']}</div>
        <div class="item-details">🔢 <b>كود بيب (SAP):</b> {item['SAP']} &nbsp;|&nbsp; 🏢 <b>المخزون الحالي للفرع:</b> {live_stock}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # صف أفقي مدمج للمبيعات السابقة (المنسدلة والنتيجة في نفس السطر لضغط المساحة)
    if not s_match.empty:
        sales_cols = [c for c in st.session_state.stock_df.columns if "Total Sales" in str(c[0])]
        if sales_cols:
            month_map = {str(sc[1]).strip(): sc for sc in sales_cols}
            c_sales_1, c_sales_2 = st.columns([2, 1])
            with c_sales_1:
                selected_month_name = st.selectbox("📊 اختر الشهر لاستعراض المبيعات:", list(month_map.keys()), label_visibility="collapsed")
            with c_sales_2:
                chosen_col = month_map[selected_month_name]
                try: sales_value = f"{float(s_match.iloc[0][chosen_col]):g}"
                except: sales_value = "0"
                st.metric(label=f"مبيعات {selected_month_name}", value=sales_value)

    # صف أفقي مدمج لإدخال البيانات وحفظها بسرعة بالـ Enter
    st.markdown("<p style='font-size:13px; font-weight:bold; margin-bottom:2px;'>📥 تفاصيل التعبئة والحفظ:</p>", unsafe_allow_html=True)
    
    if mode in ["internal", "damage", "recipe"]:
        c_input1, c_input2, c_input3 = st.columns([1, 1.5, 1])
        with c_input1: st.selectbox("الوحدة:", unit_options, index=unit_options.index(item['Unit']) if item['Unit'] in unit_options else 0, key="unit_field")
        with c_input2: st.selectbox("الـ Order Group:", list(order_options.keys()), key="order_field")
        with c_input3: st.text_input("الكمية:", value="1", key="qty_field", on_change=handle_quantity_entry)
    else:
        c_input1, c_input2 = st.columns([1, 1])
        with c_input1: st.selectbox("الوحدة:", unit_options, index=unit_options.index(item['Unit']) if item['Unit'] in unit_options else 0, key="unit_field")
        with c_input2: st.text_input("الكمية واضغط Enter:", value="1", key="qty_field", on_change=handle_quantity_entry)

st.divider()

# --- لوحة استعراض الجدول والتصدير ---
if current_list:
    st.subheader(f"📋 معاينة قائمة ({current_tab})")
    df_preview = pd.DataFrame(current_list)
    st.dataframe(df_preview[['Name', 'SAP', 'Qty', 'Unit']], use_container_width=True)
    
    col_edit_item, col_edit_qty, col_btn_act = st.columns([2, 1, 1])
    with col_edit_item: item_to_modify = st.selectbox("تعديل صنف:", [i['Name'] for i in current_list])
    with col_edit_qty: new_qty_val = st.number_input("كمية جديدة:", min_value=0.0, step=1.0, format="%g")
    with col_btn_act:
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            if st.button("📝"):
                for idx, item in enumerate(current_list):
                    if item['Name'] == item_to_modify: current_list[idx]['Qty'] = str(new_qty_val); st.rerun()
        with c_b2:
            if st.button("🗑️"):
                for idx, item in enumerate(current_list):
                    if item['Name'] == item_to_modify: current_list.pop(idx); st.rerun()

    final_rows = []
    today = datetime.now()
    curr_idx = 0
    last_v = None
    
    for it in current_list:
        if mode == "internal":
            final_rows.append({'SAP': it['SAP'], 'N1': '', 'N2': '', 'QUTY': it['Qty'], 'UNT': it['Unit'], 'LOC': '1000', 'COST CNTER': it['Plant'], 'ORDER': it['Order'], 'N3': '', 'N4': '', 'N5': '', 'N6': '', 'N7': '', 'MOV TYP': 'ZX1', 'N9': '', 'N10': '', 'PLANT': it['Plant']})
        elif mode == "damage":
            final_rows.append({'ITEM': it['SAP'], 'N1': '', 'N2': '', 'QUTY': it['Qty'], 'UON': it['Unit'], 'LOC': '1000', 'PLANT_MAIN': it['Plant'], 'ORDER': it['Order'], 'N3': '', 'N4': '', 'N5': '', 'N6': '', 'N7': '', 'DAMAGE TYPE': 'Z51', 'N11': '', 'N12': '', 'PLANT': it['Plant']})
        elif mode == "recipe":
            final_rows.append({'ITEM': it['SAP'], 'N1': '', 'N2': '', 'QUTY': it['Qty'], 'N3': '', 'LOC': '1000', 'N4': '', 'N5': '', 'N6': '', 'MOV': '317', 'N7': '', 'N8': '', 'PLANT': it['Plant']})
        elif mode == "purchase":
            if it['Supplier_ID'] != last_v: curr_idx += 1; last_v = it['Supplier_ID']
            try: p_grp_val = str(int(it['Plant']) - 1000) if int(it['Plant']) > 1000 else '104'
            except: p_grp_val = '104'
            final_rows.append({'Indicator': curr_idx, 'Doc Type': 'ZLPO', 'Vendor': it['Supplier_ID'], 'P.Org': '1100', 'P. Grp': p_grp_val, 'Company Code': '1000', 'Doc Date': today.strftime('%d.%m.%Y'), 'Material': it['SAP'], 'Quantity': it['Qty'], 'UOM': it['Unit'], 'Plant': it['Plant'], 'Storage Location': '1000', 'Delivery Date': (today + timedelta(days=2)).strftime('%d.%m.%Y'), 'Return': ''})
            
    df_final = pd.DataFrame(final_rows)
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        buffer_xlsx = io.BytesIO()
        with pd.ExcelWriter(buffer_xlsx, engine='openpyxl') as writer: df_final.to_excel(writer, index=False)
        st.download_button(label="📥 تحميل Excel لـ SAP", data=buffer_xlsx.getvalue(), file_name=f"AliSystem_{mode}_{today.strftime('%Y%m%d')}.xlsx")
    with col_dl2:
        buffer_txt = io.BytesIO()
        df_final.to_csv(buffer_txt, sep='\t', index=False)
        st.download_button(label="📥 تحميل TXT لـ SAP", data=buffer_txt.getvalue(), file_name=f"AliSystem_{mode}_{today.strftime('%Y%m%d')}.txt")
else:
    st.info("القائمة فارغة وبانتظار مسح الأصناف.")
