import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# ═══════════════════════════════════════════════════════════════════
# 🥋 TAEKWONDO ATHLETE SCORECARD (Singapore-Style Simplified)
# Qualitative observation-focused, minimal quantitative metrics
# ═══════════════════════════════════════════════════════════════════

st.set_page_config(page_title="Taekwondo Athlete Scorecard", page_icon="🥋", layout="wide")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p { font-size: 1.1em; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥋 Taekwondo Athlete Scorecard (Singapore Style)")
st.markdown("*Coaching observation-first. Data supports, not drives, decisions.*")

# --- Weight Categories ---
weight_categories = {
    "Senior (成人)": {
        "Male (男)": ["-54 kg", "-58 kg", "-63 kg", "-68 kg", "-74 kg", "-80 kg", "-87 kg", "+87 kg"],
        "Female (女)": ["-46 kg", "-49 kg", "-53 kg", "-57 kg", "-62 kg", "-67 kg", "-73 kg", "+73 kg"]
    },
    "Junior - Ages 15-17 (青少年)": {
        "Male (男)": ["-45 kg", "-48 kg", "-51 kg", "-55 kg", "-59 kg", "-63 kg", "-68 kg", "-73 kg", "-78 kg", "+78 kg"],
        "Female (女)": ["-42 kg", "-44 kg", "-46 kg", "-49 kg", "-52 kg", "-55 kg", "-59 kg", "-63 kg", "-68 kg", "+68 kg"]
    },
    "Cadet - Ages 12-14 (少年)": {
        "Male (男)": ["-33 kg", "-37 kg", "-41 kg", "-45 kg", "-49 kg", "-53 kg", "-57 kg", "-61 kg", "-65 kg", "+65 kg"],
        "Female (女)": ["-29 kg", "-33 kg", "-37 kg", "-41 kg", "-44 kg", "-47 kg", "-51 kg", "-55 kg", "-59 kg", "+59 kg"]
    }
}

# ═══════════════════════════════════════════════════════════════════
# SECTION 1: BASIC INFO
# ═══════════════════════════════════════════════════════════════════
st.header("1️⃣ Athlete Profile / 基本資料")

col1, col2, col3, col4 = st.columns(4)
with col1:
    athlete_name = st.text_input("Athlete Name (姓名)")
with col2:
    eval_date = st.date_input("Evaluation Date (評估日期)", datetime.today())
with col3:
    age_group = st.selectbox("Age Division (年齡組)", list(weight_categories.keys()))
with col4:
    gender = st.selectbox("Gender (性別)", ["Male (男)", "Female (女)"])

col5, col6, col7 = st.columns(3)
with col5:
    available_weights = weight_categories[age_group][gender]
    weight_cat = st.selectbox("Weight Category (量級)", available_weights)
with col6:
    context = st.selectbox("Context (情境)", ["Domestic (國內)", "International (國際)", "Training Camp (移訓)"])
with col7:
    eval_type = st.selectbox("Evaluation Type (評估類型)", ["Regular (定期)", "Event-based (事件導向)", "Boot camp (移訓營)"])

st.divider()

# ═══════════════════════════════════════════════════════════════════
# SECTION 2: THREE CORE ASSESSMENT AREAS
# ═══════════════════════════════════════════════════════════════════

st.header("2️⃣ Assessment / 評估")
st.markdown("*Focus on coaching observations first. Supporting evidence is secondary.*")

with st.form("assessment_form"):
    
    assessment_data = {}
    
    # ─────────────────────────────────────────────────────────────
    # A. TECHNICAL & TACTICAL EXECUTION
    # ─────────────────────────────────────────────────────────────
    st.subheader("A. Technical & Tactical Execution (技術與戰術執行)")
    st.markdown("**Focus:** Are technical choices aligned with tactics? Can athlete adjust when opponent changes tempo?")
    
    tech_observation = st.text_area(
        "Coaching Observation (教練觀察)",
        height=100,
        placeholder="Key observations: tactical consistency, technique selection, adaptation to opponent changes, technical quality under pressure...",
        key="tech_obs"
    )
    assessment_data["Technical_Observation"] = tech_observation
    
    st.markdown("**Supporting Evidence (佐證數據):**")
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        scoring_eff = st.number_input("Scoring Efficiency (%)", min_value=0, max_value=100, step=5, value=50)
        assessment_data["Scoring_Efficiency"] = scoring_eff
    with col_a2:
        counters = st.number_input("Counter-attacks Conceded (per match)", min_value=0, step=1, value=0)
        assessment_data["Counters_Conceded"] = counters
    with col_a3:
        penalties = st.number_input("Penalties Received (per match)", min_value=0, step=1, value=0)
        assessment_data["Penalties_Received"] = penalties
    
    st.divider()
    
    # ─────────────────────────────────────────────────────────────
    # B. COMPETITION BEHAVIOR & READINESS
    # ─────────────────────────────────────────────────────────────
    st.subheader("B. Competition Behavior & Readiness (競賽行為與準備度)")
    st.markdown("**Focus:** Response after score/penalty? Decision quality when behind? International tempo adaptation?")
    
    comp_observation = st.text_area(
        "Coaching Observation (教練觀察)",
        height=100,
        placeholder="Key observations: post-score reactions, decision-making when trailing, pressure response, adaptability to different opponents, international rhythm adjustment...",
        key="comp_obs"
    )
    assessment_data["Competition_Observation"] = comp_observation
    
    st.markdown("**Supporting Evidence (佐證數據):**")
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        intl_matches = st.number_input("International Matches Competed (lifetime)", min_value=0, step=1, value=0)
        assessment_data["Intl_Matches"] = intl_matches
    with col_b2:
        consistency = st.selectbox("Performance Consistency", ["High (穩定)", "Moderate (中等)", "Low (不穩定)"])
        assessment_data["Performance_Consistency"] = consistency
    with col_b3:
        pressure_response = st.selectbox("Pressure Response", ["Positive (積極)", "Neutral (中立)", "Negative (消極)"])
        assessment_data["Pressure_Response"] = pressure_response
    
    st.divider()
    
    # ─────────────────────────────────────────────────────────────
    # C. TRAINING CONTINUITY & ENGAGEMENT
    # ─────────────────────────────────────────────────────────────
    st.subheader("C. Training Continuity & Engagement (訓練連續性與投入)")
    st.markdown("**Focus:** Attendance consistency and training session quality/focus?")
    
    train_observation = st.text_area(
        "Coaching Observation (教練觀察)",
        height=100,
        placeholder="Key observations: training consistency, focus during sessions, participation in key sessions, recovery quality, training attitude, peer dynamics...",
        key="train_obs"
    )
    assessment_data["Training_Observation"] = train_observation
    
    st.markdown("**Supporting Evidence (佐證數據):**")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        total_sessions = st.number_input("Sessions Required (this period)", min_value=0, step=1, value=20)
        attended_sessions = st.number_input("Sessions Attended", min_value=0, step=1, value=18)
        att_rate = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
        assessment_data["Attendance_Rate"] = att_rate
        st.metric("Attendance Rate", f"{att_rate:.1f}%", 
                 delta="⚠️ Below 75%" if att_rate < 75 else "✅ On track")
    
    with col_c2:
        key_sessions = st.number_input("Key Sessions Attended (e.g., conditioning, technical focus)", min_value=0, step=1, value=0)
        key_total = st.number_input("Key Sessions Held", min_value=0, step=1, value=0)
        key_rate = (key_sessions / key_total * 100) if key_total > 0 else 0
        assessment_data["Key_Session_Rate"] = key_rate
        st.metric("Key Session Participation", f"{key_rate:.1f}%")
    
    st.divider()
    
    # ═════════════════════════════════════════════════════════════
    # SECTION 3: RISK FLAGS & ATHLETE STATUS
    # ═════════════════════════════════════════════════════════════
    st.header("3️⃣ Risk Assessment & Status / 風險與定位")
    
    st.subheader("⚠️ Risk Flags (風險標誌)")
    risk_options = [
        "Training Continuity Issue (訓練連續性問題)",
        "Injury/Physical Concern (傷病/身體疑慮)",
        "Inconsistent Performance (表現不穩定)",
        "Limited Int'l Exposure (缺乏國際經驗)",
        "Decision-Making Under Pressure (高壓決策能力)"
    ]
    risk_flags = st.multiselect("Select applicable risks (勾選適用風險):", risk_options)
    assessment_data["Risk_Flags"] = ", ".join(risk_flags) if risk_flags else "None"
    
    # Auto-flag based on attendance
    if att_rate < 75:
        st.warning("🚩 Training continuity below 75% - flagged automatically")
    
    st.divider()
    
    # ═════════════════════════════════════════════════════════════
    # SECTION 4: SUMMARY & NEXT STEPS
    # ═════════════════════════════════════════════════════════════
    st.header("4️⃣ Summary & Action Plan / 摘要與行動計畫")
    
    col_status1, col_status2 = st.columns([1, 2])
    
    with col_status1:
        st.subheader("Athlete Status (選手定位)")
        athlete_status = st.selectbox(
            "Current Role (目前定位)",
            ["Ready Now (即戰力)", 
             "Developing (培養中)", 
             "Long-term (長期發展)",
             "Re-assess (需重新評估)"],
            help="Based on international readiness, consistency, and preparedness"
        )
        assessment_data["Athlete_Status"] = athlete_status
    
    with col_status2:
        st.subheader("Executive Summary (整體摘要)")
        exec_summary = st.text_area(
            "1-2 sentence overview (整體摘要，1-2句)",
            height=80,
            placeholder="e.g., 'Strong tactical foundation but needs more high-intensity match exposure. Technical execution improving, consistency remains key focus for next cycle.'",
            key="exec_summary"
        )
        assessment_data["Executive_Summary"] = exec_summary
    
    st.divider()
    
    st.subheader("Next 4-8 Weeks Action Plan (未來4-8週重點行動)")
    next_actions = st.text_area(
        "Specific, time-bound actions (具體、限時的行動)",
        height=120,
        placeholder="e.g., '1) Increase international match exposure (target: 2 matches) 2) Focus on decision-making under fatigue via high-intensity conditioning 3) Participate in 100% of key technical sessions 4) Evaluate form after next competition'",
        key="next_actions"
    )
    assessment_data["Next_Actions"] = next_actions
    
    st.divider()
    
    # ─────────────────────────────────────────────────────────────
    # SUBMIT BUTTON
    # ─────────────────────────────────────────────────────────────
    submit_btn = st.form_submit_button("✅ Submit & Upload to Cloud", type="primary", use_container_width=True)

# ═══════════════════════════════════════════════════════════════════
# HANDLE SUBMISSION
# ═══════════════════════════════════════════════════════════════════

if submit_btn:
    if not athlete_name:
        st.error("⚠️ Please enter athlete name")
    else:
        try:
            # Create connection
            conn = st.connection("gsheets", type=GSheetsConnection)
            
            # Prepare data
            row_data = {
                "Date (日期)": eval_date.strftime("%Y-%m-%d"),
                "Name (姓名)": athlete_name,
                "Division (組別)": age_group,
                "Gender (性別)": gender,
                "Weight (量級)": weight_cat,
                "Context (情境)": context,
                "Eval_Type (評估類型)": eval_type,
                "Athlete_Status (定位)": athlete_status,
                "Risk_Flags (風險)": assessment_data.get("Risk_Flags", "None"),
                "Attendance_Rate (出席率%)": f"{att_rate:.1f}",
                "Key_Session_Rate (關鍵課程%)": f"{key_rate:.1f}",
                "Scoring_Efficiency (得分效率%)": scoring_eff,
                "Counters_Conceded (被反擊/場)": counters,
                "Penalties (判罰/場)": penalties,
                "Intl_Matches (國際比賽場數)": intl_matches,
                "Consistency (表現一致性)": consistency,
                "Pressure_Response (壓力反應)": pressure_response,
                "Tech_Observation (技術觀察)": tech_observation,
                "Comp_Observation (競賽觀察)": comp_observation,
                "Train_Observation (訓練觀察)": train_observation,
                "Executive_Summary (摘要)": exec_summary,
                "Next_Actions (下階段行動)": next_actions
            }
            
            new_df = pd.DataFrame([row_data])
            
            # Read & merge existing data
            try:
                existing_data = conn.read(worksheet="Sheet1", ttl=0)
                existing_df = pd.DataFrame(existing_data)
                updated_df = pd.concat([existing_df, new_df], ignore_index=True)
            except:
                updated_df = new_df
            
            # Write to Google Sheets
            conn.update(worksheet="Sheet1", data=updated_df)
            
            st.success(f"🎉 Success! {athlete_name}'s assessment uploaded to Google Sheets!")
            
            # Generate simple 3-dimensional radar chart
            tech_score = 3.5 if scoring_eff >= 50 else 2.5
            comp_score = 3.5 if consistency == "High (穩定)" else 2.5
            train_score = min(5, att_rate / 20)
            
            radar_data = pd.DataFrame({
                "dimension": ["Technical & Tactical\n(技術戰術)", "Competition Behavior\n(競賽行為)", "Training Engagement\n(訓練投入)"],
                "score": [tech_score, comp_score, train_score]
            })
            
            fig = px.line_polar(radar_data, r='score', theta='dimension', line_close=True, 
                               range_r=[0, 5], markers=True)
            fig.update_traces(fill='toself', line_color='#0288D1', fillcolor='rgba(2, 136, 209, 0.3)')
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Upload failed: {str(e)}")
