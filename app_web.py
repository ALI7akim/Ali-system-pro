import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# إعدادات الصفحة لتناسب جميع الشاشات
st.set_page_config(page_title="ALI SYSTEM PRO", page_icon="📦", layout="centered")

# تصميم مخصص مريح جداً وتصغير خط المبيعات والأزرار
st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    h1 { text-align: center; color: #1E3A8A; font-size: 26px !important; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    
    /* تصغير خط وحجم بطاقات مبيعات الأشهر السابقة */
    div[data-testid="stMetricValue"] { font-size: 16px !important; font-weight: bold !important; }
    div[data-testid="stMetricLabel"] { font-size: 11px !important; color: #555555 !important; }
    div[data-testid="metric-container"] { background-color: #f8f9fa; border: 1px solid #e2e8f0; padding: 6px 10px; border-radius: 6px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("📦 ALI SYSTEM PRO (Ultimate Web)")

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

# تهيئة المفاتيح الخاصة بالتحكم في تفريغ الحقول وإعادة الفوكس تلقائياً للباركود
if "barcode_input_value" not in st.session_state: st.session_state.barcode_input_value = ""

# --- إدارة رفع الملفات عبر القائمة الجانبية ---
with st.sidebar:
    st.header("⚙️ إدارة ملفات النظام")
    master_file = st.file_uploader("1️⃣ ملف الباركودات (EXPORT BARCODE)", type=["xlsx", "xls", "csv"])
    stock_file = st.file_uploader("2️⃣ ملف المخزون (Stock Status)", type=["xlsx", "xls", "csv"])
    
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
        st.session_state.barcode_input_value = ""
        st.rerun()

# حماية النظام من العمل دون ملفات
if st.session_state.master_df is None or st.session_state.stock_df is None:
    st.warning("⚠️ يرجى رفع ملف الباركودات وملف المخزون من القائمة الجانبية للبدء.")
    st.stop()

# --- القوائم والخيارات الثابتة ---
unit_options = ["AU", "BAG", "BOX", "CAR", "G", "KG", "M", "ML", "PAC", "PC"]
order_options = {
    "500000 Customer Service": "500000", "500001 Fruit and vegetable": "500001",
    "500002 Deli section": "500002", "500003 General sections": "500003",
    "500004 Branch Office": "500004"
}

# --- أقسام العمل (Tabs) ---
current_tab = st.radio("اختر القسم الحالي للعمل:", ["Purchase Req", "Internal Sale", "Damage Issue", "Recipe Issue"], horizontal=True)
mode_map = {"Purchase Req": "purchase", "Internal Sale": "internal", "Damage Issue": "damage", "Recipe Issue": "recipe"}
mode = mode_map[current_tab]

# --- لوحة العدادات (Dashboard) ---
current_list = getattr(st.session_state, f"scanned_{mode}")
col1, col2 = st.columns(2)
with col1: st.metric(label="عدد الأصناف المضافة", value=len(current_list))
with col2: 
    if mode == "purchase": st.metric(label="عدد الموردين", value=len(set([i.get('Supplier_ID', '') for i in current_list if i.get('Supplier_ID')])))
    else: st.metric(label="إجمالي الطلبات", value=len(current_list))

st.divider()

# --- الإعدادات الفورية ---
col_p, col_d = st.columns(2)
with col_p: plant_selected = st.selectbox("🏬 اختر الفرع (Plant):", st.session_state.plants)
with col_d: 
    date_val = datetime.now().strftime('%d.%m.%Y')
    if mode == "internal": date_input = st.text_input("📅 التاريخ:", value=date_val)

# اختيار طريقة البحث
modes_list = ["Barcode", "SAP", "Orion"]
if mode == "damage": modes_list.insert(0, "Short")
search_mode = st.radio("طريقة البحث:", modes_list, horizontal=True)

# دالة التعامل مع تغيير إدخال الباركود
def handle_barcode_change():
    st.session_state.barcode_input_value = st.session_state.search_field

# حقل إدخال الباركود المباشر
search_input = st.text_input("🔍 امسح الباركود أو اكتب الكود هنا:", key="search_field", on_change=handle_barcode_change)

# الاستعانة بالقيمة المستقرة داخل السيشن
current_barcode = st.session_state.barcode_input_value.strip()

# --- منطق البحث الجذري ---
found_item = None
if current_barcode:
    val = current_barcode
    if search_mode == "Short" and len(val) >= 6: val = val[2:6]
    
    sap_code = None
    if search_mode == "Orion":
        col = next((c for c in st.session_state.stock_df.columns if 'Orion Item Code' in str(c).strip()), None)
        if col:
            m_stock = st.session_state.stock_df[st.session_state.stock_df[col].astype(str).str.strip().replace(r'\.0$', '', regex=True) == val]
            if not m_stock.empty: sap_code = str(m_stock.iloc[0, 0]).strip().replace('.0', '')
    else:
        s_col = 'Item Barcode' if search_mode in ["Short", "Barcode"] else 'Item Code'
        m_temp = m_temp = st.session_state.master_df.copy()
        act_col = next((c for c in m_temp.columns if s_col.lower() in str(c).lower()), s_col)
        m_temp[act_col] = m_temp[act_col].astype(str).str.strip().replace(r'\.0$', '', regex=True)
        m_master = m_temp[m_temp[act_col] == val]
        if not m_master.empty: sap_code = str(m_master.iloc[0]['Item Code']).strip().replace('.0', '')

    if sap_code:
        row = st.session_state.master_df[st.session_state.master_df['Item Code'].astype(str).str.strip().replace(r'\.0$', '', regex=True) == sap_code].iloc[0]
        found_item = {
            "SAP": sap_code, "Name": str(row['Item Name']), "Supplier": str(row['Supplier Name']),
            "Factor": str(row['Factor']).split('.')[0], "Unit": str(row['UOM CODE']), "Supplier_ID": str(row['Supplier']).split('.')[0]
        }
        
        # جلب المخزون والمبيعات السابقة
        s_match = st.session_state.stock_df[st.session_state.stock_df.iloc[:, 0].astype(str).str.strip().replace(r'\.0$', '', regex=True) == sap_code]
        live_stock = "-"
        if not s_match.empty:
            p_col = [c for c in st.session_state.stock_df.columns if str(c[0]).strip() == plant_selected]
            if p_col: live_stock = str(s_match.iloc[0][p_col[0]]).split('.')[0]
            
            # قسم المبيعات السابقة بحجم الخط المصغر
            st.markdown("<p style='font-size:13px; font-weight:bold; margin-bottom:5px;'>📊 مبيعات الأشهر السابقة:</p>", unsafe_allow_html=True)
            sales_cols = [c for c in st.session_state.stock_df.columns if "Total Sales" in str(c[0])]
            cols_sales = st.columns(len(sales_cols) if sales_cols else 1)
            for i, sc in enumerate(sales_cols):
                with cols_sales[i]:
                    try: st.metric(label=str(sc[1]).strip(), value=f"{float(s_match.iloc[0][sc]):g}")
                    except: pass
        
        st.info(f"**الصنف المختار:** {found_item['Name']} | **SAP:** {found_item['SAP']} | **المخزون الحالي:** {live_stock}")
    else:
        st.error("❌ الصنف غير موجود، تحقق من طريقة البحث!")

# --- نموذج حفظ الكمية الصارم والخالي من المشاكل ---
if found_item:
    with st.form(key="final_qty_form", clear_on_submit=True):
        unit_selected = st.selectbox("📦 الوحدة (Unit):", unit_options, index=unit_options.index(found_item['Unit']) if found_item['Unit'] in unit_options else 0)
        
        qty_input_raw = st.text_input("🔢 اكتب الكمية واضغط Enter للحفظ المباشر:", value="1")
        
        order_selected = None
        if mode in ["internal", "damage", "recipe"]:
            order_key = st.selectbox("🎯 اختر الـ Order Group:", list(order_options.keys()))
            order_selected = order_options[order_key]
            
        submit_qty = st.form_submit_button("➕ حفظ الصنف إلى القائمة")
        
        if submit_qty:
            try: qty_input = float(qty_input_raw.strip())
            except ValueError: qty_input = 0.0
                
            if qty_input > 0:
                duplicate = False
                for idx, ex in enumerate(current_list):
                    if ex['SAP'] == found_item['SAP']:
                        current_list[idx]['Qty'] = str(float(ex['Qty']) + qty_input)
                        duplicate = True
                        break
                
                if not duplicate:
                    new_row = {
                        "SAP": found_item['SAP'], "Unit": unit_selected, "Qty": str(qty_input),
                        "Plant": plant_selected, "Supplier_ID": found_item['Supplier_ID'], "Name": found_item['Name']
                    }
                    if order_selected: new_row["Order"] = order_selected
                    if mode == "internal": new_row["Date"] = date_input
                    current_list.append(new_row)
                
                # تصفير المدخلات في الـ session لإخفاء النموذج فوراً وإجبار المتصفح على التركيز على الباركود
                st.session_state.barcode_input_value = ""
                st.session_state.search_field = ""
                st.success("✅ تم حفظ الصنف بنجاح!")
                st.rerun()

st.divider()

# --- لوحة استعراض الجدول والتعديل والحذف 🗑️ ---
st.subheader(f"📋 معاينة وتعديل قائمة ({current_tab})")
if current_list:
    df_preview = pd.DataFrame(current_list)
    st.dataframe(df_preview[['Name', 'SAP', 'Qty', 'Unit']], use_container_width=True)
    
    st.markdown("### 🛠️ لوحة التحكم في الأصناف المضافة:")
    col_edit_item, col_edit_qty, col_edit_btn, col_del_btn = st.columns([3, 2, 2, 2])
    
    with col_edit_item:
        item_to_modify = st.selectbox("اختر الصنف للتعديل/الحذف:", [i['Name'] for i in current_list])
    with col_edit_qty:
        new_qty_val = st.number_input("الكمية الجديدة:", min_value=0.0, step=1.0, format="%g")
