import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import streamlit.components.v1 as components

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

# حقل تحكم لإعادة الفوكس برمجياً للباركود
if "focus_trigger" not in st.session_state: st.session_state.focus_trigger = 0

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
        st.rerun()

# حماية النظام من العمل دون ملفات
if st.session_state.master_df is None or st.session_state.stock_df is None:
    st.warning("⚠️ يرجى رفع ملف الباركودات وملف المخزون من القائمة الجانبية للبدء.")
    st.stop()

# --- القوائم
