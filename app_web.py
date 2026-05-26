import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# إعدادات الصفحة
st.set_page_config(page_title="ALI SYSTEM PRO", page_icon="📦", layout="centered")

# تطبيق نمط وألوان برنامج الكمبيوتر الكلاسيكي مع كود الـ JavaScript للتنقل الآلي
st.markdown("""
    <style>
    .main { background-color: #f0f0f0 !important; }
    .main .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 850px; }
    
    /* العدادات الملونة عند المعاينة */
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
    // سكربت جافاسكربت لمراقبة ضغط أزرار الإنتر والتنقل الفوري بين الخانات على نفس السطر
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            var activeEl = document.activeElement;
            
            // إذا كان المستخدم واقفا في خانة الباركود وضغط إنتر، ينتقل للكمية فوراً
            if (activeEl && activeEl.id && activeEl.id.includes('barcode_input')) {
                setTimeout(function() {
                    var qtyInput = document.querySelector('input[id*="qty_input"]');
                    if (qtyInput) {
                        qtyInput.focus();
                        qtyInput.select();
                    }
                }, 200);
            }
            
            // إذا كان المستخدم واقفا في خانة الكمية وضغط إنتر، يتم تفعيل زر الحفظ تلقائياً
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
    df_s.iloc
