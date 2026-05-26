import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# إعدادات الصفحة
st.set_page_config(page_title="ALI SYSTEM PRO", page_icon="📦", layout="centered")

# تطبيق نمط وألوان برنامج الكمبيوتر الكلاسيكي مع كود الـ JavaScript للتحكم بالـ Enter
st.markdown("""
    <style>
    .main { background-color: #f0f0f0 !important; }
    .main .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 850px; }
    
    /* العدادات الملونة */
    .metric-blue { background-color: #007acc; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #005999; }
    .metric-green { background-color: #2ea44f; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #227d3c; }
    .metric-orange { background-color: #f37023; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 4px; border: 1px solid #d05616; }
    .metric-title { font-size: 13px; margin-bottom: 2px; color: white !important; }
    .metric-value { font-size: 20px; font-weight: bold; color: white !important; }
    
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

    <script>
    // سكربت جافاسكربت لمراقبة ضغط أزرار الإنتر والتنقل الفوري بين الخانات
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            var activeEl = document.activeElement;
            
            // إذا كان المستخدم واقف في خانة الباركود وضغط إنتر
            if (activeEl && activeEl.id && activeEl.id.includes('barcode_input')) {
                setTimeout(function() {
                    var qtyInput = document.querySelector('input[id*="qty_input"]');
                    if (qtyInput) {
                        qtyInput.focus();
                        qtyInput.select();
                    }
                }, 300);
            }
            
            // إذا كان المستخدم واقف في خانة الكمية وضغط إنتر
            if (activeEl && activeEl.id && activeEl.id.includes('qty_input')) {
                setTimeout(function() {
                    var saveBtn = document.querySelector('button[id*="save_btn"]');
                    if (saveBtn) {
                        saveBtn.click();
                    }
                }, 100);
            }
        }
    });
    </script>
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

# إدارة الانتقال والخيارات
if "app_page" not in st.session_state: st.session_state.app_page = "setup"
if "selected_plant" not in st.session_state: st.session_state.selected_plant = ""
if "selected_tab" not in st.session_state: st.session_state.selected_tab = "Purchase Req"
if "barcode_key" not in st.session_state: st.session_state.barcode_key = 0

# متغير وسيط للاحتفاظ بقيمة الباركود المقروء بعد الـ rerun لضمان ثبات التركيز
if "last_valid_barcode" not in st.session_state: st.session_state.last_valid_barcode = ""

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

unit_options = ["AU", "BAG", "BOX", "CAR", "G", "KG", "M", "ML", "PAC", "PC"]
order_options = {
    "500000 Customer Service": "500000", "500001 Fruit and vegetable": "500001",
    "500002 Deli section": "500002", "500003 General sections": "500003",
    "500004 Branch Office": "500004"
}

# ==============================================================================
# 🏢 الصفحة الأولى: اختيار الإعدادات والفرع والقسم
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
# 🔍 الصفحة الثانية: شاشة المسح الفوري والتنقل بالإنتر (معالجة JS الحية)
# ==============================================================================
elif st.session_state.app_page == "scan":
    mode = {"Purchase Req": "purchase", "Internal Sale": "internal", "Damage Issue": "damage", "Recipe Issue": "recipe"}[st.session_state.selected_tab]
    current_list = getattr(st.session_state, f"scanned_{mode}")
    
    c_nav1, c_nav2 = st.columns([1, 2])
    with c_nav1:
        if st.button("🔙 تغيير الفرع / القسم", use_container_width=True):
            st.session_state.app_page = "setup"
            st.session_state.active_item = None
            st.rerun()
    with c_nav2:
        st.markdown(f"<div style='text-align:left; font-size:14px; padding-top:8px; color:#555;'>📍 الفرع: <b>{st.session_state.selected_plant}</b> | القسم: <b>{st.session_state.selected_tab}</b></div>", unsafe_allow_html=True)
    
    st.divider()

    modes_list = ["Barcode", "SAP", "Orion"]
    if mode == "damage": modes_list.insert(0, "Short")
    search_mode = st.radio("طريقة البحث المعتمدة الحالية:", modes_list, horizontal=True)

    def on_barcode_change():
        input_key = f"barcode_input_{st.session_state.barcode_key}"
        raw_val = str(st.session_state[input_key]).strip()
        if not raw_val or raw_val == "0" or raw_val == "" or raw_val == "None": return
        
        if search_mode == "Short" and len(raw_val) >= 6: raw_val = raw_val[2:6]
        sap_code = None
        
        if search_mode == "Orion":
            col = next((c for c in st.session_state.stock_df.columns if 'Orion Item Code' in str(c).strip()), None)
            if col:
                m_stock = st.session_state.stock_df[st.session_state.stock_df[col].astype(str).str.strip().replace(r'\.0$', '', regex=True) == raw_val]
                if not m_stock.empty: sap_code = str(m_stock.iloc[0, 0]).strip().replace('.0', '')
        else:
            s_col = 'Item Barcode' if search_mode in ["Short", "Barcode"] else 'Item Code'
            m_temp = m_temp = st.session_state.master_df.copy()
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
            st.session_state.last_valid_barcode = raw_val
        else:
            st.session_state.active_item = None

    # 🌟 تعديل 1: الخانتين متواجدتين معاً في الصفحة لمنع اختفاء العناصر، ويتم التنقل بينهما عن طريق الـ JavaScript تلقائياً بالـ Enter
    col_inputs1, col_inputs2 = st.columns([2, 1])
    
    with col_inputs1:
        # حقل الباركود مخصص ومحمي للأرقام فقط
        barcode_val = st.number_input("🔍 امسح الباركود أو اكتب الكود (أرقام فقط) واضغط Enter:", 
                        min_value=0, value=0, step=1, format="%d",
                        key=f"barcode_input_{st.session_state.barcode_key}", 
                        on_change=on_barcode_change)
        
    with col_inputs2:
        # حقل الكمية يقبل الأرقام العشرية والكسور (مثل 0.5) ومربوط برمجياً بالـ JavaScript ليعمل عند الضغط على Enter في الباركود
        qty_input = st.number_input("✏️ الكمية المطلوبة الحالية:", 
                                    min_value=0.0, value=0.0, step=0.001, format="%g", key=f"qty_input_{st.session_state.barcode_key}")

    st.markdown('<div class="group-box"><div class="group-title">📋 تفاصيل الصنف الحالي في الذاكرة</div>', unsafe_allow_html=True)

    if st.session_state.active_item:
        item = st.session_state.active_item
        s_match = st.session_state.stock_df[st.session_state.stock_df.iloc[:, 0].astype(str).str.strip().replace(r'\.0$', '', regex=True) == item['SAP']]
        
        live_stock = "-"
        if not s_match.empty:
            p_col = [c for c in st.session_state.stock_df.columns if str(c[0]).strip() == st.session_state.selected_plant]
            if p_col: live_stock = str(s_match.iloc[0][p_col[0]]).split('.')[0]

        st.markdown(f"""
            <table style="width:100%; border-collapse: collapse; font-size:13px; background-color: white;">
                <tr style="border-bottom: 1px solid #ddd;"><td style="padding: 6px; font-weight:bold; width:30%;">SAP Code:</td><td style="padding: 6px; font-family: monospace; color:#007acc;">{item['SAP']}</td></tr>
                <tr style="border-bottom: 1px solid #ddd;"><td style="padding: 6px; font-weight:bold;">Description:</td><td style="padding: 6px; font-weight:bold; color:#111;">{item['Name']}</td></tr>
                <tr><td style="padding: 6px; font-weight:bold;">Live Stock:</td><td style="padding: 6px; font-weight:bold; color:#2ea44f;">{live_stock}</td></tr>
            </table>
        """, unsafe_allow_html=True)
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            u_sel = st.selectbox("الوحدة (Unit):", unit_options, index=unit_options.index(item['Unit']) if item['Unit'] in unit_options else 0)
        with col_f2:
            if mode in ["internal", "damage", "recipe"]:
                o_sel = st.selectbox("Order Group:", list(order_options.keys()))
            else:
                st.text_input("تاريخ اليوم لجلسة العمل:", value=datetime.now().strftime('%d.%m.%Y'), disabled=True)
                
        st.write("")
        # زر الحفظ مربوط بالـ JavaScript ليتم النقر عليه برمجياً بمجرد ضغط Enter داخل حقل الكمية
        if st.button("💾 حفظ الصنف إلى القائمة والانتقال للمسح التالي (Enter)", type="primary", use_container_width=True, key=f"save_btn_{st.session_state.barcode_key}") or qty_input > 0:
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
                        "Plant": st.session_state.selected_plant, "Supplier_ID": item['Supplier_ID'], "Name": item['Name']
                    }
                    if mode in ["internal", "damage", "recipe"]: new_row["Order"] = order_options.get(o_sel)
                    current_list.append(new_row)
            
            # 🌟 تعديل 2: تصفير كامل الشاشة، وتغيير الـ key لفتح حقل مسح باركود جديد تماماً واستعادة الـ Focus التلقائي له
            st.session_state.active_item = None
            st.session_state.barcode_key += 1
            st.rerun()
    else:
        st.markdown("<p style='text-align:center; color:#777; padding:15px;'>النظام جاهز ومستعد تماماً لاستقبال مسحة الباركود الأولى أو التالية...</p>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ==============================================================================
    # 📊 لوحة المعاينة (تعديل وحذف صنف معين)
    # ==============================================================================
    if current_list:
        st.write("")
        show_preview = st.checkbox("👁️ فتح لوحة مراجعة ومعاينة القائمة الإجمالية والتصدير كـ Excel / TXT", value=False)
        
        if show_preview:
            st.markdown('<div class="group-box"><div class="group-title">📊 لوحة مراجعة ومعاينة القائمة الإجمالية</div>', unsafe_allow_html=True)
            st.write("✏️ **تعديل الكميات أو حذف عناصر محددة من القائمة الحالية:**")
            
            updated_list = []
            for idx, entry in enumerate(current_list):
                col_i1, col_i2, col_i3, col_i4 = st.columns([3, 1.5, 1.5, 1])
                with col_i1:
                    st.markdown(f"<div style='padding-top:5px; font-size:13px;'><b>{entry['Name']}</b><br><small style='color:#666;'>SAP: {entry['SAP']}</small></div>", unsafe_allow_html=True)
                with col_i2:
                    new_qty = st.number_input(f"الكمية", min_value=0.001, value=float(entry['Qty']), step=0.001, format="%g", key=f"edit_qty_{idx}")
                    entry['Qty'] = str(new_qty)
                with col_i3:
                    st.markdown(f"<div style='padding-top:28px; text-align:center; font-weight:bold; color:#007acc;'>{entry['Unit']}</div>", unsafe_allow_html=True)
                with col_i4:
                    st.write("")
                    st.write("")
                    if st.button("❌", key=f"del_{idx}", help="حذف هذا الصنف"):
                        current_list.pop(idx)
                        setattr(st.session_state, f"scanned_{mode}", current_list)
                        st.rerun()
                updated_list.append(entry)
            
            setattr(st.session_state, f"scanned_{mode}", updated_list)
            st.divider()
            
            c_m1, c_m2, c_m3 = st.columns(3)
            with c_m1: st.markdown(f'<div class="metric-blue"><div class="metric-title">عدد الأصناف الحالية</div><div class="metric-value">{len(current_list)}</div></div>', unsafe_allow_html=True)
            with c_m2: st.markdown(f'<div class="metric-green"><div class="metric-title">TOTAL ORDER</div><div class="metric-value">{len(current_list)}</div></div>', unsafe_allow_html=True)
            with c_m3:
                if mode == "purchase":
                    suppliers_count = len(set([i.get('Supplier_ID', '') for i in current_list if i.get('Supplier_ID')]))
                    st.markdown(f'<div class="metric-orange"><div class="metric-title">عدد الموردين</div><div class="metric-value">{suppliers_count}</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="metric-orange"><div class="metric-title">عدد الموردين</div><div class="metric-value">-</div></div>', unsafe_allow_html=True)
            
            st.write("")
            if st.button("🗑️ مسح محتويات الجدول بالكامل وإعادة البدء", type="secondary", use_container_width=True):
                setattr(st.session_state, f"scanned_{mode}", [])
                st.session_state.active_item = None
                st.rerun()
                
            # مخرجات وهياكل ملفات SAP المعتمدة
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
