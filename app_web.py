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

# تطبيق نمط وألوان برنامج الكمبيوتر الكلاسيكي
st.markdown("""
    <style>
    .main { background-color: #f0f0f0 !important; }
    .main .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 850px; }
    
    /* العدادات الملونة أسفل المعاينة */
    .metric-blue { background-color: #007acc; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #005999; }
    .metric-green { background-color: #2ea44f; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #227d3c; }
    .metric-orange { background-color: #f37023; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #d05616; }
    .metric-title { font-size: 13px; margin-bottom: 2px; }
    .metric-value { font-size: 20px; font-weight: bold; }
    
    /* تصميم الصناديق الكلاسيكية */
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

# متغيرات إدارة مسح الباركود الحالي
if "temp_barcode" not in st.session_state: st.session_state.temp_barcode = ""
if "barcode_input_key" not in st.session_state: st.session_state.barcode_input_key = 0

# --- القائمة الجانبية: معالجة رفع الملفات وحفظها بشكل خام 100% لتجنب أخطاء الـ MultiIndex ---
with st.sidebar:
    st.header("⚙️ إدارة وتحديث الملفات المحفوظة")
    
    st.markdown("### 📊 الحالة الحالية للملفات:")
    if st.session_state.master_df is not None: st.success("📁 ملف الباركودات: مَحْفُوظ وجاهز للعمل")
    else: st.error("❌ ملف الباركودات: غير متوفر حالياً")
        
    if st.session_state.stock_df is not None: st.success("📁 ملف المخزون: مَحْفُوظ وجاهز للعمل")
    else: st.error("❌ ملف المخزون: غير متوفر حالياً")
    
    st.divider()
    st.markdown("### 🔄 رفع وتحديث الملفات:")
    
    new_master = st.file_uploader("تحديث ملف الباركودات (Excel)", type=["xlsx"], key="upload_m")
    if new_master:
        try:
            # حفظ الملف الخام مباشرة دون تفكيكه لتفادي أي مشاكل برمجية
            with open(MASTER_FILE_PATH, "wb") as f:
                f.write(new_master.getbuffer())
            st.cache_data.clear()
            st.session_state.master_df = load_processed_master(MASTER_FILE_PATH)
            st.success("✅ تم حفظ وتحديث ملف الباركودات فورا!")
            st.rerun()
        except Exception as e: st.error(f"خطأ أثناء الحفظ: {e}")
            
    new_stock = st.file_uploader("تحديث ملف المخزون (Excel)", type=["xlsx"], key="upload_s")
    if new_stock:
        try:
            # حفظ الملف الخام مباشرة لحل مشكلة الـ MultiIndex تماماً
            with open(STOCK_FILE_PATH, "wb") as f:
                f.write(new_stock.getbuffer())
            st.cache_data.clear()
            st.session_state.stock_df, st.session_state.plants = load_processed_stock(STOCK_FILE_PATH)
            st.success("✅ تم حفظ وتحديث ملف المخزون بنجاح!")
            st.rerun()
        except Exception as e: st.error(f"خطأ أثناء الحفظ: {e}")

# حماية التشغيل الأساسية للملفات المفقودة
if st.session_state.master_df is None or st.session_state.stock_df is None:
    st.warning("⚠️ النظام يحتاج إلى ملف الباركودات وملف المخزون للبدء. يرجى رفعها لمرة واحدة فقط من القائمة الجانبية.")
    st.stop()

# خيارات القوائم الثابتة
unit_options = ["AU", "BAG", "BOX", "CAR", "G", "KG", "M", "ML", "PAC", "PC"]
order_options = {
    "500000 Customer Service": "500000", "500001 Fruit and vegetable": "500001",
    "500002 Deli section": "500002", "500003 General sections": "500003",
    "500004 Branch Office": "500004"
}

# ==============================================================================
# 🚪 خطوة 1: شاشة تحديد الفرع والقسم الحالي
# ==============================================================================
if st.session_state.app_page == "setup":
    st.markdown('<div class="group-box"><div class="group-title">🏢 خطوة 1: تحديد وجهة العمل والفرع</div>', unsafe_allow_html=True)
    
    plant_idx = 0
    if st.session_state.selected_plant in st.session_state.plants:
        plant_idx = st.session_state.plants.index(st.session_state.selected_plant)
    plant_selected = st.selectbox("🏬 اختر الفرع الحالي (Plant) الذي ستعمل عليه:", st.session_state.plants, index=plant_idx)
    
    tab_list = ["Purchase Req", "Internal Sale", "Damage Issue", "Recipe Issue"]
    tab_idx = tab_list.index(st.session_state.selected_tab) if st.session_state.selected_tab in tab_list else 0
    tab_selected = st.radio("📂 اختر قسم العمل الحالي:", tab_list, index=tab_idx, horizontal=True)
    
    st.write("")
    if st.button("🚀 الدخول لصفحة مسح الأصناف والباركود 📥", type="primary", use_container_width=True):
        st.session_state.selected_plant = plant_selected
        st.session_state.selected_tab = tab_selected
        st.session_state.app_page = "scan"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 🔍 خطوة 2: الشاشة الاحترافية للمسح الفوري ومعالجة الـ Enter والـ Clear
# ==============================================================================
elif st.session_state.app_page == "scan":
    mode = {"Purchase Req": "purchase", "Internal Sale": "internal", "Damage Issue": "damage", "Recipe Issue": "recipe"}[st.session_state.selected_tab]
    current_list = getattr(st.session_state, f"scanned_{mode}")
    
    # سطر التنقل والرجوع العلوي
    c_nav1, c_nav2 = st.columns([1, 2])
    with c_nav1:
        if st.button("🔙 تغيير الفرع / القسم", use_container_width=True):
            st.session_state.app_page = "setup"
            st.session_state.temp_barcode = ""
            st.rerun()
    with c_nav2:
        st.markdown(f"<div style='text-align:left; font-size:14px; padding-top:8px; color:#555;'>📍 الفرع الحالى: <b>{st.session_state.selected_plant}</b> | القسم: <b>{st.session_state.selected_tab}</b></div>", unsafe_allow_html=True)
    
    st.divider()

    modes_list = ["Barcode", "SAP", "Orion"]
    if mode == "damage": modes_list.insert(0, "Short")
    search_mode = st.radio("طريقة البحث المعتمدة الحالية:", modes_list, horizontal=True)

    # نموذج الاستمارة الذكي (Form) للتحكم الكامل في ضغطة زر الـ Enter
    with st.form(key=f"barcode_scanning_form_{st.session_state.barcode_input_key}", clear_on_submit=False):
        
        # 1. حقل إدخال الباركود الأساسي
        barcode_val = st.text_input("🔍 امسح الباركود أو اكتب الكود هنا ثم اضغط Enter للحفظ التلقائي القادم:", value=st.session_state.temp_barcode)
        
        # البحث الفوري عن الصنف لتجهيز بيانات العرض والمخزون والمبيعات الحالية
        active_item = None
        raw_val = barcode_val.strip()
        
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

        # 2. صندوق معلومات الصنف المقروء
        st.markdown('<div class="group-box"><div class="group-title">📋 تفاصيل الصنف المقروء حالياً</div>', unsafe_allow_html=True)
        
        if active_item:
            s_match = st.session_state.stock_df[st.session_state.stock_df.iloc[:, 0].astype(str).str.strip().replace(r'\.0$', '', regex=True) == active_item['SAP']]
            
            live_stock = "-"
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
                <p class="computer-label">SAP Code:</p><div style="background-color: white; border: 1px solid #aaa; padding: 6px; font-family: monospace; font-size: 14px; margin-bottom: 8px;">{active_item['SAP']}</div>
                <p class="computer-label">Description (اسم الصنف):</p><div style="background-color: white; border: 1px solid #aaa; padding: 6px; font-size: 14px; margin-bottom: 8px; font-weight: bold; color: #111;">{active_item['Name']}</div>
                <p class="computer-label">Live Stock (مخزون الفرع الحالي):</p><div style="background-color: white; border: 1px solid #aaa; padding: 6px; font-size: 13px; margin-bottom: 8px; font-weight: bold; color: #007acc;">{live_stock}</div>
                <p class="computer-label">Sales History (المبيعات):</p><div style="background-color: #fcf8e3; border: 1px solid #fbeed5; padding: 6px; font-size: 12px; margin-bottom: 8px; color: #c09853;">{sales_info}</div>
            """, unsafe_allow_html=True)
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                u_sel = st.selectbox("الوحدة (Unit):", unit_options, index=unit_options.index(active_item['Unit']) if active_item['Unit'] in unit_options else 0)
            with col_f2:
                if mode in ["internal", "damage", "recipe"]:
                    o_sel = st.selectbox("Order Group:", list(order_options.keys()))
                else:
                    st.text_input("تاريخ اليوم لجلسة العمل:", value=datetime.now().strftime('%d.%m.%Y'), disabled=True)
                    
            qty_input = st.number_input("اكتب كمية الجرد الحالية الحالية واضغط Enter للحفظ المباشر:", min_value=1.0, value=1.0, step=1.0, format="%g")
        else:
            st.markdown("<p style='text-align:center; color:#777; padding:15px;'>يرجى إدخال أو مسح كود صنف صحيح لعرض بيانات الجرد والكمية...</p>", unsafe_allow_html=True)
            u_sel, qty_input = "PC", 1.0
            
        st.markdown('</div>', unsafe_allow_html=True)

        # 3. أزرار التحكم بالاستمارة والمسح الفوري (Enter)
        btn_save_triggered = st.form_submit_button("💾 حفظ الصنف الحالي إلى القائمة (Enter)", type="primary", use_container_width=True)
        
        if btn_save_triggered and active_item:
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
                
            # تصفير حقل الإدخال بالكامل للانتقال الفوري للصنف التالي
            st.session_state.temp_barcode = ""
            st.session_state.barcode_input_key += 1
            st.rerun()

    # زر الـ CLEAR المستقل تماماً خارج الاستمارة لتصفير حقل الباركود فقط دون التأثير على الجدول
    if st.session_state.temp_barcode or barcode_val:
        if st.button("❌ CLEAR (مسح خانة الباركود الحالية فقط)", use_container_width=True):
            st.session_state.temp_barcode = ""
            st.session_state.barcode_input_key += 1
            st.rerun()

    # ==============================================================================
    # 📊 خطوة 3: لوحة المعاينة والعدادات الثلاثية وجداول التصدير لـ SAP
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
            st.session_state.temp_barcode = ""
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
