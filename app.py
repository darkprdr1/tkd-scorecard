import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import logging

# ═══════════════════════════════════════════════════════════════════
# 🥋 TAEKWONDO ATHLETE SCORECARD (Singapore) - DUAL MODE + PDF REPORT
# ═══════════════════════════════════════════════════════════════════

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Taekwondo Athlete Scorecard", page_icon="🥋", layout="wide")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p { font-size: 1.1em; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥋 Taekwondo Athlete Scorecard (Singapore)")
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
# 🎯 模式選擇
# ═══════════════════════════════════════════════════════════════════

eval_mode = st.radio(
    "📌 評估模式 (Evaluation Mode)",
    ["🥋 對打 (Sparring / Kyorugi)", "🎭 品勢 (Poomsae)"],
    horizontal=True,
    help="選擇評估類型 / Select assessment type"
)

is_sparring = "對打" in eval_mode
is_poomsae = "品勢" in eval_mode

st.divider()

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

with st.form("assessment_form"):

    assessment_data = {}

    if is_sparring:
        # ─────────────────────────────────────────────────────────────
        # 對打模式
        # ─────────────────────────────────────────────────────────────
        st.markdown("**Focus:** Tactical planning, match control, adjustment to different opponent styles, technical consistency under pressure?")

        # A. TECHNICAL & TACTICAL EXECUTION
        st.subheader("A. Technical & Tactical Execution (技術與戰術執行)")
        st.markdown("**Focus:** Tactical planning, match control, adjustment to different opponent styles, technical consistency under pressure?")

        col_tact1, col_tact2 = st.columns(2)

        with col_tact1:
            st.markdown("**Pre-Match Tactical Planning (賽前戰術規劃)**")
            pregame_tactic = st.text_area(
                "Pre-game observation",
                height=80,
                placeholder="Tactical plan clarity, opponent analysis, strategy selection, readiness...",
                key="pregame_tactic"
            )
            assessment_data["Pre_Match_Tactic"] = pregame_tactic

        with col_tact2:
            st.markdown("**In-Match Tactical Execution (比賽中戰術執行)**")
            inmatch_tactic = st.text_area(
                "In-match observation",
                height=80,
                placeholder="Tactic execution consistency, tactical adjustments, tempo response...",
                key="inmatch_tactic"
            )
            assessment_data["In_Match_Tactic"] = inmatch_tactic

        st.markdown("**Match Control & Opponent-Style Adaptation (比賽掌控與對手風格適應)**")
        tech_observation = st.text_area(
            "Coaching Observation (教練觀察)",
            height=100,
            placeholder="Match control ability, adaptation to different opponent styles (e.g., aggressive/continuous attackers vs. slow/tempo-based players), technical quality under pressure, opponent-specific adjustments...",
            key="tech_obs"
        )
        assessment_data["Technical_Observation"] = tech_observation

        st.markdown("**Supporting Evidence (佐證數據):**")
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
        with col_a1:
            scoring_eff = st.number_input("Scoring Effectiveness (%)", min_value=0, max_value=100, step=5, value=50)
            assessment_data["Scoring_Effectiveness"] = scoring_eff
        with col_a2:
            match_control = st.number_input("Match Control (1-5)", min_value=1, max_value=5, step=1, value=3)
            assessment_data["Match_Control"] = match_control
        with col_a3:
            counters = st.number_input("Counter-attacks Conceded (per match)", min_value=0, step=1, value=0)
            assessment_data["Counters_Conceded"] = counters
        with col_a4:
            penalties = st.number_input("Penalties Received (per match)", min_value=0, step=1, value=0)
            assessment_data["Penalties_Received"] = penalties

        st.divider()

        # B. COMPETITION BEHAVIOR & READINESS
        st.subheader("B. Competition Behavior & Readiness (競賽行為與準備度)")
        st.markdown("**Focus:** Response after score/penalty? Decision quality when behind? Match load tolerance under international tempo?")

        comp_observation = st.text_area(
            "Coaching Observation (教練觀察)",
            height=100,
            placeholder="Post-score reactions, decision-making when trailing, pressure response, opponent adaptation, match load tolerance (physical & mental), international rhythm adjustment...",
            key="comp_obs"
        )
        assessment_data["Competition_Observation"] = comp_observation

        st.markdown("**Supporting Evidence (佐證數據):**")
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)
        with col_b1:
            intl_matches = st.number_input("International Matches Competed (lifetime)", min_value=0, step=1, value=0)
            assessment_data["Intl_Matches"] = intl_matches
        with col_b2:
            consistency = st.selectbox("Performance Consistency", ["High (穩定)", "Moderate (中等)", "Low (不穩定)"])
            assessment_data["Performance_Consistency"] = consistency
        with col_b3:
            pressure_response = st.selectbox("Pressure Response", ["Positive (積極)", "Neutral (中立)", "Negative (消極)"])
            assessment_data["Pressure_Response"] = pressure_response
        with col_b4:
            load_tolerance = st.selectbox("Match Load Tolerance", ["High (高)", "Moderate (中等)", "Low (低)"])
            assessment_data["Match_Load_Tolerance"] = load_tolerance

        st.divider()

        # C. TRAINING CONTINUITY & ENGAGEMENT
        st.subheader("C. Training Continuity & Engagement (訓練連續性與投入)")
        st.markdown("**Focus:** Attendance consistency and training session quality/focus?")

        train_observation = st.text_area(
            "Coaching Observation (教練觀察)",
            height=100,
            placeholder="Training consistency, focus during sessions, participation in key sessions, recovery quality, training attitude, peer dynamics...",
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

    else:  # is_poomsae
        # ─────────────────────────────────────────────────────────────
        # 品勢模式
        # ─────────────────────────────────────────────────────────────
        st.markdown("**Focus:** Technical difficulty, execution quality, artistic expression, consistency, international competitiveness?")

        # A. TECHNICAL DIFFICULTY & EXECUTION
        st.subheader("A. Technical Difficulty & Execution (技術難度與執行)")
        st.markdown("**Focus:** Complexity of chosen poomsae, execution precision, power delivery, transitions?")

        col_poom1, col_poom2 = st.columns(2)

        with col_poom1:
            st.markdown("**Poomsae Selection (品勢選擇)**")
            poomsae_name = st.text_input(
                "Poomsae Name (e.g., Koryo, Kumgang, Taebaek, etc.)",
                placeholder="Enter the poomsae name...",
                key="poomsae_name"
            )
            assessment_data["Poomsae_Name"] = poomsae_name

        with col_poom2:
            st.markdown("**Technical Level (技術等級)**")
            tech_level = st.selectbox("Difficulty Level", 
                                     ["Foundation (基礎)", "Intermediate (中級)", "Advanced (高級)"],
                                     key="tech_level")
            assessment_data["Tech_Level"] = tech_level

        st.markdown("**Coaching Observation - Technical Execution (教練觀察 - 技術執行)**")
        tech_obs_poom = st.text_area(
            "Technical quality observation",
            height=100,
            placeholder="Precision, power, transitions, stances, hand techniques, footwork consistency...",
            key="tech_obs_poom"
        )
        assessment_data["Technical_Observation"] = tech_obs_poom

        st.markdown("**Supporting Evidence (佐證數據):**")
        col_poom_a1, col_poom_a2, col_poom_a3 = st.columns(3)
        with col_poom_a1:
            execution_score = st.number_input("Execution Score (1-10)", min_value=1, max_value=10, step=0.5, value=7.0)
            assessment_data["Execution_Score"] = execution_score
        with col_poom_a2:
            power_delivery = st.selectbox("Power Delivery", ["Strong (有力)", "Moderate (適中)", "Weak (無力)"])
            assessment_data["Power_Delivery"] = power_delivery
        with col_poom_a3:
            transition_quality = st.selectbox("Transition Quality", ["Smooth (流暢)", "Acceptable (可接受)", "Rough (生硬)"])
            assessment_data["Transition_Quality"] = transition_quality

        st.divider()

        # B. ARTISTIC EXPRESSION & PRESENTATION
        st.subheader("B. Artistic Expression & Presentation (藝術表現與呈現)")
        st.markdown("**Focus:** Rhythm, musicality, breathing, presence, performance quality?")

        art_obs = st.text_area(
            "Coaching Observation - Artistic Expression (教練觀察 - 藝術表現)",
            height=100,
            placeholder="Rhythm synchronization, breathing control, stage presence, focus/concentration, interpretation of poomsae meaning...",
            key="art_obs"
        )
        assessment_data["Artistic_Observation"] = art_obs

        st.markdown("**Supporting Evidence (佐證數據):**")
        col_poom_b1, col_poom_b2, col_poom_b3 = st.columns(3)
        with col_poom_b1:
            rhythm_score = st.number_input("Rhythm & Musicality (1-10)", min_value=1, max_value=10, step=0.5, value=7.0)
            assessment_data["Rhythm_Score"] = rhythm_score
        with col_poom_b2:
            presence = st.selectbox("Stage Presence", ["Excellent (優異)", "Good (良好)", "Fair (一般)"])
            assessment_data["Stage_Presence"] = presence
        with col_poom_b3:
            focus = st.selectbox("Focus & Concentration", ["Excellent (優異)", "Good (良好)", "Fair (一般)"])
            assessment_data["Focus_Concentration"] = focus

        st.divider()

        # C. CONSISTENCY & RELIABILITY
        st.subheader("C. Consistency & Reliability (穩定性與可靠性)")
        st.markdown("**Focus:** Training consistency, performance stability across different contexts?")

        consist_obs = st.text_area(
            "Coaching Observation - Consistency (教練觀察 - 穩定性)",
            height=100,
            placeholder="Training participation, performance variability, mistake frequency, psychological resilience...",
            key="consist_obs"
        )
        assessment_data["Consistency_Observation"] = consist_obs

        st.markdown("**Supporting Evidence (佐證數據):**")
        col_poom_c1, col_poom_c2, col_poom_c3 = st.columns(3)
        with col_poom_c1:
            total_sessions = st.number_input("Training Sessions (this period)", min_value=0, step=1, value=20)
            attended_sessions = st.number_input("Sessions Attended", min_value=0, step=1, value=18)
            att_rate = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
            assessment_data["Attendance_Rate"] = att_rate
            st.metric("Attendance Rate", f"{att_rate:.1f}%")
        with col_poom_c2:
            consistency = st.selectbox("Performance Consistency", ["High (穩定)", "Moderate (中等)", "Low (不穩定)"])
            assessment_data["Performance_Consistency"] = consistency
        with col_poom_c3:
            mistake_frequency = st.selectbox("Mistake Frequency", ["Rare (罕見)", "Occasional (偶爾)", "Frequent (頻繁)"])
            assessment_data["Mistake_Frequency"] = mistake_frequency

        st.divider()

        # D. INTERNATIONAL COMPETITIVENESS
        st.subheader("D. International Competitiveness (國際競爭力)")

        intl_comp = st.text_area(
            "Coaching Observation - International Readiness (教練觀察 - 國際準備度)",
            height=80,
            placeholder="Readiness for international competition, comparison to regional/international standards...",
            key="intl_comp"
        )
        assessment_data["Intl_Readiness"] = intl_comp

        st.markdown("**Supporting Evidence (佐證數據):**")
        col_poom_d1, col_poom_d2 = st.columns(2)
        with col_poom_d1:
            intl_competitions = st.number_input("International Competitions (lifetime)", min_value=0, step=1, value=0)
            assessment_data["Intl_Competitions"] = intl_competitions
        with col_poom_d2:
            best_ranking = st.text_input("Best International Ranking (if any)", placeholder="e.g., 5th place at Asian Games", value="")
            assessment_data["Best_Ranking"] = best_ranking

        st.divider()

    # ═══════════════════════════════════════════════════════════════════
    # SHARED SECTION: RISK ASSESSMENT
    # ═══════════════════════════════════════════════════════════════════
    st.header("3️⃣ Risk Assessment & Status / 風險與定位")

    st.subheader("⚠️ Risk Flags (風險標誌)")

    if is_sparring:
        risk_options = [
            "Training Continuity Issue (訓練連續性問題)",
            "Injury/Physical Concern (傷病/身體疑慮)",
            "Inconsistent Performance (表現不穩定)",
            "Limited Int'l Exposure (缺乏國際經驗)",
            "Decision-Making Under Pressure (高壓決策能力)",
            "Opponent-Style Adaptation (對手風格適應)"
        ]
    else:  # is_poomsae
        risk_options = [
            "Training Continuity Issue (訓練連續性問題)",
            "Injury/Physical Concern (傷病/身體疑慮)",
            "Inconsistent Performance (表現不穩定)",
            "Limited Int'l Exposure (缺乏國際經驗)",
            "Artistic Expression Gaps (藝術表現差距)",
            "Execution Precision Issues (執行精準度問題)"
        ]

    risk_flags = st.multiselect("Select applicable risks (勾選適用風險):", risk_options)
    assessment_data["Risk_Flags"] = ", ".join(risk_flags) if risk_flags else "None"

    # Auto-flag based on attendance
    if att_rate < 75:
        st.warning("🚩 Training continuity below 75% - flagged automatically")

    st.divider()

    # ═══════════════════════════════════════════════════════════════════
    # SHARED SECTION: SUMMARY & ACTION PLAN
    # ═══════════════════════════════════════════════════════════════════
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
            help="Based on readiness, consistency, and preparedness"
        )
        assessment_data["Athlete_Status"] = athlete_status

    with col_status2:
        st.subheader("Executive Summary (整體摘要)")
        exec_summary = st.text_area(
            "1-2 sentence overview (整體摘要，1-2句)",
            height=80,
            placeholder="e.g., 'Strong technical execution with good power delivery. Artistic expression needs refinement. Consistent training participation.'",
            key="exec_summary"
        )
        assessment_data["Executive_Summary"] = exec_summary

    st.divider()

    st.subheader("Next 4-8 Weeks Action Plan (未來4-8週重點行動)")
    next_actions = st.text_area(
        "Specific, time-bound actions (具體、限時的行動)",
        height=120,
        placeholder="e.g., '1) Strengthen power delivery through resistance training 2) Work on rhythm synchronization with music 3) Increase international competition exposure 4) Focus on consistency in technical execution'",
        key="next_actions"
    )
    assessment_data["Next_Actions"] = next_actions

    st.divider()

    # SUBMIT BUTTON
    col_submit1, col_submit2 = st.columns(2)
    with col_submit1:
        submit_btn = st.form_submit_button("✅ Submit & Upload to Cloud", type="primary", use_container_width=True)
    with col_submit2:
        download_btn = st.form_submit_button("📄 Download Report (PDF)", type="secondary", use_container_width=True)

# ═══════════════════════════════════════════════════════════════════
# HELPER: 生成 PDF 報告
# ═══════════════════════════════════════════════════════════════════

def generate_pdf_report(athlete_info, assessment_data, is_sparring):
    """生成專業的 PDF 報告"""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)

    # 設定樣式
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f4e78'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2e5c8a'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderColor=colors.HexColor('#d0d0d0'),
        borderWidth=1,
        borderPadding=4
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY
    )

    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#555555'),
        fontName='Helvetica-Bold'
    )

    # 文檔內容
    elements = []

    # --- 標題 ---
    elements.append(Paragraph("🥋 TAEKWONDO ATHLETE ASSESSMENT REPORT", title_style))
    elements.append(Paragraph(f"跆拳道選手評估報告", title_style))
    elements.append(Spacer(1, 0.15*inch))

    # --- 基本信息表格 ---
    athlete_table_data = [
        [Paragraph("<b>Name / 姓名</b>", label_style), athlete_info['athlete_name']],
        [Paragraph("<b>Evaluation Date / 評估日期</b>", label_style), athlete_info['eval_date'].strftime('%Y-%m-%d')],
        [Paragraph("<b>Age Division / 年齡組</b>", label_style), athlete_info['age_group']],
        [Paragraph("<b>Gender / 性別</b>", label_style), athlete_info['gender']],
        [Paragraph("<b>Weight Category / 量級</b>", label_style), athlete_info['weight_cat']],
        [Paragraph("<b>Context / 情境</b>", label_style), athlete_info['context']],
        [Paragraph("<b>Evaluation Type / 評估類型</b>", label_style), athlete_info['eval_type']],
        [Paragraph("<b>Mode / 評估模式</b>", label_style), "Sparring (對打)" if is_sparring else "Poomsae (品勢)"],
    ]

    athlete_table = Table(athlete_table_data, colWidths=[2*inch, 3*inch])
    athlete_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f7')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))

    elements.append(athlete_table)
    elements.append(Spacer(1, 0.2*inch))

    # --- 評估內容 ---
    if is_sparring:
        # 對打評估
        elements.append(Paragraph("SPARRING ASSESSMENT (對打評估)", heading_style))

        # A. Technical & Tactical
        elements.append(Paragraph("A. TECHNICAL & TACTICAL EXECUTION (技術與戰術執行)", heading_style))
        elements.append(Paragraph("<b>Pre-Match Tactical Planning:</b>", body_style))
        elements.append(Paragraph(assessment_data.get('Pre_Match_Tactic', 'N/A'), body_style))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(Paragraph("<b>In-Match Tactical Execution:</b>", body_style))
        elements.append(Paragraph(assessment_data.get('In_Match_Tactic', 'N/A'), body_style))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(Paragraph("<b>Coaching Observation:</b>", body_style))
        elements.append(Paragraph(assessment_data.get('Technical_Observation', 'N/A'), body_style))
        elements.append(Spacer(1, 0.1*inch))

        # 數據表格
        tech_table_data = [
            [Paragraph("<b>Metric / 指標</b>", label_style), Paragraph("<b>Value / 數值</b>", label_style)],
            ["Scoring Effectiveness / 得分效率 (%)", f"{assessment_data.get('Scoring_Effectiveness', 'N/A')}%"],
            ["Match Control / 比賽掌控 (1-5)", str(assessment_data.get('Match_Control', 'N/A'))],
            ["Counter-attacks Conceded / 被反擊 (per match)", str(assessment_data.get('Counters_Conceded', 'N/A'))],
            ["Penalties Received / 判罰 (per match)", str(assessment_data.get('Penalties_Received', 'N/A'))],
        ]
        tech_table = Table(tech_table_data, colWidths=[2.5*inch, 2.5*inch])
        tech_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(tech_table)
        elements.append(Spacer(1, 0.15*inch))

        # B. Competition Behavior
        elements.append(Paragraph("B. COMPETITION BEHAVIOR & READINESS (競賽行為與準備度)", heading_style))
        elements.append(Paragraph("<b>Coaching Observation:</b>", body_style))
        elements.append(Paragraph(assessment_data.get('Competition_Observation', 'N/A'), body_style))
        elements.append(Spacer(1, 0.1*inch))

        comp_table_data = [
            [Paragraph("<b>Metric / 指標</b>", label_style), Paragraph("<b>Value / 數值</b>", label_style)],
            ["International Matches / 國際比賽", str(assessment_data.get('Intl_Matches', 'N/A'))],
            ["Performance Consistency / 表現穩定性", str(assessment_data.get('Performance_Consistency', 'N/A'))],
            ["Pressure Response / 壓力反應", str(assessment_data.get('Pressure_Response', 'N/A'))],
            ["Match Load Tolerance / 比賽負荷承受", str(assessment_data.get('Match_Load_Tolerance', 'N/A'))],
        ]
        comp_table = Table(comp_table_data, colWidths=[2.5*inch, 2.5*inch])
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(comp_table)
        elements.append(Spacer(1, 0.15*inch))

        # C. Training Continuity
        elements.append(Paragraph("C. TRAINING CONTINUITY & ENGAGEMENT (訓練連續性與投入)", heading_style))
        elements.append(Paragraph("<b>Coaching Observation:</b>", body_style))
        elements.append(Paragraph(assessment_data.get('Training_Observation', 'N/A'), body_style))
        elements.append(Spacer(1, 0.1*inch))

        train_table_data = [
            [Paragraph("<b>Metric / 指標</b>", label_style), Paragraph("<b>Value / 數值</b>", label_style)],
            ["Attendance Rate / 出席率", f"{assessment_data.get('Attendance_Rate', 0):.1f}%"],
            ["Key Session Participation / 關鍵課程參與", f"{assessment_data.get('Key_Session_Rate', 0):.1f}%"],
        ]
        train_table = Table(train_table_data, colWidths=[2.5*inch, 2.5*inch])
        train_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(train_table)

    else:  # Poomsae
        # 品勢評估
        elements.append(Paragraph("POOMSAE ASSESSMENT (品勢評估)", heading_style))

        # A. Technical Difficulty & Execution
        elements.append(Paragraph("A. TECHNICAL DIFFICULTY & EXECUTION (技術難度與執行)", heading_style))
        elements.append(Paragraph(f"<b>Poomsae Name:</b> {assessment_data.get('Poomsae_Name', 'N/A')}", body_style))
        elements.append(Paragraph(f"<b>Technical Level:</b> {assessment_data.get('Tech_Level', 'N/A')}", body_style))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(Paragraph("<b>Coaching Observation:</b>", body_style))
        elements.append(Paragraph(assessment_data.get('Technical_Observation', 'N/A'), body_style))
        elements.append(Spacer(1, 0.1*inch))

        poom_tech_data = [
            [Paragraph("<b>Metric / 指標</b>", label_style), Paragraph("<b>Value / 數值</b>", label_style)],
            ["Execution Score / 執行分數 (1-10)", str(assessment_data.get('Execution_Score', 'N/A'))],
            ["Power Delivery / 力度表現", str(assessment_data.get('Power_Delivery', 'N/A'))],
            ["Transition Quality / 轉換品質", str(assessment_data.get('Transition_Quality', 'N/A'))],
        ]
        poom_tech_table = Table(poom_tech_data, colWidths=[2.5*inch, 2.5*inch])
        poom_tech_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(poom_tech_table)
        elements.append(Spacer(1, 0.15*inch))

        # B. Artistic Expression
        elements.append(Paragraph("B. ARTISTIC EXPRESSION & PRESENTATION (藝術表現與呈現)", heading_style))
        elements.append(Paragraph("<b>Coaching Observation:</b>", body_style))
        elements.append(Paragraph(assessment_data.get('Artistic_Observation', 'N/A'), body_style))
        elements.append(Spacer(1, 0.1*inch))

        poom_art_data = [
            [Paragraph("<b>Metric / 指標</b>", label_style), Paragraph("<b>Value / 數值</b>", label_style)],
            ["Rhythm & Musicality / 節奏與音樂性 (1-10)", str(assessment_data.get('Rhythm_Score', 'N/A'))],
            ["Stage Presence / 舞台表現", str(assessment_data.get('Stage_Presence', 'N/A'))],
            ["Focus & Concentration / 專注力", str(assessment_data.get('Focus_Concentration', 'N/A'))],
        ]
        poom_art_table = Table(poom_art_data, colWidths=[2.5*inch, 2.5*inch])
        poom_art_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(poom_art_table)
        elements.append(Spacer(1, 0.15*inch))

        # C. Consistency & Reliability
        elements.append(Paragraph("C. CONSISTENCY & RELIABILITY (穩定性與可靠性)", heading_style))
        elements.append(Paragraph("<b>Coaching Observation:</b>", body_style))
        elements.append(Paragraph(assessment_data.get('Consistency_Observation', 'N/A'), body_style))
        elements.append(Spacer(1, 0.1*inch))

        poom_cons_data = [
            [Paragraph("<b>Metric / 指標</b>", label_style), Paragraph("<b>Value / 數值</b>", label_style)],
            ["Attendance Rate / 出席率", f"{assessment_data.get('Attendance_Rate', 0):.1f}%"],
            ["Performance Consistency / 表現穩定性", str(assessment_data.get('Performance_Consistency', 'N/A'))],
            ["Mistake Frequency / 失誤頻率", str(assessment_data.get('Mistake_Frequency', 'N/A'))],
        ]
        poom_cons_table = Table(poom_cons_data, colWidths=[2.5*inch, 2.5*inch])
        poom_cons_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(poom_cons_table)
        elements.append(Spacer(1, 0.15*inch))

        # D. International Competitiveness
        elements.append(Paragraph("D. INTERNATIONAL COMPETITIVENESS (國際競爭力)", heading_style))
        elements.append(Paragraph("<b>Coaching Observation:</b>", body_style))
        elements.append(Paragraph(assessment_data.get('Intl_Readiness', 'N/A'), body_style))
        elements.append(Spacer(1, 0.1*inch))

        intl_data = [
            [Paragraph("<b>Metric / 指標</b>", label_style), Paragraph("<b>Value / 數值</b>", label_style)],
            ["International Competitions / 國際比賽", str(assessment_data.get('Intl_Competitions', 'N/A'))],
            ["Best Ranking / 最佳排名", str(assessment_data.get('Best_Ranking', 'N/A'))],
        ]
        intl_table = Table(intl_data, colWidths=[2.5*inch, 2.5*inch])
        intl_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(intl_table)

    elements.append(PageBreak())

    # --- 風險與定位 ---
    elements.append(Paragraph("RISK ASSESSMENT & STATUS (風險與定位)", heading_style))
    elements.append(Paragraph(f"<b>Risk Flags / 風險標誌:</b> {assessment_data.get('Risk_Flags', 'None')}", body_style))
    elements.append(Paragraph(f"<b>Athlete Status / 選手定位:</b> {athlete_info['athlete_status']}", body_style))
    elements.append(Spacer(1, 0.15*inch))

    # --- 摘要與行動計畫 ---
    elements.append(Paragraph("EXECUTIVE SUMMARY & ACTION PLAN (摘要與行動計畫)", heading_style))
    elements.append(Paragraph("<b>Executive Summary / 整體摘要:</b>", body_style))
    elements.append(Paragraph(athlete_info['exec_summary'], body_style))
    elements.append(Spacer(1, 0.1*inch))

    elements.append(Paragraph("<b>Next 4-8 Weeks Action Plan / 未來4-8週重點行動:</b>", body_style))
    elements.append(Paragraph(athlete_info['next_actions'], body_style))
    elements.append(Spacer(1, 0.1*inch))

    # --- 頁尾 ---
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(f"<i>Report generated on {date.today().strftime('%Y-%m-%d')}</i>", styles['Normal']))

    # 生成 PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ═══════════════════════════════════════════════════════════════════
# HANDLE SUBMISSION
# ═══════════════════════════════════════════════════════════════════

if submit_btn or download_btn:
    # 驗證
    if not athlete_name:
        st.error("⚠️ Please enter athlete name")
        st.stop()

    # 準備共同的 athlete_info
    athlete_info = {
        'athlete_name': athlete_name,
        'eval_date': eval_date,
        'age_group': age_group,
        'gender': gender,
        'weight_cat': weight_cat,
        'context': context,
        'eval_type': eval_type,
        'athlete_status': athlete_status,
        'exec_summary': exec_summary,
        'next_actions': next_actions,
    }

    assessment_data["Eval_Mode"] = "對打 (Sparring)" if is_sparring else "品勢 (Poomsae)"
    assessment_data["Athlete_Status"] = athlete_status
    assessment_data["Risk_Flags"] = assessment_data.get("Risk_Flags", "None")

    if download_btn:
        # 下載 PDF
        try:
            pdf_buffer = generate_pdf_report(athlete_info, assessment_data, is_sparring)

            filename = f"{athlete_name}_Assessment_{eval_date.strftime('%Y%m%d')}.pdf"
            st.download_button(
                label="📥 Click to Download PDF Report",
                data=pdf_buffer.getvalue(),
                file_name=filename,
                mime="application/pdf",
                key="pdf_download"
            )
            st.success(f"✅ PDF Report ready! Filename: {filename}")

        except Exception as e:
            st.error(f"❌ PDF generation failed: {str(e)}")
            logger.error(f"PDF generation error: {str(e)}", exc_info=True)

    if submit_btn:
        # 上傳到 Google Sheets
        with st.spinner("🔄 Uploading to Google Sheets..."):
            try:
                logger.info("Attempting to establish Google Sheets connection...")
                conn = st.connection("gsheets", type=GSheetsConnection)
                logger.info("✅ Connection established successfully")

                # 準備數據
                row_data = {
                    "Date (日期)": eval_date.strftime("%Y-%m-%d"),
                    "Name (姓名)": athlete_name,
                    "Division (組別)": age_group,
                    "Gender (性別)": gender,
                    "Weight (量級)": weight_cat,
                    "Context (情境)": context,
                    "Eval_Type (評估類型)": eval_type,
                    "Eval_Mode (評估模式)": assessment_data["Eval_Mode"],
                    "Athlete_Status (定位)": athlete_status,
                    "Risk_Flags (風險)": assessment_data.get("Risk_Flags", "None"),
                    "Attendance_Rate (出席率%)": f"{att_rate:.1f}",
                    "Executive_Summary (摘要)": exec_summary,
                    "Next_Actions (下階段行動)": next_actions,
                }

                # 根據模式加入對應的欄位
                if is_sparring:
                    row_data.update({
                        "Pre_Match_Tactic (賽前戰術)": assessment_data.get("Pre_Match_Tactic", ""),
                        "In_Match_Tactic (比賽中戰術)": assessment_data.get("In_Match_Tactic", ""),
                        "Tech_Observation (技術觀察)": assessment_data.get("Technical_Observation", ""),
                        "Scoring_Effectiveness (得分效率%)": scoring_eff,
                        "Match_Control (比賽掌控)": match_control,
                        "Counters_Conceded (被反擊/場)": counters,
                        "Penalties (判罰/場)": penalties,
                        "Intl_Matches (國際比賽場數)": intl_matches,
                        "Consistency (表現一致性)": consistency,
                        "Pressure_Response (壓力反應)": pressure_response,
                        "Match_Load_Tolerance (比賽負荷承受)": load_tolerance,
                        "Comp_Observation (競賽觀察)": comp_observation,
                        "Train_Observation (訓練觀察)": train_observation,
                        "Key_Session_Rate (關鍵課程%)": f"{key_rate:.1f}",
                    })
                else:  # Poomsae
                    row_data.update({
                        "Poomsae_Name (品勢名稱)": poomsae_name,
                        "Tech_Level (技術等級)": tech_level,
                        "Tech_Observation (技術執行觀察)": tech_obs_poom,
                        "Execution_Score (執行分數)": execution_score,
                        "Power_Delivery (力度表現)": power_delivery,
                        "Transition_Quality (轉換品質)": transition_quality,
                        "Art_Observation (藝術表現觀察)": art_obs,
                        "Rhythm_Score (節奏分數)": rhythm_score,
                        "Stage_Presence (舞台表現)": presence,
                        "Focus_Concentration (專注力)": focus,
                        "Consist_Observation (穩定性觀察)": consist_obs,
                        "Performance_Consistency (表現穩定性)": consistency,
                        "Mistake_Frequency (失誤頻率)": mistake_frequency,
                        "Intl_Readiness (國際準備度)": intl_comp,
                        "Intl_Competitions (國際比賽場數)": intl_competitions,
                        "Best_Ranking (最佳排名)": best_ranking,
                    })

                # 創建新數據框
                new_df = pd.DataFrame([row_data])
                logger.info(f"New data prepared: {new_df.shape}")

                # 讀取現有數據
                try:
                    logger.info("Attempting to read existing data from Google Sheets...")
                    existing_data = conn.read(worksheet="sheet1", ttl=0)

                    if isinstance(existing_data, list):
                        if len(existing_data) > 0:
                            existing_df = pd.DataFrame(existing_data)
                            logger.info(f"Existing data loaded: {existing_df.shape}")
                        else:
                            existing_df = pd.DataFrame()
                            logger.info("Sheet is empty, creating new")
                    else:
                        existing_df = existing_data
                        logger.info(f"Existing data loaded: {existing_df.shape}")

                    # 合併數據
                    if len(existing_df) > 0:
                        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                        logger.info(f"Data merged: {updated_df.shape}")
                    else:
                        updated_df = new_df
                        logger.info("Using new data as first entry")

                except Exception as read_error:
                    logger.warning(f"Could not read existing data: {str(read_error)}. Using new data only.")
                    updated_df = new_df

                # 上傳
                logger.info("Uploading data to Google Sheets...")
                conn.update(worksheet="sheet1", data=updated_df)
                logger.info("✅ Data uploaded successfully!")

                st.success(f"🎉 Success! {athlete_name}'s assessment uploaded to Google Sheets!")
                st.balloons()

            except KeyError as e:
                st.error(f"❌ Configuration Error: {str(e)}")
                st.info("""
                **請檢查以下項目：**

                1. 確認 `.streamlit/secrets.toml` 已創建並包含正確的 `[connections.gsheets]` 配置
                2. 檢查 Google Sheet ID 是否正確
                3. 確認已分享 Google Sheet 給 Service Account
                4. 本地測試：`streamlit secrets show`
                """)
                logger.error(f"KeyError: {str(e)}")

            except Exception as e:
                st.error(f"❌ Upload failed: {str(e)}")
                st.info("""
                **常見問題排查：**

                - **錯誤：Worksheet not found** → 檢查工作表名稱（確認為 "sheet1"）
                - **錯誤：Authentication failed** → 確認 Service Account 已獲得編輯權限
                - **錯誤：Connection timeout** → 檢查網絡連接

                詳見文檔：https://docs.streamlit.io/develop/tutorials/databases/private-gsheet
                """)
                logger.error(f"Exception occurred: {str(e)}", exc_info=True)
