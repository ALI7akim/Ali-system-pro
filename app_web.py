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

# تطبيق نمط وألوان برنامج الكمبيوتر الكلاسيكي المريح
st.markdown("""
    <style>
    .main { background-color: #f0f0f0 !important; }
    .main .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 850px; }
    
    .metric-blue { background-color: #007acc; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #005999; }
    .metric-green { background-color: #2ea44f; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #227d3c; }
    .metric-orange { background-color: #f37023; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #d05616; }
    
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
    </style>
""", unsafe_allow_html=True)

# --- دالات قراءة البيانات وتنسيقها بأعلى سرعة من السيرفر ---
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

# جلب قاعدة البيانات من الملفات المحفوظة
saved_m = load_processed_master(MASTER_FILE_PATH)
saved_s, saved_p = load_processed_stock(STOCK_FILE_PATH)

# --- تهيئة متغيرات الجلسة (Session State) ---
for key in ["scanned_purchase", "scanned_internal", "scanned_damage", "scanned_recipe"]:
    if key not in st.session_state: st.session_state[key] = []

if "master_df" not in st.session_state: st.session_state.master_df = saved_m
if "stock_df" not in st.session_state: st.session_state.stock_df = saved_s
if "plants" not in st.session_state: st.session_state.plants = saved_p

if "app_page" not in st.session_state: st.session_state.app_page = "setup"
if "selected_plant" not in st.session_state: st.session_state.selected_plant = ""
if "selected_tab" not in st.session_state: st.session_state.selected_tab = "Purchase Req"

# متغيرات لحفظ الصنف الحالي المبحوث عنه في الذاكرة لمنع اختفاء البيانات
if "current_searched_item" not in st.session_state: st.session_state.current_searched_item = None

# --- القائمة الجانبية لتحديث الملفات بشكل خام ---
with st.sidebar:
    st.header("⚙️ إدارة وتحديث الملفات المحفوظة")
    st.markdown("### 📊 الحالة الحالية للملفات:")
    if st.session_state.master_df is not None: st.success("📁 ملف الباركودات: جاهز")
    else: st.error("❌ ملف الباركودات: غير متوفر")
    if st.session_state.stock_df is not None: st.success("📁 ملف المخزون: جاهز")
    else: st.error("❌ ملف المخزون: غير متوفر")
    
    st.divider()
    new_master = st.file_uploader("تحديث ملف الباركودات (Excel)", type=["xlsx"], key="upload_m")
    if new_master:
        with open(MASTER_FILE_PATH, "wb") as f: f.write(new_master.getbuffer())
        st.cache_data.clear()
        st.session_state.master_df = load_processed_master(MASTER_FILE_PATH)
        st.success("✅ تم التحديث!")
        st.rerun()
            
    new_stock = st.file_uploader("تحديث ملف المخزون (Excel)", type=["xlsx"], key="upload_s")
    if new_stock:
        with open(STOCK_FILE_PATH, "wb") as f: f.write(new_stock.getbuffer())
        st.cache_data.clear()
        st.session_state.stock_df, st.session_state.plants = load_processed_stock(STOCK_FILE_PATH)
        st.success("✅ تم التحديث!")
        st.rerun()

if st.session_state.master_df is None or st.session_state.stock_df is None:
    st.warning("⚠️ يرجى رفع الملفات من القائمة الجانبية أولاً للبدء.")
    st.stop()

unit_options = ["AU", "BAG", "BOX", "CAR", "G", "KG", "M", "ML", "PAC", "PC"]
order_options = {
    "500000 Customer Service": "500000", "500001 Fruit and vegetable": "500001",
    "500002 Deli section": "500002", "500003 General sections": "500003",
    "500004 Branch Office": "500004"
}

# ==============================================================================
# 🚪 خطوة 1: شاشة التجهيز واختيار الفرع
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
        st.session_state.current_searched_item = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 🔍 خطوة 2: الشاشة الاحترافية المعتمدة المستقرة
# ==============================================================================
elif st.session_state.app_page == "scan":
    mode = {"Purchase Req": "purchase", "Internal Sale": "internal", "Damage Issue": "damage", "Recipe Issue": "recipe"}[st.session_state.selected_tab]
    current_list = getattr(st.session_state, f"scanned_{mode}")
    
    c_nav1, c_nav2 = st.columns([1, 2])
    with c_nav1:
        if st.button("🔙 تغيير الفرع / القسم", use_container_width=True):
            st.session_state.app_page = "setup"
            st.session_state.current_searched_item = None
            st.rerun()
    with c_nav2:
        st.markdown(f"<div style='text-align:left; font-size:14px; padding-top:8px; color:#555;'>📍 الفرع الحالي: <b>{st.session_state.selected_plant}</b> | القسم: <b>{st.session_state.selected_tab}</b></div>", unsafe_allow_html=True)
    
    st.divider()

    modes_list = ["Barcode", "SAP", "Orion"]
    if mode == "damage": modes_list.insert(0, "Short")
    search_mode = st.radio("طريقة البحث المعتمدة الحالية:", modes_list, horizontal=True)

    # نموذج الاستمارة الموحد والمستقر
    with st.form(key="main_scan_form", clear_on_submit=False):
        raw_val = st.text_input("🔍 امسح الباركود أو اكتب الكود هنا واضغط Enter:").strip()
        
        # البحث الفوري عند الضغط على Enter أو زر التحديث
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
                st.session_state.current_searched_item = {
                    "SAP": sap_code, "Name": str(row['Item Name']), "Supplier": str(row['Supplier Name']),
                    "Factor": str(row['Factor']).split('.')[0], "Unit": str(row['UOM CODE']), "Supplier_ID": str(row['Supplier']).split('.')[0]
                }
            else:
                st.session_state.current_searched_item = None

        # مراجعة بيانات الصنف وعرض الستوك والمبيعات بشكل مستقر
        st.markdown('<div class="group-box"><div class="group-title">📋 تفاصيل الصنف والمخزون الحالي للفرع</div>', unsafe_allow_html=True)
        
        if st.session_state.current_searched_item:
            item = st.session_state.current_searched_item
            s_match = st.session_state.stock_df[st.session_state.stock_df.iloc[:, 0].astype(str).str.strip().replace(r'\.0$', '', regex=True) == item['SAP']]
            
            live_stock = "0"
            if not s_match.empty:
                p_col = [c for c in st.session_state.stock_df.columns if str(c[0]).strip() == st.session_state.selected_plant]
                if p_col: live_stock = str(s_match.iloc[0][p_col[0]]).split('.')[0]
                
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
                <div style="background-color: white; border: 1px solid #aaa; padding: 10px; border-radius: 4px; font-size: 14px; line-height: 1.6;">
                    <b>SAP Code:</b> <code style="color: #007acc;">{item['SAP']}</code><br>
                    <b>اسم الصنف (Description):</b> <span>{item['Name']}</span><br>
                    <b>المخزون الحالي في فرعك (Live Stock):</b> <span style="color: green; font-weight: bold;">{live_stock}</span><br>
                    <b>حركة المبيعات السابقة (Sales):</b> <span style="color: #a07000;">{sales_info}</span>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                u_sel = st.selectbox("الوحدة (Unit):", unit_options, index=unit_options.index(item['Unit']) if item['Unit'] in unit_options else 0)
            with col_f2:
                if mode in ["internal", "damage", "recipe"]:
                    o_sel = st.selectbox("Order Group:", list(order_options.keys()))
                else:
                    st.text_input("تاريخ اليوم لجلسة العمل:", value=datetime.now().strftime('%d.%m.%Y'), disabled=True)
            
            qty_val = st.number_input("✍️ اكتب كمية الجرد الحالية الحالية:", min_value=1.0, value=1.0, step=1.0, format="%g")
            
            col_b1, col_b2 = st.columns([3, 1])
            with col_b1:
                btn_save = st.form_submit_button("💾 حفظ وإدراج الصنف في الجدول بالأسفل", type="primary", use_container_width=True)
            with col_b2:
                btn_clear = st.form_submit_button("CLEAR", use_container_width=True)
                
            if btn_save:
                duplicate = False
                for idx, ex in enumerate(current_list):
                    if ex['SAP'] == item['SAP']:
                        current_list[idx]['Qty'] = str(float(ex['Qty']) + qty_val)
                        duplicate = True
                        break
                if not duplicate:
                    new_row = {
                        "SAP": item['SAP'], "Unit": u_sel, "Qty": str(qty_val),
                        "Plant": st.session_state.selected_plant, "Supplier_ID": item['Supplier_ID'], "Name": item['Name']
                    }
                    if mode in ["internal", "damage", "recipe"]: new_row["Order"] = order_options.get(o_sel)
                    current_list.append(new_row)
                    
                st.session_state.current_searched_item = None
                st.success(f"✅ تم حفظ {item['Name']} بنجاح!")
                st.rerun()
                
            if btn_clear:
                st.session_state.current_searched_item = None
                st.rerun()
        else:
            st.markdown("<p style='text-align:center; color:#777; padding:15px;'>يرجى مسح كود الصنف بالخيار الأعلى أولاً للتحقق من المبيعات والستوك...</p>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ==============================================================================
    # 📊 خطوة 3: لوحة المعاينة الإجمالية الملونة للتصدير
    # ==============================================================================
    if current_list:
        st.markdown('<div class="group-box"><div class="group-title">📊 لوحة مراجعة ومعاينة القائمة الإجمالية</div>', unsafe_allow_html=True)
        
        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1:
            st.markdown(f'<div class="metric-blue"><div class="metric-title" style="color:white;">عدد الأصناف الحالي</div><div class="metric-value" style="color:white; font-size:22px;">{len(current_list)}</div></div>', unsafe_allow_html=True)
        with c_m2:
            st.markdown(f'<div class="metric-green"><div class="metric-title" style="color:white;">TOTAL ORDER</div><div class="metric-value" style="color:white; font-size:22px;">{len(current_list)}</div></div>', unsafe_allow_html=True)
        with c_m3:
            if mode == "purchase":
                suppliers_count = len(set([i.get('Supplier_ID', '') for i in current_list if i.get('Supplier_ID')]))
                st.markdown(f'<div class="metric-orange"><div class="metric-title" style="color:white;">عدد الموردين</div><div class="metric-value" style="color:white; font-size:22px;">{suppliers_count}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="metric-orange"><div class="metric-title" style="color:white;">عدد الموردين</div><div class="metric-value" style="color:white; font-size:22px;">-</div></div>', unsafe_allow_html=True)
        
        st.write("")
        df_preview = pd.DataFrame(current_list)
        st.dataframe(df_preview[['Name', 'SAP', 'Qty', 'Unit']], use_container_width=True)
        
        if st.button("🗑️ مسح محتويات الجدول بالكامل وإعادة البدء", type="secondary"):
            setattr(st.session_state, f"scanned_{mode}", [])
            st.session_state.current_searched_item = None
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
