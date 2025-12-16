import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from streamlit_gsheets import GSheetsConnection  # Import Google Sheets connection module

# 1. Page Configuration
st.set_page_config(page_title="Taekwondo Athlete Scorecard", page_icon="🥋", layout="centered")

# CSS Optimization
st.markdown("""
    <style>
    .stSlider [data-baseweb="slider"] { margin-top: -15px; }
    .stRadio [role="radiogroup"] { flex-direction: row; overflow-x: auto; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥋 Taekwondo Athlete Scorecard (Cloud Sync)")

# --- Weight Categories Definition ---
weight_categories = {
    "Senior (成人)": {
        "Male (男)": ["-54 kg", "-58 kg", "-63 kg", "-68 kg", "-74 kg", "-80 kg", "-87 kg", "+87 kg"],
        "Female (女)": ["-46 kg", "-49 kg", "-53 kg", "-57 kg", "-62 kg", "-67 kg", "-73 kg", "+73 kg"]
    },
    "Junior - Ages 15-17 (青少年 15-17歲)": {
        "Male (男)": ["-45 kg", "-48 kg", "-51 kg", "-55 kg", "-59 kg", "-63 kg", "-68 kg", "-73 kg", "-78 kg", "+78 kg"],
        "Female (女)": ["-42 kg", "-44 kg", "-46 kg", "-49 kg", "-52 kg", "-55 kg", "-59 kg", "-63 kg", "-68 kg", "+68 kg"]
    },
    "Cadet - Ages 12-14 (少年 12-14歲)": {
        "Male (男)": ["-33 kg", "-37 kg", "-41 kg", "-45 kg", "-49 kg", "-53 kg", "-57 kg", "-61 kg", "-65 kg", "+65 kg"],
        "Female (女)": ["-29 kg", "-33 kg", "-37 kg", "-41 kg", "-44 kg", "-47 kg", "-51 kg", "-55 kg", "-59 kg", "+59 kg"]
    }
}

# --- Basic Information ---
st.subheader("📋 Basic Information / 基本資料")
col1, col2 = st.columns(2)
with col1:
    athlete_name = st.text_input("Athlete Name (選手姓名)")
with col2:
    eval_date = st.date_input("Evaluation Date (評估日期)", datetime.today())

col_age, col_gender = st.columns(2)
with col_age:
    age_group = st.selectbox("Age Division (年齡組別)", list(weight_categories.keys()))
with col_gender:
    gender = st.radio("Gender (性別)", ["Male (男)", "Female (女)"], horizontal=True)

available_weights = weight_categories[age_group][gender]
weight_cat = st.selectbox("Weight Category (量級)", available_weights)
context = st.radio("Context (情境)", ["Domestic (國內)", "International (國際)", "Training Camp (移訓)"], horizontal=True)

st.markdown("---")

# --- Scoring Form ---
with st.form("scorecard_form"):
    st.info("After completing the form, click the 'Submit' button at the bottom. Data will be automatically uploaded to Google Sheets. / 填寫完畢後，請點擊底部的「提交」按鈕，資料將自動上傳 Google Sheets。")

    rubrics = {
        "1. Technique & Tactics (技術與戰術)": ["Tactical Execution (戰術執行)", "Scoring Efficiency (得分效率)", "Risk Control (風險控制)"],
        "2. Physical Performance (體能表現)": ["End-Game Performance (後段表現)", "Load Tolerance (負荷承受)", "Explosiveness/Speed (爆發/速度)"],
        "3. Competition Psychology (競賽心理)": ["Response to Scoring Loss (失分後反應)", "Decision-Making Under Pressure (壓力下決策)", "Instruction Execution (指令執行)"],
        "4. Competition Preparation (競賽準備)": ["Rhythm Adaptation (節奏適應)", "Style Adaptation (風格適應)", "International Experience (國際經驗)"]
    }

    scores = {}
    notes = {}

    for category, items in rubrics.items():
        with st.expander(f"📌 {category}", expanded=False):
            for item in items:
                scores[item] = st.select_slider(f"{item}", options=[1, 2, 3, 4, 5], value=3, key=f"s_{item}")
            notes[category] = st.text_area(f"Notes ({category.split()[0]})", height=100)

    # Attendance & Engagement
    st.markdown("---")
    st.subheader("5. Attendance & Engagement (出勤與投入)")
    with st.expander("📊 Input Attendance Data (輸入出勤數據)", expanded=True):
        c1, c2 = st.columns(2)
        total = c1.number_input("Expected Attendance (應出席)", value=20)
        actual = c2.number_input("Actual Attendance (實際出席)", value=18)
        att_rate = (actual/total)*100 if total>0 else 0
        st.progress(min(att_rate/100, 1.0))
        st.caption(f"Attendance Rate (出席率): {att_rate:.1f}%")
        
        att_score = st.slider("Attendance Score (出勤評分)", 1, 5, 5 if att_rate>=90 else 3)
        scores["Attendance (出勤率)"] = att_score
        
        checks = st.multiselect("Attitude Checklist (態度檢核)", 
                               ["Punctuality (準時)", "Equipment Complete (裝備齊全)", "Focus (專注)", "Voice/Participation (聲量)", "Initiative (主動)"], 
                               ["Punctuality (準時)", "Equipment Complete (裝備齊全)"])
        scores["Training Attitude (訓練態度)"] = st.slider("Attitude Score (態度評分)", 1, 5, min(len(checks), 5))

    st.markdown("---")
    overall_rec = st.selectbox("Overall Recommendation (整體建議)", 
                              ["Continue Observation (持續觀察)", "Key Development (重點培養)", "Needs Adjustment (需調整)", "Discontinue/Pause (淘汰/暫停)"])
    next_actions = st.text_area("Next Steps/Action Items (下階段行動)")
    
    # Submit Button
    submit_btn = st.form_submit_button("✅ Submit & Upload to Cloud (提交並上傳雲端)", type="primary")

# --- Post-Submission Logic (Connect to Google Sheets) ---
if submit_btn:
    if not athlete_name:
        st.error("⚠️ Please enter the athlete's name (請輸入選手姓名)")
    else:
        try:
            # 1. Establish connection
            conn = st.connection("gsheets", type=GSheetsConnection)
            
            # 2. Prepare current session data
            radar_data = {
                "Technique (技術)": sum([scores[k] for k in rubrics["1. Technique & Tactics (技術與戰術)"]]) / 3,
                "Physical (體能)": sum([scores[k] for k in rubrics["2. Physical Performance (體能表現)"]]) / 3,
                "Psychology (心理)": sum([scores[k] for k in rubrics["3. Competition Psychology (競賽心理)"]]) / 3,
                "Preparation (準備)": sum([scores[k] for k in rubrics["4. Competition Preparation (競賽準備)"]]) / 3,
                "Attendance (出勤)": (att_score + scores["Training Attitude (訓練態度)"]) / 2
            }

            row_data = {
                "Date (日期)": eval_date.strftime("%Y-%m-%d"),
                "Name (姓名)": athlete_name,
                "Division (組別)": age_group,
                "Gender (性別)": gender,
                "Weight (量級)": weight_cat,
                "Context (情境)": context,
                "Attendance Rate (出席率)": f"{att_rate:.1f}%",
                "Recommendation (建議)": overall_rec,
                "Next_Actions (下階段行動)": next_actions
            }
            row_data.update(scores)
            row_data.update(notes)
            
            new_df = pd.DataFrame([row_data])

            # 3. Read existing data and merge (Append logic)
            # Note: This reads from Sheet1; if the file is empty, we handle the exception
            try:
                existing_data = conn.read(worksheet="Sheet1", ttl=0)
                existing_df = pd.DataFrame(existing_data)
                # Merge old data with new data
                updated_df = pd.concat([existing_df, new_df], ignore_index=True)
            except Exception:
                # If it's a brand new empty sheet, use new data directly
                updated_df = new_df

            # 4. Write back to Google Sheets
            conn.update(worksheet="Sheet1", data=updated_df)
            
            st.success(f"🎉 Success! {athlete_name}'s data has been uploaded to Google Sheets! / 成功！{athlete_name} 的資料已上傳至 Google Sheets！")
            
            # Generate radar chart
            df_radar = pd.DataFrame(dict(r=list(radar_data.values()), theta=list(radar_data.keys())))
            fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True, range_r=[0,5])
            fig.update_traces(fill='toself')
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Upload failed. Please check your internet connection or permissions. / 上傳失敗，請檢查網路或權限設定。\nError Message (錯誤訊息): {e}")
