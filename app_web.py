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

# تهيئة حقل الباركود النشط لعدم الفقدان
if "active_item" not in st.session_state: st.session_state.active_item = None
if "barcode_input_key" not in st.session_state: st.session_state.barcode_input_key = 0
if "qty_input_key" not in st.session_state: st.session_state.qty_input_key = 1000

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
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 🔍
