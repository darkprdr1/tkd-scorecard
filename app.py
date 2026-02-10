import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import logging
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from datetime import date

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

        # C. ATHLETE STATUS & RISK
        st.subheader("C. Athlete Status & Injury/Risk Flags (選手狀態與受傷/風險旗標)")
        st.markdown("**Focus:** Any physical/mental health concerns? Red flags that may impact performance or safety?")

        health_observation = st.text_area(
            "Health & Injury Status (健康與受傷狀態)",
            height=100,
            placeholder="Current injuries, fatigue level, mental state, recovery status, pain locations, areas of weakness...",
            key="health_obs"
        )
        assessment_data["Health_Status"] = health_observation

        st.markdown("**Risk Flags (風險旗標):**")
        col_c1, col_c2, col_c3 = st.columns(3)

        with col_c1:
            injury_flag = st.selectbox("Injury Risk", ["None (無)", "Minor (輕微)", "Moderate (中等)", "High (高)"])
            assessment_data["Injury_Risk"] = injury_flag

        with col_c2:
            fatigue_flag = st.selectbox("Fatigue Level", ["Low (低)", "Moderate (中等)", "High (高)", "Critical (嚴重)"])
            assessment_data["Fatigue_Level"] = fatigue_flag

        with col_c3:
            mental_flag = st.selectbox("Mental Status", ["Positive (積極)", "Stable (穩定)", "Concerned (擔憂)"])
            assessment_data["Mental_Status"] = mental_flag

    else:

        # ─────────────────────────────────────────────────────────────
        # 品勢模式
        # ─────────────────────────────────────────────────────────────

        # A. POOMSAE TECHNICAL EXECUTION
        st.subheader("A. Poomsae Technical Execution (品勢技術執行)")
        st.markdown("**Focus:** Form accuracy, power delivery, stance stability, movement precision, rhythm consistency?")

        col_tact1, col_tact2 = st.columns(2)

        with col_tact1:
            st.markdown("**Form Accuracy & Technique Quality (套路準確性與技術品質)**")
            form_accuracy = st.text_area(
                "Form observation",
                height=80,
                placeholder="Form sequence accuracy, stance depth, hand technique precision, foot placement, body alignment...",
                key="form_accuracy"
            )
            assessment_data["Form_Accuracy"] = form_accuracy

        with col_tact2:
            st.markdown("**Power & Delivery (力量與表達)**")
            power_delivery = st.text_area(
                "Power observation",
                height=80,
                placeholder="Kick height and power, hand speed and impact, punch crisp-ness, overall dynamic energy...",
                key="power_delivery"
            )
            assessment_data["Power_Delivery"] = power_delivery

        st.markdown("**Movement Flow & Rhythm Consistency (動作流暢性與節奏一致性)**")
        tech_observation = st.text_area(
            "Coaching Observation (教練觀察)",
            height=100,
            placeholder="Transition smoothness, weight shift efficiency, balance recovery, rhythm consistency, transitions between techniques...",
            key="poomsae_obs"
        )
        assessment_data["Technical_Observation"] = tech_observation

        st.markdown("**Supporting Evidence (佐證數據):**")
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)

        with col_a1:
            accuracy_score = st.number_input("Technical Accuracy (1-10)", min_value=1, max_value=10, step=1, value=5)
            assessment_data["Accuracy_Score"] = accuracy_score

        with col_a2:
            power_score = st.number_input("Power Level (1-10)", min_value=1, max_value=10, step=1, value=5)
            assessment_data["Power_Score"] = power_score

        with col_a3:
            flow_score = st.number_input("Movement Flow (1-10)", min_value=1, max_value=10, step=1, value=5)
            assessment_data["Flow_Score"] = flow_score

        with col_a4:
            rhythm_score = st.number_input("Rhythm Consistency (1-10)", min_value=1, max_value=10, step=1, value=5)
            assessment_data["Rhythm_Score"] = rhythm_score

        st.divider()

        # B. POOMSAE COMPETITION BEHAVIOR
        st.subheader("B. Poomsae Competition Behavior & Performance (品勢競賽行為與表現)")
        st.markdown("**Focus:** Stage presence, focus during performance, recovery from mistakes, consistency across attempts?")

        comp_observation = st.text_area(
            "Coaching Observation (教練觀察)",
            height=100,
            placeholder="Stage presence and confidence, focus consistency, recovery from mistakes, emotional control, audience awareness...",
            key="poomsae_comp_obs"
        )
        assessment_data["Competition_Observation"] = comp_observation

        st.markdown("**Supporting Evidence (佐證數據):**")
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)

        with col_b1:
            competition_score = st.number_input("Competition Experience (# competitions)", min_value=0, step=1, value=0)
            assessment_data["Competition_Exp"] = competition_score

        with col_b2:
            focus = st.selectbox("Focus Under Pressure", ["Excellent (優秀)", "Good (良好)", "Fair (一般)", "Poor (不佳)"])
            assessment_data["Focus_Under_Pressure"] = focus

        with col_b3:
            consistency_poom = st.selectbox("Attempt Consistency", ["High (穩定)", "Moderate (中等)", "Variable (變動)"])
            assessment_data["Attempt_Consistency"] = consistency_poom

        with col_b4:
            stage_presence = st.selectbox("Stage Presence", ["Strong (強)", "Neutral (中立)", "Weak (弱)"])
            assessment_data["Stage_Presence"] = stage_presence

        st.divider()

        # C. POOMSAE HEALTH & RISK
        st.subheader("C. Athlete Status & Injury/Risk Flags (選手狀態與受傷/風險旗標)")
        st.markdown("**Focus:** Any physical concerns affecting movement? Flexibility or strength limitations?")

        health_observation = st.text_area(
            "Health & Movement Status (健康與動作狀態)",
            height=100,
            placeholder="Joint flexibility, strength limitations, current pain or discomfort, recovery status, movement quality issues...",
            key="poomsae_health_obs"
        )
        assessment_data["Health_Status"] = health_observation

        st.markdown("**Risk Flags (風險旗標):**")
        col_c1, col_c2, col_c3 = st.columns(3)

        with col_c1:
            flexibility_flag = st.selectbox("Flexibility Concern", ["None (無)", "Minor (輕微)", "Moderate (中等)", "High (高)"])
            assessment_data["Flexibility_Concern"] = flexibility_flag

        with col_c2:
            strength_flag = st.selectbox("Strength/Power Concern", ["None (無)", "Minor (輕微)", "Moderate (中等)", "High (高)"])
            assessment_data["Strength_Concern"] = strength_flag

        with col_c3:
            mental_flag = st.selectbox("Mental Status", ["Positive (積極)", "Stable (穩定)", "Concerned (擔憂)"])
            assessment_data["Mental_Status"] = mental_flag

    st.divider()

    # ═══════════════════════════════════════════════════════════════════
    # SECTION 3: EXECUTIVE SUMMARY & ACTION PLAN
    # ═══════════════════════════════════════════════════════════════════

    st.header("3️⃣ Executive Summary & Action Plan / 執行摘要與行動計畫")

    col_status1, col_status2 = st.columns(2)

    with col_status1:
        athlete_status = st.selectbox(
            "Overall Athlete Status (選手整體狀態)",
            ["🟢 Excellent (優秀)", "🟡 Good (良好)", "🟠 Fair (一般)", "🔴 Needs Support (需要協助)"]
        )

    with col_status2:
        risk_flags = st.selectbox(
            "Risk Flag Summary (風險旗標摘要)",
            ["🟢 None (無風險)", "🟡 Minor (輕微風險)", "🟠 Moderate (中等風險)", "🔴 High (高風險)"]
        )

    st.markdown("**Executive Summary (執行摘要):**")
    exec_summary = st.text_area(
        "Summary of assessment",
        height=120,
        placeholder="2-3 sentence summary of key findings, athlete strengths, and areas for development. Should be actionable and coaching-focused.",
        key="exec_summary"
    )
    assessment_data["Executive_Summary"] = exec_summary

    st.markdown("**Recommended Next Actions (建議下一步行動):**")
    next_actions = st.text_area(
        "Action plan",
        height=120,
        placeholder="Specific, measurable actions for next 2-4 weeks:\n- Technical focus areas\n- Competition/training plan adjustments\n- Recovery or injury prevention strategies\n- Mental preparation focus",
        key="next_actions"
    )
    assessment_data["Next_Actions"] = next_actions

    st.divider()

    # ═══════════════════════════════════════════════════════════════════
    # SUBMISSION BUTTONS
    # ═══════════════════════════════════════════════════════════════════

    col_submit1, col_submit2, col_submit3 = st.columns(3)

    with col_submit1:
        submit_btn = st.form_submit_button("✅ Submit & Upload to Cloud", use_container_width=True)

    with col_submit2:
        download_btn = st.form_submit_button("📄 Generate PDF Report Only", use_container_width=True)

    with col_submit3:
        st.form_submit_button("❌ Clear Form", type="secondary", use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# PDF GENERATION FUNCTION (with Chinese font support)
# ═══════════════════════════════════════════════════════════════════

def generate_pdf_report(athlete_info, assessment_data, is_sparring):
    """生成專業的 PDF 報告 (支援中文)"""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # ─────────────────────────────────────────────────────────────
    # 關鍵改動：註冊中文字體
    # 確保 'NotoSansTC-Regular.ttf' 這個檔名跟你上傳的完全一樣
    # ─────────────────────────────────────────────────────────────
    try:
        pdfmetrics.registerFont(TTFont('ChineseFont', 'NotoSansTC-VariableFont_wght.ttf'))
        font_name = 'ChineseFont'
    except:
        font_name = 'Helvetica'
        logger.warning("⚠️ 字體檔案未找到，PDF 中文將無法顯示")
    
    # 設定樣式
    styles = getSampleStyleSheet()
    
    # 覆蓋預設樣式的字體
    styles['Normal'].fontName = font_name
    styles['Heading1'].fontName = font_name
    styles['Heading2'].fontName = font_name
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f4e78'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName=font_name  # ← 改成 font_name
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2e5c8a'),
        spaceAfter=8,
        spaceBefore=12,
        fontName=font_name,  # ← 改成 font_name
        borderColor=colors.HexColor('#d0d0d0'),
        borderWidth=1,
        borderPadding=4
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        fontName=font_name  # ← 改成 font_name
    )
    
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#555555'),
        fontName=font_name  # ← 改成 font_name
    )
    
    # ─────────────────────────────────────────────────────────────
    # 定義表格樣式函數 (確保表格字體也用中文)
    # ─────────────────────────────────────────────────────────────
    def get_table_style_header():
        """表格標題樣式 (藍色背景)"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),  # ← 加入字體設定
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ])
    
    def get_table_style_info():
        """基本信息表格樣式 (淺色背景)"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),  # ← 加入字體設定
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ])
    
    # ─────────────────────────────────────────────────────────────
    # 文檔內容
    # ─────────────────────────────────────────────────────────────
    elements = []
    
    # --- 標題 ---
    elements.append(Paragraph("🥋 TAEKWONDO ATHLETE ASSESSMENT REPORT", title_style))
    elements.append(Paragraph("跆拳道選手評估報告", title_style))
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
    athlete_table.setStyle(get_table_style_info())
    elements.append(athlete_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # --- 技術觀察 ---
    if is_sparring:
        elements.append(Paragraph("Technical & Tactical Observation (技術與戰術觀察)", heading_style))
        elements.append(Paragraph(assessment_data.get("Technical_Observation", "N/A"), body_style))
        elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Paragraph("Competition Behavior (競賽行為)", heading_style))
        elements.append(Paragraph(assessment_data.get("Competition_Observation", "N/A"), body_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # 數據表格 (對打)
        sparring_data = [
            ["Metric", "Value"],
            ["Scoring Effectiveness", f"{assessment_data.get('Scoring_Effectiveness', 'N/A')}%"],
            ["Match Control (1-5)", f"{assessment_data.get('Match_Control', 'N/A')}"],
            ["Counters Conceded", f"{assessment_data.get('Counters_Conceded', 'N/A')}"],
            ["Penalties Received", f"{assessment_data.get('Penalties_Received', 'N/A')}"],
        ]
        sparring_table = Table(sparring_data, colWidths=[2.5*inch, 2.5*inch])
        sparring_table.setStyle(get_table_style_header())
        elements.append(sparring_table)
        elements.append(Spacer(1, 0.15*inch))
    else:
        elements.append(Paragraph("Poomsae Technical Execution (品勢技術執行)", heading_style))
        elements.append(Paragraph(assessment_data.get("Technical_Observation", "N/A"), body_style))
        elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Paragraph("Competition Performance (競賽表現)", heading_style))
        elements.append(Paragraph(assessment_data.get("Competition_Observation", "N/A"), body_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # 數據表格 (品勢)
        poomsae_data = [
            ["Metric", "Score (1-10)"],
            ["Technical Accuracy", f"{assessment_data.get('Accuracy_Score', 'N/A')}"],
            ["Power Level", f"{assessment_data.get('Power_Score', 'N/A')}"],
            ["Movement Flow", f"{assessment_data.get('Flow_Score', 'N/A')}"],
            ["Rhythm Consistency", f"{assessment_data.get('Rhythm_Score', 'N/A')}"],
        ]
        poomsae_table = Table(poomsae_data, colWidths=[2.5*inch, 2.5*inch])
        poomsae_table.setStyle(get_table_style_header())
        elements.append(poomsae_table)
        elements.append(Spacer(1, 0.15*inch))
    
    # --- 健康與風險 ---
    elements.append(Paragraph("Health Status & Risk Assessment (健康狀態與風險評估)", heading_style))
    elements.append(Paragraph(assessment_data.get("Health_Status", "N/A"), body_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # --- 執行摘要 ---
    elements.append(PageBreak())
    elements.append(Paragraph("Executive Summary & Action Plan (執行摘要與行動計畫)", heading_style))
    
    elements.append(Paragraph("<b>Overall Status: </b>" + athlete_info['athlete_status'], body_style))
    elements.append(Spacer(1, 0.05*inch))
    
    elements.append(Paragraph("<b>Assessment Summary (評估摘要):</b>", label_style))
    elements.append(Paragraph(athlete_info['exec_summary'], body_style))
    elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Paragraph("<b>Recommended Next Actions (建議下一步行動):</b>", label_style))
    elements.append(Paragraph(athlete_info['next_actions'], body_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # --- 頁尾 ---
    elements.append(Spacer(1, 0.2*inch))
    footer_text = f"Report generated on {date.today().strftime('%Y-%m-%d')} | Coaching observation-first approach"
    elements.append(Paragraph(f"<i>{footer_text}</i>", styles['Normal']))
    
    # 生成 PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ═══════════════════════════════════════════════════════════════════
# HANDLE SUBMISSION & DOWNLOAD (with session_state fix)
# ═══════════════════════════════════════════════════════════════════

# 初始化 Session State
if 'pdf_buffer' not in st.session_state:
    st.session_state.pdf_buffer = None
if 'pdf_filename' not in st.session_state:
    st.session_state.pdf_filename = "report.pdf"

# 表單提交處理
if submit_btn or download_btn:
    # 驗證
    if not athlete_name:
        st.error("⚠️ Please enter athlete name")
        st.stop()

    # 準備資料
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
    assessment_data["Risk_Flags"] = risk_flags

    # 生成 PDF 並存入 Session State
    try:
        pdf_buffer = generate_pdf_report(athlete_info, assessment_data, is_sparring)
        st.session_state.pdf_buffer = pdf_buffer
        st.session_state.pdf_filename = f"{athlete_name}_Assessment_{eval_date.strftime('%Y%m%d')}.pdf"
        st.success("✅ PDF generated successfully!")
    except Exception as e:
        st.error(f"❌ PDF generation failed: {str(e)}")
        logger.error(f"PDF error: {str(e)}", exc_info=True)

    # 如果是點擊上傳按鈕
    if submit_btn:
        with st.spinner("🔄 Uploading to Google Sheets..."):
            try:
                logger.info("Attempting to establish Google Sheets connection...")
                conn = st.connection("gsheets", type=GSheetsConnection)
                logger.info("✅ Connection established successfully")
                
                # 準備數據
                row_data = {
                    "Date (日期)": eval_date.strftime("%Y-%m-%d"),
                    "Name (姓名)": athlete_name,
                    "Age Group (年齡組)": age_group,
                    "Gender (性別)": gender,
                    "Weight (量級)": weight_cat,
                    "Mode (模式)": "Sparring" if is_sparring else "Poomsae",
                    "Status (狀態)": athlete_status,
                    "Risk Flags (風險旗標)": risk_flags,
                }
                
                new_df = pd.DataFrame([row_data])
                
                try:
                    existing_data = conn.read(worksheet="sheet1", ttl=0)
                    if isinstance(existing_data, list):
                        existing_df = pd.DataFrame(existing_data) if existing_data else pd.DataFrame()
                    else:
                        existing_df = existing_data
                    
                    if len(existing_df) > 0:
                        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                    else:
                        updated_df = new_df
                except:
                    updated_df = new_df
                
                conn.update(worksheet="sheet1", data=updated_df)
                logger.info("✅ Data uploaded successfully!")
                st.success(f"🎉 Success! {athlete_name}'s assessment uploaded to Google Sheets!")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Upload failed: {str(e)}")
                logger.error(f"Upload error: {str(e)}", exc_info=True)

# ─────────────────────────────────────────────────────────────
# 在表單外部顯示下載按鈕 (關鍵改動)
# 這樣按鈕才不會在點擊後消失
# ─────────────────────────────────────────────────────────────

if st.session_state.pdf_buffer:
    st.divider()
    st.markdown("### 📥 Download Report")
    
    col_download1, col_download2, col_download3 = st.columns([2, 2, 2])
    
    with col_download1:
        st.download_button(
            label=f"📄 Download PDF Report",
            data=st.session_state.pdf_buffer.getvalue(),
            file_name=st.session_state.pdf_filename,
            mime="application/pdf",
            key="pdf_download_btn",
            use_container_width=True
        )
    
    with col_download2:
        st.info(f"✅ File: {st.session_state.pdf_filename}")
    
    with col_download3:
        if st.button("🔄 Clear & Start New", use_container_width=True):
            st.session_state.pdf_buffer = None
            st.session_state.pdf_filename = "report.pdf"
            st.rerun()

st.divider()
st.caption("🥋 Taekwondo Athlete Scorecard | Coaching observation-first. Data supports, not drives, decisions.")
