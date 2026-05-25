import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# إعدادات الصفحة لتناسب الهواتف
st.set_page_config(page_title="ALI SYSTEM PRO", page_icon="📦", layout="centered")

# تغيير التصميم العام ليصبح مريحاً على الهاتف (CSS مخصص)
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-size: 16px; }
    div[data-testid="metric-container"] { background-color: #f8f9fa; border: 1px solid #e0e0e0; padding: 10px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("📦 ALI SYSTEM PRO (Web Edition)")

# --- تهيئة الذاكرة المؤقتة للجلسة (Session State) ---
if "scanned_purchase" not in st.session_state: st.session_state.scanned_purchase = []
if "scanned_internal" not in st.session_state: st.session_state.scanned_internal = []
if "scanned_damage" not in st.session_state: st.session_state.scanned_damage = []
if "scanned_recipe" not in st.session_state: st.session_state.scanned_recipe = []
if "master_df" not in st.session_state: st.session_state.master_df = None
if "stock_df" not in st.session_state: st.session_state.stock_df = None
if "plants" not in st.session_state: st.session_state.plants = []

# --- قسم رفع الملفات ---
with st.sidebar:
    st.header("⚙️ إدارة ملفات النظام")
    master_file = st.file_uploader("1️⃣ ملف الباركودات (EXPORT BARCODE)", type=["xlsx", "xls", "csv"])
    stock_file = st.file_uploader("2️⃣ ملف المخزون (Stock Status)", type=["xlsx", "xls", "csv"])
    
    if master_file:
        try:
            df = pd.read_excel(master_file) if master_file.name.endswith('x') else pd.read_csv(master_file)
            st.session_state.master_df = df.astype(str).apply(lambda x: x.str.strip())
            st.success("✅ تم تحميل الباركودات")
        except Exception as e: st.error(f"خطأ في ملف الباركودات: {e}")
        
    if stock_file:
        try:
            df_s = pd.read_excel(stock_file, header=[0, 1], dtype=str) if stock_file.name.endswith('x') else pd.read_csv(stock_file, header=[0, 1], dtype=str)
            df_s.iloc[:, 0] = df_s.iloc[:, 0].str.strip().replace(r'\.0$', '', regex=True)
            st.session_state.stock_df = df_s
            st.session_state.plants = sorted(list(set([str(c[0]).strip() for c in df_s.columns if str(c[0]).strip().isdigit()])))
            st.success("✅ تم تحميل المخزون")
        except Exception as e: st.error(f"خطأ في ملف المخزون: {e}")

    if st.button("🗑️ مسح جميع القوائم الحالية", type="primary"):
        st.session_state.scanned_purchase = []
        st.session_state.scanned_internal = []
        st.session_state.scanned_damage = []
        st.session_state.scanned_recipe = []
        st.rerun()

# التحقق من رفع الملفات قبل بدء العمل
if st.session_state.master_df is None or st.session_state.stock_df is None:
    st.warning("⚠️ يرجى رفع ملف الباركودات وملف المخزون من القائمة الجانبية (Sidebar) للبدء.")
    st.stop()

# --- القوائم والخيارات الثابتة ---
unit_options = ["AU", "BAG", "BOX", "CAR", "G", "KG", "M", "ML", "PAC", "PC"]
order_options = {
    "500000 Customer Service": "500000", "500001 Fruit and vegetable": "500001",
    "500002 Deli section": "500002", "500003 General sections": "500003",
    "500004 Branch Office": "500004"
}

# --- واجهة التبويبات (Tabs) ---
current_tab = st.radio("اختر القسم الحالي للعمل:", ["Purchase Req", "Internal Sale", "Damage Issue", "Recipe Issue"], horizontal=True)
mode_map = {"Purchase Req": "purchase", "Internal Sale": "internal", "Damage Issue": "damage", "Recipe Issue": "recipe"}
mode = mode_map[current_tab]

# --- لوحة العدادات المباشرة (Dashboard) ---
current_list = getattr(st.session_state, f"scanned_{mode}")
col1, col2 = st.columns(2)
with col1: st.metric(label="عدد الأصناف المضافة", value=len(current_list))
with col2: 
    if mode == "purchase":
        st.metric(label="عدد الموردين", value=len(set([i.get('Supplier_ID', '') for i in current_list if i.get('Supplier_ID')])))
    else:
        st.metric(label="إجمالي الطلبات", value=len(current_list))

st.divider()

# --- الإعدادات الفورية ---
col_p, col_d = st.columns(2)
with col_p: plant_selected = st.selectbox("🏬 اختر الفرع (Plant):", st.session_state.plants)
with col_d: 
    date_val = datetime.now().strftime('%d.%m.%Y')
    if mode == "internal":
        date_input = st.text_input("📅 التاريخ:", value=date_val)

# طريقة إدخال البحث
modes_list = ["Barcode", "SAP", "Orion"]
if mode == "damage": modes_list.insert(0, "Short")
search_mode = st.radio("طريقة البحث:", modes_list, horizontal=True)

# صندوق إدخال الكود الفوري
search_input = st.text_input("🔍 امسح الباركود أو اكتب الكود هنا:", key="search_box")

# --- منطق البحث عند الكتابة ---
found_item = None
if search_input:
    val = search_input.strip()
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
        found_item = {
            "SAP": sap_code, "Name": str(row['Item Name']), "Supplier": str(row['Supplier Name']),
            "Factor": str(row['Factor']).split('.')[0], "Unit": str(row['UOM CODE']), "Supplier_ID": str(row['Supplier']).split('.')[0]
        }
        
        # جلب المخزون والمبيعات
        s_match = st.session_state.stock_df[st.session_state.stock_df.iloc[:, 0].astype(str).str.strip().replace(r'\.0$', '', regex=True) == sap_code]
        live_stock = "-"
        if not s_match.empty:
            p_col = [c for c in st.session_state.stock_df.columns if str(c[0]).strip() == plant_selected]
            if p_col: live_stock = str(s_match.iloc[0][p_col[0]]).split('.')[0]
            
            # عرض المبيعات السابقة كبطاقات صغيرة مريحة للهاتف
            st.markdown("### 📊 مبيعات الأشهر السابقة:")
            sales_cols = [c for c in st.session_state.stock_df.columns if "Total Sales" in str(c[0])]
            cols_sales = st.columns(len(sales_cols) if sales_cols else 1)
            for i, sc in enumerate(sales_cols):
                with cols_sales[i]:
                    try: st.metric(label=str(sc[1]).strip(), value=f"{float(s_match.iloc[0][sc]):g}")
                    except: pass
        
        # عرض بيانات الصنف الأساسية
        st.info(f"**Item:** {found_item['Name']} | **SAP:** {found_item['SAP']} | **Live Stock:** {live_stock}")
    else:
        st.error("❌ الصنف غير موجود، تحقق من طريقة البحث!")

# --- إدخال الكمية والحفظ ---
if found_item:
    unit_selected = st.selectbox("📦 الوحدة (Unit):", unit_options, index=unit_options.index(found_item['Unit']) if found_item['Unit'] in unit_options else 0)
    qty_input = st.number_input("🔢 الكمية المطلوبة:", min_value=0.0, step=1.0, format="%g", key="qty_box")
    
    order_selected = None
    if mode in ["internal", "damage", "recipe"]:
        order_key = st.selectbox("🎯 اختر الـ Order Group:", list(order_options.keys()))
        order_selected = order_options[order_key]
        
    if st.button("➕ حفظ الصنف إلى القائمة"):
        if qty_input > 0:
            # التحقق من التكرار والدمج تلقائياً
            duplicate = False
            for idx, ex in enumerate(current_list):
                if ex['SAP'] == found_item['SAP']:
                    current_list[idx]['Qty'] = str(float(ex['Qty']) + qty_input)
                    duplicate = True
                    st.success("🔄 تم العثور على الصنف مسبقاً، وتم دمج الكمية بنجاح!")
                    break
            
            if not duplicate:
                new_row = {
                    "SAP": found_item['SAP'], "Unit": unit_selected, "Qty": str(qty_input),
                    "Plant": plant_selected, "Supplier_ID": found_item['Supplier_ID'], "Name": found_item['Name']
                }
                if order_selected: new_row["Order"] = order_selected
                if mode == "internal": new_row["Date"] = date_input
                current_list.append(new_row)
                st.success(f"✅ تم إضافة {found_item['Name']} بنجاح!")
            
            st.rerun()

st.divider()

# --- قسم استعراض القائمة الحالية والتصدير (Preview & Export) ---
st.subheader(f"📋 معاينة قائمة ({current_tab})")
if current_list:
    df_preview = pd.DataFrame(current_list)
    st.dataframe(df_preview, use_container_width=True)
    
    # بناء ملف التصدير النهائي حسب الهيكلية الصارمة الخاصة بك بنظام SAP
    final_rows = []
    today = datetime.now()
    curr_idx = 0
    last_v = None
    
    for it in current_list:
        if mode == "internal":
            final_rows.append({
                'SAP': it['SAP'], 'N1': '', 'N2': '', 'QUTY': it['Qty'], 'UNT': it['Unit'], 'LOC': '1000', 
                'COST CNTER': it['Plant'], 'ORDER': it['Order'], 'N3': '', 'N4': '', 'N5': '', 'N6': '', 
                'N7': '', 'MOV TYP': 'ZX1', 'N9': '', 'N10': '', 'PLANT': it['Plant']
            })
        elif mode == "damage":
            final_rows.append({
                'ITEM': it['SAP'], 'N1': '', 'N2': '', 'QUTY': it['Qty'], 'UON': it['Unit'], 'LOC': '1000', 
                'PLANT_MAIN': it['Plant'], 'ORDER': it['Order'], 'N3': '', 'N4': '', 'N5': '', 'N6': '', 
                'N7': '', 'DAMAGE TYPE': 'Z51', 'N11': '', 'N12': '', 'PLANT': it['Plant']
            })
        elif mode == "recipe":
            final_rows.append({
                'ITEM': it['SAP'], 'N1': '', 'N2': '', 'QUTY': it['Qty'], 'N3': '', 'LOC': '1000', 
                'N4': '', 'N5': '', 'N6': '', 'MOV': '317', 'N7': '', 'N8': '', 'PLANT': it['Plant']
            })
        elif mode == "purchase":
            if it['Supplier_ID'] != last_v:
                curr_idx += 1
                last_v = it['Supplier_ID']
            try:
                plant_num = int(it['Plant'])
                p_grp_val = str(plant_num - 1000) if plant_num > 1000 else '104'
            except: p_grp_val = '104'
            
            final_rows.append({
                'Indicator': curr_idx, 'Doc Type': 'ZLPO', 'Vendor': it['Supplier_ID'], 'P.Org': '1100', 
                'P. Grp': p_grp_val, 'Company Code': '1000', 'Doc Date': today.strftime('%d.%m.%Y'), 
                'Material': it['SAP'], 'Quantity': it['Qty'], 'UOM': it['Unit'], 'Plant': it['Plant'], 
                'Storage Location': '1000', 'Delivery Date': (today + timedelta(days=2)).strftime('%d.%m.%Y'), 'Return': ''
            })
            
    df_final = pd.DataFrame(final_rows)
    
    # تحويل الملف المجهز إلى سيل بايتات للتنزيل الفوري عبر المتصفح
    # Excel Export
    buffer_xlsx = io.BytesIO()
    with pd.ExcelWriter(buffer_xlsx, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 تحميل كملف Excel للهاتف",
        data=buffer_xlsx.getvalue(),
        file_name=f"AliSystem_{mode}_{today.strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # TXT Export
    buffer_txt = io.BytesIO()
    df_final.to_csv(buffer_txt, sep='\t', index=False)
    
    st.download_button(
        label="📥 تحميل كملف TXT للهاتف",
        data=buffer_txt.getvalue(),
        file_name=f"AliSystem_{mode}_{today.strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )
else:
    st.info("القائمة الحالية فارغة. ابحث عن صنف لتبدأ التعبئة.")
