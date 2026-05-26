import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import os

# إعدادات الشاشة والمظهر
st.set_page_config(page_title="ALI SYSTEM PRO", page_icon="📦", layout="centered")

# مسارات حفظ الملفات الخام على السيرفر
MASTER_FILE_PATH = "master_db.xlsx"
STOCK_FILE_PATH = "stock_db.xlsx"

# تطبيق نمط وألوان برنامج الكمبيوتر الكلاسيكي المريح للعين
st.markdown("""
    <style>
    .main { background-color: #f0f0f0 !important; }
    .main .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 850px; }
    
    .metric-blue { background-color: #007acc; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #005999; }
    .metric-green { background-color: #2ea44f; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #227d3c; }
    .metric-orange { background-color: #f37023; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #d05616; }
    .metric-title { font-size: 13px; margin-bottom: 2px; }
    .metric-value { font-size: 20px; font-weight: bold; }
    
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

# --- دالات قراءة البيانات المحسنة لعدم البطء ---
@st.cache_data
def load_processed_master(file_path):
    if not os.path.exists(file_path): return None
    try:
        df = pd.read_excel(file_path)
        return df.astype(str).apply(lambda x: x.str.strip())
    except: return None

@st.cache_data
def load_processed_stock(file_path):
    if not os.path.exists(file_path): return None, []
    try:
        df_s = pd.read_excel(file_path, header=[0, 1], dtype=str)
        df_s.iloc[:, 0] = df_s.iloc[:, 0].str.strip().replace(r'\.0$', '', regex=True)
        plants = sorted(list(set([str(c[0]).strip() for c in df_s.columns if str(c[0]).strip().isdigit()])))
        return df_s, plants
    except: return None, []

# جلب قاعدة البيانات الحالية
saved_m = load_processed_master(MASTER_FILE_PATH)
saved_s, saved_p = load_processed_stock(STOCK_FILE_PATH)

# --- تهيئة متغيرات الجلسة الدائمة ---
for key in ["scanned_purchase", "scanned_internal", "scanned_damage", "scanned_recipe"]:
    if key not in st.session_state: st.session_state[key] = []

if "master_df" not in st.session_state: st.session_state.master_df = saved_m
if "stock_df" not in st.session_state: st.session_state.stock_df = saved_s
if "plants" not in st.session_state: st.session_state.plants = saved_p

if "app_page" not in st.session_state: st.session_state.app_page = "setup"
if "selected_plant" not in st.session_state: st.session_state.selected_plant = ""
if "selected_tab" not in st.session_state: st.session_state.selected_tab = "Purchase Req"

# متغيرات تحكم البحث لمنع الفقدان التلقائي أثناء الكتابة
if "search_barcode_value" not in st.session_state: st.session_state.search_barcode_value = ""

# --- القائمة الجانبية المخصصة لإدارة وتحديث الملفات ---
with st.sidebar:
    st.header("⚙️ إدارة وتحديث الملفات المحفوظة")
    st.markdown("### 📊 الحالة الحالية للملفات:")
    if st.session_state.master_df is not None: st.success("📁 ملف الباركودات: جاهز")
    else: st.error("❌ ملف الباركودات: غير متوفر")
    if st.session_state.stock_df is not None: st.success("📁 ملف المخزون: جاهز")
    else: st.error("❌ ملف المخزون: غير متوفر")
    
    st.divider()
    new_master = st.file_uploader("تحديث ملف الباركودات (Excel)", type=["xlsx"])
    if new_master:
        with open(MASTER_FILE_PATH, "wb") as f: f.write(new_master.getbuffer())
        st.cache_data.clear()
        st.session_state.master_df = load_processed_master(MASTER_FILE_PATH)
        st.success("✅ تم تحديث قاعدة الباركودات!")
        st.rerun()
            
    new_stock = st.file_uploader("تحديث ملف المخزون (Excel)", type=["xlsx"])
    if new_stock:
        with open(STOCK_FILE_PATH, "wb") as f: f.write(new_stock.getbuffer())
        st.cache_data.clear()
        st.session_state.stock_df, st.session_state.plants = load_processed_stock(STOCK_FILE_PATH)
        st.success("✅ تم تحديث قاعدة المخزون والمبيعات!")
        st.rerun()

if st.session_state.master_df is None or st.session_state.stock_df is None:
    st.warning("⚠️ يرجى رفع ملف الباركودات وملف المخزون من القائمة الجانبية للبدء.")
    st.stop()

unit_options = ["AU", "BAG", "BOX", "CAR", "G", "KG", "M", "ML", "PAC", "PC"]
order_options = {
    "500000 Customer Service": "500000", "500001 Fruit and vegetable": "500001",
    "500002 Deli section": "500002", "500003 General sections": "500003",
    "500004 Branch Office": "500004"
}

# ==============================================================================
# 🚪 خطوة 1: شاشة تحديد الفرع والقسم
# ==============================================================================
if st.session_state.app_page == "setup":
    st.markdown('<div class="group-box"><div class="group-title">🏢 خطوة 1: تحديد وجهة العمل والفرع</div>', unsafe_allow_html=True)
    plant_idx = st.session_state.plants.index(st.session_state.selected_plant) if st.session_state.selected_plant in st.session_state.plants else 0
    plant_selected = st.selectbox("🏬 اختر الفرع الحالي (Plant) الذي ستعمل عليه:", st.session_state.plants, index=plant_idx)
    
    tab_list = ["Purchase Req", "Internal Sale", "Damage Issue", "Recipe Issue"]
    tab_idx = tab_list.index(st.session_state.selected_tab) if st.session_state.selected_tab in tab_list else 0
    tab_selected = st.radio("📂 اختر قسم العمل الحالي:", tab_list, index=tab_idx, horizontal=True)
    
    if st.button("🚀 الدخول لصفحة مسح الأصناف والباركود 📥", type="primary", use_container_width=True):
        st.session_state.selected_plant = plant_selected
        st.session_state.selected_tab = tab_selected
        st.session_state.app_page = "scan"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 🔍 خطوة 2: الشاشة المصلحة (البحث الفوري أولاً وعرض المخزون والمبيعات كاملاً)
# ==============================================================================
elif st.session_state.app_page == "scan":
    mode = {"Purchase Req": "purchase", "Internal Sale": "internal", "Damage Issue": "damage", "Recipe Issue": "recipe"}[st.session_state.selected_tab]
    current_list = getattr(st.session_state, f"scanned_{mode}")
    
    c_nav1, c_nav2 = st.columns([1, 2])
    with c_nav1:
        if st.button("🔙 تغيير الفرع / القسم", use_container_width=True):
            st.session_state.app_page = "setup"
            st.session_state.search_barcode_value = ""
            st.rerun()
    with c_nav2:
        st.markdown(f"<div style='text-align:left; font-size:14px; padding-top:8px; color:#555;'>📍 الفرع الحالي: <b>{st.session_state.selected_plant}</b> | القسم: <b>{st.session_state.selected_tab}</b></div>", unsafe_allow_html=True)
    
    st.divider()

    modes_list = ["Barcode", "SAP", "Orion"]
    if mode == "damage": modes_list.insert(0, "Short")
    search_mode = st.radio("طريقة البحث المعتمدة الحالية:", modes_list, horizontal=True)

    # خانة الباركود المستقلة تماماً (تحديث القيمة المكتوبة بدون فور تصفير أو ترحيل عشوائي)
    barcode_input = st.text_input("🔍 امسح الباركود أو اكتب الكود هنا واضغط Enter للبحث وعرض المخزون:", 
                                  value=st.session_state.search_barcode_value)

    # تنفيذ البحث الفوري عند تواجد مدخلات في الخانة
    active_item = None
    raw_val = barcode_input.strip()
    
    if raw_val:
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
            active_item = {
                "SAP": sap_code, "Name": str(row['Item Name']), "Supplier": str(row['Supplier Name']),
                "Factor": str(row['Factor']).split('.')[0], "Unit": str(row['UOM CODE']), "Supplier_ID": str(row['Supplier']).split('.')[0]
            }

    # تفاصيل الصنف المقرؤ (المخزون والستوك يظهران هنا بوضوح)
    st.markdown('<div class="group-box"><div class="group-title">📋 تفاصيل الصنف والمخزون الحالى</div>', unsafe_allow_html=True)
    
    if active_item:
        s_match = st.session_state.stock_df[st.session_state.stock_df.iloc[:, 0].astype(str).str.strip().replace(r'\.0$', '', regex=True) == active_item['SAP']]
        
        # استخراج الستوك الفعلي للفرع
        live_stock = "0"
        if not s_match.empty:
            p_col = [c for c in st.session_state.stock_df.columns if str(c[0]).strip() == st.session_state.selected_plant]
            if p_col: live_stock = str(s_match.iloc[0][p_col[0]]).split('.')[0]
            
        # استخراج مبيعات الأشهر السابقة كاملة لعرضها
        sales_info = "لا توجد مبيعات مسجلة"
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
            <table style="width:100%; border-collapse: collapse; margin-bottom: 10px; background-color: white;">
                <tr style="border-bottom: 1px solid #ddd;"><td style="padding: 6px; font-weight:bold; width:30%;">SAP Code:</td><td style="padding: 6px; font-family:monospace;">{active_item['SAP']}</td></tr>
                <tr style="border-bottom: 1px solid #ddd;"><td style="padding: 6px; font-weight:bold;">اسم الصنف:</td><td style="padding: 6px; color:#111; font-weight:bold;">{active_item['Name']}</td></tr>
                <tr style="border-bottom: 1px solid #ddd;"><td style="padding: 6px; font-weight:bold; color:#007acc;">المخزون الحالي (Live Stock):</td><td style="padding: 6px; font-weight:bold; color:#007acc;">{live_stock}</td></tr>
                <tr><td style="padding: 6px; font-weight:bold; color:#a07000;">تاريخ المبيعات (Sales):</td><td style="padding: 6px; color:#a07000;">{sales_info}</td></tr>
            </table>
        """, unsafe_allow_html=True)
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            u_sel = st.selectbox("الوحدة (Unit):", unit_options, index=unit_options.index(active_item['Unit']) if active_item['Unit'] in unit_options else 0)
        with col_f2:
            if mode in ["internal", "damage", "recipe"]:
                o_sel = st.selectbox("Order Group:", list(order_options.keys()))
            else:
                st.text_input("تاريخ اليوم لجلسة العمل:", value=datetime.now().strftime('%d.%m.%Y'), disabled=True)
                
        # خانة كتابة الكمية المستقلة (تنتظر كتابتك والضغط على الحفظ الفعلي)
        qty_input = st.number_input("✍️ اكتب كمية الجرد المطلوبة حالياً هنا:", min_value=1.0, value=1.0, step=1.0, format="%g")
        
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            if st.button("💾 حفظ وإدراج الصنف في الجدول المعاين بالأسفل", type="primary", use_container_width=True):
                duplicate = False
                for idx, ex in enumerate(current_list):
                    if ex['SAP'] == active_item['SAP']:
                        current_list[idx]['Qty'] = str(float(ex['Qty']) + qty_input)
                        duplicate = True
                        break
                if not duplicate:
                    new_row = {
                        "SAP": active_item['SAP'], "Unit": u_sel, "Qty": str(qty_input),
                        "Plant": st.session_state.selected_plant, "Supplier_ID": active_item['Supplier_ID'], "Name": active_item['Name']
                    }
                    if mode in ["internal", "damage", "recipe"]: new_row["Order"] = order_options.get(o_sel)
                    current_list.append(new_row)
                    
                # تصفير الخانة والعودة لاستقبال الصنف التالي بنجاح دون أخطاء
                st.session_state.search_barcode_value = ""
                st.rerun()
        with col_btn2:
            if st.button("CLEAR", use_container_width=True):
                st.session_state.search_barcode_value = ""
                st.rerun()
    else:
        st.markdown("<p style='text-align:center; color:#777; padding:15px;'>يرجى مسح أو إدخال كود الصنف للتحقق والبدء...</p>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ==============================================================================
    # 📊 خطوة 3: لوحة معاينة الجدول النهائي والتصدير
    # ==============================================================================
    if current_list:
        st.markdown('<div class="group-box"><div class="group-title">📊 لوحة مراجعة ومعاينة القائمة الإجمالية</div>', unsafe_allow_html=True)
        
        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1:
            st.markdown(f'<div class="metric-blue"><div class="metric-title">عدد الأصناف الحالي</div><div class="metric-value">{len(current_list)}</div></div>', unsafe_allow_html=True)
        with c_m2:
            st.markdown(f'<div class="metric-green"><div class="metric-title">TOTAL ORDER</div><div class="metric-value">{len(current_list)}</div></div>', unsafe_allow_html=True)
        with c_m3:
            if mode == "purchase":
                suppliers_count = len(set([i.get('Supplier_ID', '') for i in current_list if i.get('Supplier_ID')]))
                st.markdown(f'<div class="metric-orange"><div class="metric-title">عدد الموردين</div><div class="metric-value">{suppliers_count}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="metric-orange"><div class="metric-title">عدد الموردين</div><div class="metric-value">-</div></div>', unsafe_allow_html=True)
        
        st.write("")
        df_preview = pd.DataFrame(current_list)
        st.dataframe(df_preview[['Name', 'SAP', 'Qty', 'Unit']], use_container_width=True)
        
        if st.button("🗑️ مسح محتويات الجدول بالكامل وإعادة البدء", type="secondary"):
            setattr(st.session_state, f"scanned_{mode}", [])
            st.session_state.search_barcode_value = ""
            st.rerun()
            
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
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            buffer_xlsx = io.BytesIO()
            with pd.ExcelWriter(buffer_xlsx, engine='openpyxl') as writer: df_final.to_excel(writer, index=False)
            st.download_button(label="🟢 Preview & Export List (Excel)", data=buffer_xlsx.getvalue(), file_name=f"AliSystem_{mode}_{today.strftime('%Y%m%d')}.xlsx", use_container_width=True)
        with col_dl2:
            buffer_txt = io.BytesIO()
            df_final.to_csv(buffer_txt, sep='\t', index=False)
            st.download_button(label="📥 تحميل كملف نصي TXT لـ SAP", data=buffer_txt.getvalue(), file_name=f"AliSystem_{mode}_{today.strftime('%Y%m%d')}.txt", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("الجدول الحالي فارغ، لم يتم إضافة أي عناصر بعد.")
