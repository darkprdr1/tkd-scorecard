import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from streamlit_gsheets import GSheetsConnection  # 引入 Google Sheets 連線套件

# 1. 頁面設定
st.set_page_config(page_title="跆拳道選手評分卡", page_icon="🥋", layout="centered")

# CSS 優化
st.markdown("""
    <style>
    .stSlider [data-baseweb="slider"] { margin-top: -15px; }
    .stRadio [role="radiogroup"] { flex-direction: row; overflow-x: auto; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥋 跆拳道選手評分卡 (Cloud Sync)")

# --- 量級定義 ---
weight_categories = {
    "Senior (成人)": {
        "Male (男)": ["-54 kg", "-58 kg", "-63 kg", "-68 kg", "-74 kg", "-80 kg", "-87 kg", "+87 kg"],
        "Female (女)": ["-46 kg", "-49 kg", "-53 kg", "-57 kg", "-62 kg", "-67 kg", "-73 kg", "+73 kg"]
    },
    "Junior (青少年 15-17歲)": {
        "Male (男)": ["-45 kg", "-48 kg", "-51 kg", "-55 kg", "-59 kg", "-63 kg", "-68 kg", "-73 kg", "-78 kg", "+78 kg"],
        "Female (女)": ["-42 kg", "-44 kg", "-46 kg", "-49 kg", "-52 kg", "-55 kg", "-59 kg", "-63 kg", "-68 kg", "+68 kg"]
    },
    "Cadet (少年 12-14歲)": {
        "Male (男)": ["-33 kg", "-37 kg", "-41 kg", "-45 kg", "-49 kg", "-53 kg", "-57 kg", "-61 kg", "-65 kg", "+65 kg"],
        "Female (女)": ["-29 kg", "-33 kg", "-37 kg", "-41 kg", "-44 kg", "-47 kg", "-51 kg", "-55 kg", "-59 kg", "+59 kg"]
    }
}

# --- 基本資料 ---
st.subheader("📋 基本資料 / Profile")
col1, col2 = st.columns(2)
with col1:
    athlete_name = st.text_input("選手姓名 / Name")
with col2:
    eval_date = st.date_input("評估日期", datetime.today())

col_age, col_gender = st.columns(2)
with col_age:
    age_group = st.selectbox("年齡組別", list(weight_categories.keys()))
with col_gender:
    gender = st.radio("性別", ["Male (男)", "Female (女)"], horizontal=True)

available_weights = weight_categories[age_group][gender]
weight_cat = st.selectbox("量級", available_weights)
context = st.radio("情境", ["國內", "國際", "移訓"], horizontal=True)

st.markdown("---")

# --- 評分表單 ---
with st.form("scorecard_form"):
    st.info("填寫完畢後，請點擊底部的「提交」按鈕，資料將自動上傳 Google Sheets。")

    rubrics = {
        "1. 技術與戰術": ["戰術執行", "得分效率", "風險控制"],
        "2. 體能表現": ["後段表現", "負荷承受", "爆發/速度"],
        "3. 競賽心理": ["失分後反應", "壓力下決策", "指令執行"],
        "4. 競賽準備": ["節奏適應", "風格適應", "國際經驗"]
    }

    scores = {}
    notes = {}

    for category, items in rubrics.items():
        with st.expander(f"📌 {category}", expanded=False):
            for item in items:
                scores[item] = st.select_slider(f"{item}", options=[1, 2, 3, 4, 5], value=3, key=f"s_{item}")
            notes[category] = st.text_area(f"筆記 ({category.split()[1]})", height=100)

    # 出勤與投入
    st.markdown("---")
    st.subheader("5. 出勤與投入")
    with st.expander("📊 輸入出勤數據", expanded=True):
        c1, c2 = st.columns(2)
        total = c1.number_input("應出席", value=20)
        actual = c2.number_input("實際出席", value=18)
        att_rate = (actual/total)*100 if total>0 else 0
        st.progress(min(att_rate/100, 1.0))
        st.caption(f"出席率: {att_rate:.1f}%")
        
        att_score = st.slider("出勤評分", 1, 5, 5 if att_rate>=90 else 3)
        scores["出勤率"] = att_score
        
        checks = st.multiselect("態度檢核", ["準時", "裝備齊全", "專注", "聲量", "主動"], ["準時", "裝備齊全"])
        scores["訓練態度"] = st.slider("態度評分", 1, 5, min(len(checks), 5))

    st.markdown("---")
    overall_rec = st.selectbox("整體建議", ["持續觀察", "重點培養", "需調整", "淘汰/暫停"])
    next_actions = st.text_area("下階段行動")
    
    # 提交按鈕
    submit_btn = st.form_submit_button("✅ 提交並上傳雲端 (Upload)", type="primary")

# --- 提交後處理邏輯 (連線 Google Sheets) ---
if submit_btn:
    if not athlete_name:
        st.error("⚠️ 請輸入選手姓名")
    else:
        try:
            # 1. 建立連線
            conn = st.connection("gsheets", type=GSheetsConnection)
            
            # 2. 準備本次資料
            radar_data = {
                "技術": sum([scores[k] for k in rubrics["1. 技術與戰術"]]) / 3,
                "體能": sum([scores[k] for k in rubrics["2. 體能表現"]]) / 3,
                "心理": sum([scores[k] for k in rubrics["3. 競賽心理"]]) / 3,
                "準備": sum([scores[k] for k in rubrics["4. 競賽準備"]]) / 3,
                "出勤": (att_score + scores["訓練態度"]) / 2
            }

            row_data = {
                "Date": eval_date.strftime("%Y-%m-%d"),
                "Name": athlete_name,
                "Division": age_group,
                "Gender": gender,
                "Weight": weight_cat,
                "Context": context,
                "Attendance": f"{att_rate:.1f}%",
                "Recommendation": overall_rec,
                "Next_Actions": next_actions
            }
            row_data.update(scores)
            row_data.update(notes)
            
            new_df = pd.DataFrame([row_data])

            # 3. 讀取現有資料並合併 (Append logic)
            # 注意：這裡會讀取 Sheet1，如果檔案是空的，我們會處理例外
            try:
                existing_data = conn.read(worksheet="Sheet1", ttl=0)
                existing_df = pd.DataFrame(existing_data)
                # 合併舊資料與新資料
                updated_df = pd.concat([existing_df, new_df], ignore_index=True)
            except Exception:
                # 如果是全新的空白表，直接用新資料
                updated_df = new_df

            # 4. 寫回 Google Sheets
            conn.update(worksheet="Sheet1", data=updated_df)
            
            st.success(f"🎉 成功！{athlete_name} 的資料已上傳至 Google Sheets！")
            
            # 畫圖
            df_radar = pd.DataFrame(dict(r=list(radar_data.values()), theta=list(radar_data.keys())))
            fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True, range_r=[0,5])
            fig.update_traces(fill='toself')
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"上傳失敗，請檢查網路或權限設定。\n錯誤訊息: {e}")