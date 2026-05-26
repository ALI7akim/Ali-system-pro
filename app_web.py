import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# إعدادات الصفحة
st.set_page_config(page_title="ALI SYSTEM PRO", page_icon="📦", layout="centered")

# تطبيق نمط وألوان برنامج الكمبيوتر الكلاسيكي
st.markdown("""
    <style>
    .main { background-color: #f0f0f0 !important; }
    .main .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 850px; }
    
    /* العدادات الملونة عند المعاينة */
    .metric-blue { background-color: #007acc; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #005999; }
    .metric-green { background-color: #2ea44f; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #227d3c; }
    .metric-orange { background-color: #f37023; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #d05616; }
    .metric-title { font-size: 13px; margin-bottom: 2px; }
    .metric-value { font-size: 20px; font-weight: bold; }
    
    /* تصميم الصناديق */
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

# --- دالات قراءة الملفات من الذاكرة ---
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

# --- تهيئة متغيرات الجلسة (Session State) ---
for key in ["scanned_purchase", "scanned_internal", "scanned_damage", "scanned_recipe"]:
    if key not in st.session_state: st.session_state[key] = []
if "master_df" not in st.session_state: st.session_state.master_df = None
if "stock_df" not in st.session_state: st.session_state.stock_df = None
if "plants" not in st.session_state: st.session_state.plants = []
if "active_item" not in st.session_state: st.session_state.active_item = None

# إدارة الانتقال بين الصفحات (setup أو scan)
if "app_page" not in st.session_state: st.session_state.app_page = "setup"
# متغيرات حفظ الخيارات المختارة
if "selected_plant" not in st.session_state: st.session_state.selected_plant = ""
if "selected_tab" not in st.session_state: st.session_state.selected_tab = "Purchase Req"
# إدارة تصفير حقل الباركود
if "barcode_key" not in st.session_state: st.session_state.barcode_key = 0

# --- القائمة الجانبية (تحميل الملفات) ---
with st.sidebar:
    st.header("⚙️ ملفات النظام")
    master_file = st.file_uploader("1️⃣ ملف الباركودات (EXPORT BARCODE)", type=["xlsx", "xls", "csv"])
    stock_file = st.file_uploader("2️⃣ ملف المخزون (Stock Status)", type=["xlsx", "xls", "csv"])
    
    if master_file:
        try: st.session_state.master_df = load_master_file(master_file); st.success("✅ تم تحميل الباركودات")
        except Exception as e: st.error(f"خطأ: {e}")
    if stock_file:
        try: st.session_state.stock_df, st.session_state.plants = load_stock_file(stock_file); st.success("✅ تم تحميل المخزون")
        except Exception as e: st.error(f"خطأ: {e}")

# حماية التشغيل
if st.session_state.master_df is None or st.session_state.stock_df is None:
    st.warning("⚠️ يرجى رفع ملف الباركودات وملف المخزون من القائمة الجانبية للبدء.")
    st.stop()

# خيارات النظام الثابتة
unit_options = ["AU", "BAG", "BOX", "CAR", "G", "KG", "M", "ML", "PAC", "PC"]
order_options = {
    "500000 Customer Service": "500000", "500001 Fruit and vegetable": "500001",
    "500002 Deli section": "500002", "500003 General sections": "500003",
    "500004 Branch Office": "500004"
}

# ==============================================================================
# 🚪 الصفحة الأولى: اختيار الإعدادات والفرع والقسم
# ==============================================================================
if st.session_state.app_page == "setup":
    st.markdown('<div class="group-box"><div class="group-title">🏢 خطوة 1: تحديد وجهة العمل والفرع</div>', unsafe_allow_html=True)
    
    # اختيار الفرع
    plant_idx = 0
    if st.session_state.selected_plant in st.session_state.plants:
        plant_idx = st.session_state.plants.index(st.session_state.selected_plant)
    plant_selected = st.selectbox("🏬 اختر الفرع الحالي (Plant) الذي ستعمل عليه:", st.session_state.plants, index=plant_idx)
    
    # اختيار القسم
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
# 🔍 الصفحة الثانية: شاشة المسح الفوري والجرد (مع أزرار العودة والكلير للباركود)
# ==============================================================================
elif st.session_state.app_page == "scan":
    mode = {"Purchase Req": "purchase", "Internal Sale": "internal", "Damage Issue": "damage", "Recipe Issue": "recipe"}[st.session_state.selected_tab]
    current_list = getattr(st.session_state, f"scanned_{mode}")
    
    # سطر علوي للعودة واستعراض معلومات الوجهة الحالية بشكل مضغوط جداً
    c_nav1, c_nav2 = st.columns([1, 2])
    with c_nav1:
        if st.button("🔙 تغيير الفرع / القسم", use_container_width=True):
            st.session_state.app_page = "setup"
            st.session_state.active_item = None
            st.rerun()
    with c_nav2:
        st.markdown(f"<div style='text-align:left; font-size:14px; padding-top:8px; color:#555;'>📍 الفرع: <b>{st.session_state.selected_plant}</b> | القسم: <b>{st.session_state.selected_tab}</b></div>", unsafe_allow_html=True)
    
    st.divider()

    # خيارات طريقة البحث والمسح الفورية في سطر واحد
    modes_list = ["Barcode", "SAP", "Orion"]
    if mode == "damage": modes_list.insert(0, "Short")
    search_mode = st.radio("طريقة البحث المعتمدة الحالية:", modes_list, horizontal=True)

    # دالة المعالجة والبحث عند إدخال الباركود
    def on_barcode_change():
        raw_val = st.session_state[f"barcode_input_{st.session_state.barcode_key}"].strip()
        if not raw_val: return
        
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

    # حقل الإدخال الرئيسي للباركود والمسح الفوري
    st.text_input("🔍 امسح الباركود أو اكتب الكود هنا واضغط Enter:", key=f"barcode_input_{st.session_state.barcode_key}", on_change=on_barcode_change)

    # صندوق تفاصيل ومراجعة بيانات الصنف النشط
    st.markdown('<div class="group-box"><div class="group-title">📋 تفاصيل الصنف المقروء حالياً</div>', unsafe_allow_html=True)

    if st.session_state.active_item:
        item = st.session_state.active_item
        s_match = st.session_state.stock_df[st.session_state.stock_df.iloc[:, 0].astype(str).str.strip().replace(r'\.0$', '', regex=True) == item['SAP']]
        
        # جلب مخزون الصنف في الفرع المختار
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

        # عرض البيانات النصية للبطاقة
        st.markdown(f"""
            <p class="computer-label">SAP Code:</p><div style="background-color: white; border: 1px solid #aaa; padding: 6px; font-family: monospace; font-size: 14px; margin-bottom: 8px;">{item['SAP']}</div>
            <p class="computer-label">Description (اسم الصنف كاملاً):</p><div style="background-color: white; border: 1px solid #aaa; padding: 6px; font-size: 14px; margin-bottom: 8px; font-weight: bold; color: #111;">{item['Name']}</div>
            <p class="computer-label">Live Stock (مخزون الفرع الحالي):</p><div style="background-color: white; border: 1px solid #aaa; padding: 6px; font-size: 13px; margin-bottom: 8px; font-weight: bold; color: #007acc;">{live_stock}</div>
            <p class="computer-label">Sales History (المبيعات):</p><div style="background-color: #fcf8e3; border: 1px solid #fbeed5; padding: 6px; font-size: 12px; margin-bottom: 8px; color: #c09853;">{sales_info}</div>
        """, unsafe_allow_html=True)
        
        # مدخلات التعبئة والكمية
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            u_sel = st.selectbox("الوحدة (Unit):", unit_options, index=unit_options.index(item['Unit']) if item['Unit'] in unit_options else 0)
        with col_f2:
            if mode in ["internal", "damage", "recipe"]:
                o_sel = st.selectbox("Order Group:", list(order_options.keys()))
            else:
                st.text_input("تاريخ اليوم لجلسة العمل:", value=datetime.now().strftime('%d.%m.%Y'), disabled=True)
                
        qty_input = st.number_input("اكتب كمية الجرد الحالية واضغط حفظ:", min_value=1.0, value=1.0, step=1.0, format="%g")

        # أزرار الحفظ والمسح للباركود الحالي فقط
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            if st.button("💾 حفظ الصنف إلى القائمة (Enter)", type="primary", use_container_width=True):
                duplicate = False
                for idx, ex in enumerate(current_list):
                    if ex['SAP'] == item['SAP']:
                        current_list[idx]['Qty'] = str(float(ex['Qty']) + qty_input)
                        duplicate = True
                        break
                if not duplicate:
                    new_row = {
                        "SAP": item['SAP'], "Unit": u_sel, "Qty": str(qty_input),
                        "Plant": st.session_state.selected_plant, "Supplier_ID": item['Supplier_ID'], "Name": item['Name']
                    }
                    if mode in ["internal", "damage", "recipe"]: new_row["Order"] = order_options.get(o_sel)
                    current_list.append(new_row)
                    
                # تصفير حقل نص الباركود فقط والانتقال للصنف التالي
                st.session_state.active_item = None
                st.session_state.barcode_key += 1
                st.rerun()
                
        with col_btn2:
            # 🌟 زر CLEAR يقوم بمسح وإفراغ حقل الباركود فقط دون حذف الجدول المحفوظ
            if st.button("CLEAR", use_container_width=True, help="تصفير خانة البحث والباركود الحالية فقط"):
                st.session_state.active_item = None
                st.session_state.barcode_key += 1
                st.rerun()
    else:
        st.markdown("<p style='text-align:center; color:#777; padding:15px;'>النظام جاهز تماماً ومستعد لاستقبال مسحة الباركود أو كود الصنف التالي...</p>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ==============================================================================
    # 📊 خطوة 3: لوحة المعاينة والعدادات الثلاثية أسفل الصفحة عند الجداول
    # ==============================================================================
    if current_list:
        st.markdown('<div class="group-box"><div class="group-title">📊 لوحة مراجعة ومعاينة القائمة الإجمالية</div>', unsafe_allow_html=True)
        
        # العدادات الإحصائية الثلاثية تظهر هنا بدقة ووضوح عند جدول المراجعة
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
            st.session_state.active_item = None
            st.rerun()
            
        # معالجة تصدير هياكل ملفات SAP
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
