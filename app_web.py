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

st.markdown("""
    <style>
    .main { background-color: #f0f0f0 !important; }
    .main .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 850px; }
    .metric-blue { background-color: #007acc; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; }
    .metric-green { background-color: #2ea44f; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; }
    .metric-orange { background-color: #f37023; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; }
    .group-box { border: 1px solid #b8b8b8; background-color: #ececec; padding: 15px; border-radius: 4px; margin-bottom: 12px; }
    .group-title { font-size: 14px; font-weight: bold; color: #111111; margin-bottom: 10px; border-bottom: 2px solid #007acc; padding-bottom: 4px; }
    </style>
""", unsafe_allow_html=True)

# --- دالات قراءة خفيفة جداً وسريعة لمنع التعليق وعلاج العناوين المركبة ---
def fast_load_master():
    if not os.path.exists(MASTER_FILE_PATH): return None
    try:
        df = pd.read_excel(MASTER_FILE_PATH)
        return df.astype(str).apply(lambda x: x.str.strip())
    except: return None

def fast_load_stock():
    if not os.path.exists(STOCK_FILE_PATH): return None, []
    try:
        # قراءة الملف كـ سطر عادي لتجنب بطء وقفل الـ Multi-Index تماماً
        df = pd.read_excel(STOCK_FILE_PATH, dtype=str)
        df.iloc[:, 0] = df.iloc[:, 0].str.strip().replace(r'\.0$', '', regex=True)
        
        # استخراج الفروع المتوفرة أوتوماتيكياً من أسماء الأعمدة الرقمية
        plants = []
        for col in df.columns:
            col_str = str(col).strip()
            if col_str.isdigit() and col_str not in plants:
                plants.append(col_str)
        return df, sorted(plants)
    except:
        return None, []

# --- تهيئة متغيرات الجلسة وتأمين عدم التكرار المستمر ---
for key in ["scanned_purchase", "scanned_internal", "scanned_damage", "scanned_recipe"]:
    if key not in st.session_state: st.session_state[key] = []

if "master_df" not in st.session_state:
    st.session_state.master_df = fast_load_master()

if "stock_df" not in st.session_state:
    df_s, p_list = fast_load_stock()
    st.session_state.stock_df = df_s
    st.session_state.plants = p_list

if "app_page" not in st.session_state: st.session_state.app_page = "setup"
if "selected_plant" not in st.session_state: st.session_state.selected_plant = ""
if "selected_tab" not in st.session_state: st.session_state.selected_tab = "Purchase Req"
if "current_searched_item" not in st.session_state: st.session_state.current_searched_item = None

# --- القائمة الجانبية المحدثة لإدارة ورفع الملفات ---
with st.sidebar:
    st.header("⚙️ إدارة وتحديث الملفات المحفوظة")
    st.markdown("### 📊 الحالة الحالية للملفات:")
    if st.session_state.master_df is not None: st.success("📁 ملف الباركودات: جاهز")
    else: st.error("❌ ملف الباركودات: غير متوفر")
    if st.session_state.stock_df is not None: st.success("📁 ملف المخزون: جاهز")
    else: st.error("❌ ملف المخزون: غير متوفر")
    
    st.divider()
    new_master = st.file_uploader("تحديث ملف الباركودات (Excel)", type=["xlsx"], key="up_m")
    if new_master:
        with open(MASTER_FILE_PATH, "wb") as f: f.write(new_master.getbuffer())
        st.session_state.master_df = fast_load_master()
        st.success("✅ تم تحديث قاعدة الباركودات!")
        st.rerun()
            
    new_stock = st.file_uploader("تحديث ملف المخزون (Excel)", type=["xlsx"], key="up_s")
    if new_stock:
        with open(STOCK_FILE_PATH, "wb") as f: f.write(new_stock.getbuffer())
        df_s, p_list = fast_load_stock()
        st.session_state.stock_df = df_s
        st.session_state.plants = p_list
        st.success("✅ تم تحديث قاعدة المخزون!")
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
        st.session_state.current_searched_item = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 🔍 خطوة 2: شاشة المسح والبحث الفوري والآمن
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

    with st.form(key="search_bar_form", clear_on_submit=True):
        raw_val = st.text_input("🔍 امسح الباركود أو اكتب الكود هنا واضغط Enter للبحث الحقيقي:").strip()
        submit_search = st.form_submit_button("🔎 ابحث عن الصنف وعرض البيانات", use_container_width=True)
        
        if submit_search and raw_val:
            if search_mode == "Short" and len(raw_val) >= 6: raw_val = raw_val[2:6]
            sap_code = None
            
            if search_mode == "Orion":
                orion_col = next((c for c in st.session_state.stock_df.columns if 'Orion' in str(c)), None)
                if orion_col:
                    m_stock = st.session_state.stock_df[st.session_state.stock_df[orion_col].astype(str).str.strip().replace(r'\.0$', '', regex=True) == raw_val]
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
                st.warning("⚠️ الصنف غير موجود أو الكود خاطئ.")

    st.markdown('<div class="group-box"><div class="group-title">📋 تفاصيل الصنف والمخزون الحالي للفرع</div>', unsafe_allow_html=True)
    
    if st.session_state.current_searched_item:
        item = st.session_state.current_searched_item
        s_match = st.session_state.stock_df[st.session_state.stock_df.iloc[:, 0].astype(str).str.strip().replace(r'\.0$', '', regex=True) == item['SAP']]
        
        live_stock = "0"
        if not s_match.empty and st.session_state.selected_plant in st.session_state.stock_df.columns:
            live_stock = str(s_match.iloc[0][st.session_state.selected_plant]).split('.')[0]
            
        sales_segments = []
        if not s_match.empty:
            for col in st.session_state.stock_df.columns:
                if "Sales" in str(col) or "Total" in str(col):
                    val = str(s_match.iloc[0][col]).split('.')[0]
                    sales_segments.append(f"<b>{col}:</b> {val}")
        sales_info = " &nbsp;|&nbsp; ".join(sales_segments) if sales_segments else "لا توجد مبيعات"

        st.markdown(f"""
            <div style="background-color: white; border: 1px solid #ccc; padding: 12px; border-radius: 4px; font-size: 14px;">
                <b>SAP Code:</b> <code style="color: #007acc;">{item['SAP']}</code><br>
                <b>اسم الصنف:</b> <span style="font-weight:bold;">{item['Name']}</span><br>
                <b>المخزون الحالي (Live Stock):</b> <span style="color: green; font-weight: bold;">{live_stock}</span><br>
                <b>تاريخ المبيعات المحفوظة:</b> <span style="color: #a07000;">{sales_info}</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        with st.form(key="quantity_save_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                u_sel = st.selectbox("الوحدة (Unit):", unit_options, index=unit_options.index(item['Unit']) if item['Unit'] in unit_options else 0)
            with col_f2:
                if mode in ["internal", "damage", "recipe"]:
                    o_sel = st.selectbox("Order Group:", list(order_options.keys()))
                else:
                    st.text_input("تاريخ جلسة العمل الحالية:", value=datetime.now().strftime('%d.%m.%Y'), disabled=True)
            
            qty_val = st.number_input("✍️ أدخل كمية الجرد الحالية للصنف المختار:", min_value=1.0, value=1.0, step=1.0, format="%g")
            
            c_b1, c_b2 = st.columns([3, 1])
            with c_b1:
                btn_save = st.form_submit_button("💾 حفظ وإدراج الصنف في الجدول بالأسفل", type="primary", use_container_width=True)
            with c_b2:
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
                st.success("✅ تم حفظ الصنف بنجاح!")
                st.rerun()
                
            if btn_clear:
                st.session_state.current_searched_item = None
                st.rerun()
    else:
        st.markdown("<p style='text-align:center; color:#777; padding:15px;'>يرجى مسح كود الصنف بالخيار الأعلى أولاً للتحقق والبدء...</p>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ==============================================================================
    # 📊 خطوة 3: المعاينة والتصدير النهائي لـ SAP
    # ==============================================================================
    if current_list:
        st.markdown('<div class="group-box"><div class="group-title">📊 لوحة مراجعة ومعاينة القائمة الإجمالية</div>', unsafe_allow_html=True)
        
        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1: st.markdown(f'<div class="metric-blue">عدد الأصناف الحالي<br><h3>{len(current_list)}</h3></div>', unsafe_allow_html=True)
        with c_m2: st.markdown(f'<div class="metric-green">TOTAL ORDER<br><h3>{len(current_list)}</h3></div>', unsafe_allow_html=True)
        with c_m3:
            if mode == "purchase":
                suppliers_count = len(set([i.get('Supplier_ID', '') for i in current_list if i.get('Supplier_ID')]))
                st.markdown(f'<div class="metric-orange">عدد الموردين<br><h3>{suppliers_count}</h3></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="metric-orange">عدد الموردين<br><h3>-</h3></div>', unsafe_allow_html=True)
        
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
