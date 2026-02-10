import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import logging
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from datetime import date

# ================================================================
# 🥋 SINGAPORE TAEKWONDO NATIONAL TEAM – ATHLETE SCORECARD
# ================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Singapore Taekwondo National Team – Athlete Scorecard",
    page_icon="🥋",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.05rem;
        font-weight: 600;
    }
    .report-note {
        color: #555555;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🥋 Singapore Taekwondo National Team – Athlete Scorecard")
st.markdown(
    "<p class='report-note'>Coaching observation-first; data supports, not drives, decisions.</p>",
    unsafe_allow_html=True,
)

# --- Weight Categories ---
weight_categories = {
    "Senior": {
        "Male": ["-54 kg", "-58 kg", "-63 kg", "-68 kg", "-74 kg", "-80 kg", "-87 kg", "+87 kg"],
        "Female": ["-46 kg", "-49 kg", "-53 kg", "-57 kg", "-62 kg", "-67 kg", "-73 kg", "+73 kg"],
    },
    "Junior – Ages 15–17": {
        "Male": [
            "-45 kg",
            "-48 kg",
            "-51 kg",
            "-55 kg",
            "-59 kg",
            "-63 kg",
            "-68 kg",
            "-73 kg",
            "-78 kg",
            "+78 kg",
        ],
        "Female": [
            "-42 kg",
            "-44 kg",
            "-46 kg",
            "-49 kg",
            "-52 kg",
            "-55 kg",
            "-59 kg",
            "-63 kg",
            "-68 kg",
            "+68 kg",
        ],
    },
    "Cadet – Ages 12–14": {
        "Male": ["-33 kg", "-37 kg", "-41 kg", "-45 kg", "-49 kg", "-53 kg", "-57 kg", "-61 kg", "-65 kg", "+65 kg"],
        "Female": ["-29 kg", "-33 kg", "-37 kg", "-41 kg", "-44 kg", "-47 kg", "-51 kg", "-55 kg", "-59 kg", "+59 kg"],
    },
}

# ================================================================
# Evaluation Mode
# ================================================================

eval_mode = st.radio(
    "Evaluation Mode",
    ["Sparring / Kyorugi", "Poomsae"],
    horizontal=True,
    help="Select the primary assessment type for this session.",
)

is_sparring = "Sparring" in eval_mode
is_poomsae = "Poomsae" in eval_mode

st.divider()

# ================================================================
# 1. Athlete Profile
# ================================================================

st.header("1️⃣ Athlete Profile")

col1, col2, col3, col4 = st.columns(4)

with col1:
    athlete_name = st.text_input("Athlete Name")

with col2:
    eval_date = st.date_input("Evaluation Date", datetime.today())

with col3:
    age_group = st.selectbox("Age Division", list(weight_categories.keys()))

with col4:
    gender = st.selectbox("Gender", ["Male", "Female"])

col5, col6, col7 = st.columns(3)

with col5:
    if is_sparring:
        available_weights = weight_categories[age_group][gender]
        weight_cat = st.selectbox("Weight Category", available_weights)
    else:
        weight_cat = "N/A"

with col6:
    context = st.selectbox(
        "Context",
        ["Domestic Competition", "International Competition", "Training Camp"],
    )

with col7:
    eval_type = st.selectbox(
        "Evaluation Type",
        ["Regular Check", "Event-based", "Boot Camp"],
    )

st.divider()

# ================================================================
# 2. Technical / Competition / Health Assessment
# ================================================================

st.header("2️⃣ Assessment")

with st.form("assessment_form"):

    assessment_data = {}

    if is_sparring:
        # --------------------------------------------------------
        # Sparring Mode
        # --------------------------------------------------------
        st.subheader("A. Technical & Tactical Execution")
        st.markdown(
            "Focus: Tactical planning, match control, adaptation to different opponent styles, and technical consistency under pressure."
        )

        col_tact1, col_tact2 = st.columns(2)

        with col_tact1:
            st.markdown("**Pre-match Tactical Planning**")
            pregame_tactic = st.text_area(
                "Coaching Observation – Pre-match",
                height=80,
                placeholder="Tactical clarity, opponent analysis, strategy selection, readiness.",
                key="pregame_tactic",
            )
            assessment_data["Pre_Match_Tactic"] = pregame_tactic

        with col_tact2:
            st.markdown("**In-match Tactical Execution**")
            inmatch_tactic = st.text_area(
                "Coaching Observation – In-match",
                height=80,
                placeholder="Consistency of execution, tactical adjustments, tempo control.",
                key="inmatch_tactic",
            )
            assessment_data["In_Match_Tactic"] = inmatch_tactic

        st.markdown("**Match Control & Opponent Adaptation**")
        tech_observation = st.text_area(
            "Coaching Observation – Technical & Tactical",
            height=100,
            placeholder="Match control, reaction to aggressive/defensive/tempo-based opponents, quality under pressure.",
            key="tech_obs",
        )
        assessment_data["Technical_Observation"] = tech_observation

        st.markdown("**Supporting Metrics:**")
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)

        with col_a1:
            scoring_eff = st.number_input(
                "Scoring Effectiveness (%)",
                min_value=0,
                max_value=100,
                step=5,
                value=50,
            )
            assessment_data["Scoring_Effectiveness"] = scoring_eff

        with col_a2:
            match_control = st.number_input(
                "Match Control (1–5)",
                min_value=1,
                max_value=5,
                step=1,
                value=3,
            )
            assessment_data["Match_Control"] = match_control

        with col_a3:
            counters = st.number_input(
                "Counters Conceded per Match",
                min_value=0,
                step=1,
                value=0,
            )
            assessment_data["Counters_Conceded"] = counters

        with col_a4:
            penalties = st.number_input(
                "Penalties per Match",
                min_value=0,
                step=1,
                value=0,
            )
            assessment_data["Penalties_Received"] = penalties

        st.divider()

        st.subheader("B. Competition Behaviour & Readiness")
        st.markdown(
            "Focus: Response after scores/penalties, decision quality when behind, and tolerance to high-tempo competition."
        )

        comp_observation = st.text_area(
            "Coaching Observation – Competition Behaviour",
            height=100,
            placeholder="Post-score reactions, decisions when trailing, pressure response, match-load tolerance.",
            key="comp_obs",
        )
        assessment_data["Competition_Observation"] = comp_observation

        st.markdown("**Supporting Metrics:**")
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)

        with col_b1:
            intl_matches = st.number_input(
                "International Matches (lifetime)",
                min_value=0,
                step=1,
                value=0,
            )
            assessment_data["Intl_Matches"] = intl_matches

        with col_b2:
            consistency = st.selectbox(
                "Performance Consistency",
                ["High", "Moderate", "Low"],
            )
            assessment_data["Performance_Consistency"] = consistency

        with col_b3:
            pressure_response = st.selectbox(
                "Pressure Response",
                ["Positive", "Neutral", "Negative"],
            )
            assessment_data["Pressure_Response"] = pressure_response

        with col_b4:
            load_tolerance = st.selectbox(
                "Match Load Tolerance",
                ["High", "Moderate", "Low"],
            )
            assessment_data["Match_Load_Tolerance"] = load_tolerance

        st.divider()

        st.subheader("C. Health Status & Risk Flags")
        st.markdown(
            "Focus: Current physical/mental condition, injury status, fatigue level, and any red flags affecting performance or safety."
        )

        health_observation = st.text_area(
            "Health & Injury Status – Coaching Notes",
            height=100,
            placeholder="Current injuries, fatigue level, recovery status, and areas needing close monitoring.",
            key="health_obs",
        )
        assessment_data["Health_Status"] = health_observation

        st.markdown("**Risk Flags:**")
        col_c1, col_c2, col_c3 = st.columns(3)

        with col_c1:
            injury_flag = st.selectbox(
                "Injury Risk",
                ["None", "Minor", "Moderate", "High"],
            )
            assessment_data["Injury_Risk"] = injury_flag

        with col_c2:
            fatigue_flag = st.selectbox(
                "Fatigue Level",
                ["Low", "Moderate", "High", "Critical"],
            )
            assessment_data["Fatigue_Level"] = fatigue_flag

        with col_c3:
            mental_flag = st.selectbox(
                "Mental Status",
                ["Positive", "Stable", "Concerned"],
            )
            assessment_data["Mental_Status"] = mental_flag

    else:
        # --------------------------------------------------------
        # Poomsae Mode
        # --------------------------------------------------------
        st.subheader("A. Technical Execution")
        st.markdown(
            "Focus: Accuracy, power, stance stability, movement precision, and rhythm consistency."
        )

        col_tact1, col_tact2 = st.columns(2)

        with col_tact1:
            st.markdown("**Form Accuracy & Technique Quality**")
            form_accuracy = st.text_area(
                "Coaching Observation – Form",
                height=80,
                placeholder="Sequence accuracy, stance depth, hand and foot positions, body alignment.",
                key="form_accuracy",
            )
            assessment_data["Form_Accuracy"] = form_accuracy

        with col_tact2:
            st.markdown("**Power & Delivery**")
            power_delivery = st.text_area(
                "Coaching Observation – Power",
                height=80,
                placeholder="Kick height and power, hand speed, overall explosiveness.",
                key="power_delivery",
            )
            assessment_data["Power_Delivery"] = power_delivery

        st.markdown("**Movement Flow & Rhythm**")
        tech_observation = st.text_area(
            "Coaching Observation – Technical Summary",
            height=100,
            placeholder="Transitions, weight shifting, balance recovery, rhythm stability.",
            key="poomsae_obs",
        )
        assessment_data["Technical_Observation"] = tech_observation

        st.markdown("**Supporting Metrics:**")
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)

        with col_a1:
            accuracy_score = st.number_input(
                "Technical Accuracy (1–10)",
                min_value=1,
                max_value=10,
                step=1,
                value=5,
            )
            assessment_data["Accuracy_Score"] = accuracy_score

        with col_a2:
            power_score = st.number_input(
                "Power Level (1–10)",
                min_value=1,
                max_value=10,
                step=1,
                value=5,
            )
            assessment_data["Power_Score"] = power_score

        with col_a3:
            flow_score = st.number_input(
                "Movement Flow (1–10)",
                min_value=1,
                max_value=10,
                step=1,
                value=5,
            )
            assessment_data["Flow_Score"] = flow_score

        with col_a4:
            rhythm_score = st.number_input(
                "Rhythm Consistency (1–10)",
                min_value=1,
                max_value=10,
                step=1,
                value=5,
            )
            assessment_data["Rhythm_Score"] = rhythm_score

        st.divider()

        st.subheader("B. Competition Behaviour & Presentation")
        st.markdown(
            "Focus: Stage presence, focus under pressure, recovery from mistakes, and overall consistency."
        )

        comp_observation = st.text_area(
            "Coaching Observation – Competition Behaviour",
            height=100,
            placeholder="Presence, confidence, recovery after errors, emotional control, overall performance quality.",
            key="poomsae_comp_obs",
        )
        assessment_data["Competition_Observation"] = comp_observation

        st.markdown("**Supporting Metrics:**")
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)

        with col_b1:
            competition_score = st.number_input(
                "Competition Experience (number of events)",
                min_value=0,
                step=1,
                value=0,
            )
            assessment_data["Competition_Exp"] = competition_score

        with col_b2:
            focus = st.selectbox(
                "Focus Under Pressure",
                ["Excellent", "Good", "Fair", "Poor"],
            )
            assessment_data["Focus_Under_Pressure"] = focus

        with col_b3:
            consistency_poom = st.selectbox(
                "Attempt Consistency",
                ["High", "Moderate", "Variable"],
            )
            assessment_data["Attempt_Consistency"] = consistency_poom

        with col_b4:
            stage_presence = st.selectbox(
                "Stage Presence",
                ["Strong", "Neutral", "Weak"],
            )
            assessment_data["Stage_Presence"] = stage_presence

        st.divider()

        st.subheader("C. Health, Training Consistency & Risks")
        st.markdown(
            "Focus: Flexibility, strength limitations, movement quality issues, and training continuity."
        )

        health_observation = st.text_area(
            "Health & Movement Status – Coaching Notes",
            height=100,
            placeholder="Joint mobility, strength imbalance, pain or discomfort, recovery status, movement quality.",
            key="poomsae_health_obs",
        )
        assessment_data["Health_Status"] = health_observation

        st.markdown("**Risk Flags:**")
        col_c1, col_c2, col_c3 = st.columns(3)

        with col_c1:
            flexibility_flag = st.selectbox(
                "Flexibility Concern",
                ["None", "Minor", "Moderate", "High"],
            )
            assessment_data["Flexibility_Concern"] = flexibility_flag

        with col_c2:
            strength_flag = st.selectbox(
                "Strength/Power Concern",
                ["None", "Minor", "Moderate", "High"],
            )
            assessment_data["Strength_Concern"] = strength_flag

        with col_c3:
            mental_flag = st.selectbox(
                "Mental Status",
                ["Positive", "Stable", "Concerned"],
            )
            assessment_data["Mental_Status"] = mental_flag

    st.divider()

    # ============================================================
    # 3. Executive Summary & Action Plan
    # ============================================================

    st.header("3️⃣ Executive Summary & Action Plan")

    col_status1, col_status2 = st.columns(2)

    with col_status1:
        athlete_status = st.selectbox(
            "Overall Athlete Status",
            ["Excellent", "Good", "Fair", "Needs Support"],
        )

    with col_status2:
        risk_flags = st.selectbox(
            "Risk Flag Summary",
            ["None", "Minor", "Moderate", "High"],
        )

    st.markdown("**Executive Summary:**")
    exec_summary = st.text_area(
        "Summary of Assessment (2–3 sentences)",
        height=120,
        placeholder="Highlight key strengths, main development areas, and readiness for upcoming events.",
        key="exec_summary",
    )
    assessment_data["Executive_Summary"] = exec_summary

    st.markdown("**Recommended Next Actions:**")
    next_actions = st.text_area(
        "Action Plan for Next 2–4 Weeks",
        height=120,
        placeholder=(
            "- Technical / tactical focus areas\n"
            "- Training and competition adjustments\n"
            "- Recovery and injury prevention strategies\n"
            "- Mental preparation and routine"
        ),
        key="next_actions",
    )
    assessment_data["Next_Actions"] = next_actions

    st.divider()

    col_submit1, col_submit2, col_submit3 = st.columns(3)
    with col_submit1:
        submit_btn = st.form_submit_button("✅ Submit & Upload", use_container_width=True)
    with col_submit2:
        download_btn = st.form_submit_button("📄 Generate PDF Only", use_container_width=True)
    with col_submit3:
        st.form_submit_button("❌ Clear Form", type="secondary", use_container_width=True)

# ================================================================
# 4. Live Training Attendance (outside form, instant update)
# ================================================================

st.divider()
st.header("4️⃣ Training Attendance Overview")

if is_sparring:
    st.subheader("Sparring Training Attendance")
else:
    st.subheader("Poomsae Training Attendance")

col_att1, col_att2 = st.columns(2)

with col_att1:
    live_sessions_required = st.number_input(
        "Sessions Required (this period)",
        min_value=0,
        step=1,
        value=20,
        key="live_sessions_required",
    )
    live_sessions_attended = st.number_input(
        "Sessions Attended",
        min_value=0,
        step=1,
        value=18,
        key="live_sessions_attended",
    )

    if live_sessions_required > 0:
        live_attendance_rate = (live_sessions_attended / live_sessions_required) * 100
    else:
        live_attendance_rate = 0.0

    rate_label = "On track" if live_attendance_rate >= 85 else "Below target"
    st.metric("Attendance Rate", f"{live_attendance_rate:.1f}%", rate_label)

with col_att2:
    if live_sessions_required > 0:
        df_live = pd.DataFrame(
            {
                "Status": ["Attended", "Missed"],
                "Sessions": [live_sessions_attended, max(live_sessions_required - live_sessions_attended, 0)],
            }
        )
        fig_live = px.pie(
            df_live,
            names="Status",
            values="Sessions",
            hole=0.55,
            color="Status",
            color_discrete_map={"Attended": "#2ecc71", "Missed": "#e74c3c"},
            title="Attendance Breakdown",
        )
        fig_live.update_layout(showlegend=True)
        st.plotly_chart(fig_live, use_container_width=True)

# store attendance into assessment_data for PDF / upload
assessment_data["Attendance_Rate"] = live_attendance_rate
assessment_data["Sessions_Required"] = live_sessions_required
assessment_data["Sessions_Attended"] = live_sessions_attended

# ================================================================
# PDF Generation
# ================================================================


def generate_pdf_report(athlete_info, assessment_data, is_sparring):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)

    try:
        pdfmetrics.registerFont(TTFont("ChineseFont", "NotoSansTC-VariableFont_wght.ttf"))
        font_name = "ChineseFont"
    except Exception:
        font_name = "Helvetica"
        logger.warning("⚠️ Font file not found; non-Latin text may not render correctly in PDF.")

    styles = getSampleStyleSheet()
    styles["Normal"].fontName = font_name
    styles["Heading1"].fontName = font_name
    styles["Heading2"].fontName = font_name

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#1f4e78"),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName=font_name,
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#2e5c8a"),
        spaceAfter=8,
        spaceBefore=10,
        fontName=font_name,
        borderColor=colors.HexColor("#d0d0d0"),
        borderWidth=1,
        borderPadding=4,
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        fontName=font_name,
    )

    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        fontName=font_name,
    )

    def get_table_style_header():
        return TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e5c8a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#cccccc")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ]
        )

    def get_table_style_info():
        return TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f0f7")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#cccccc")),
            ]
        )

    elements = []

    elements.append(Paragraph("SINGAPORE TAEKWONDO NATIONAL TEAM", title_style))
    elements.append(Paragraph("Athlete Assessment Report", title_style))
    elements.append(Spacer(1, 0.15 * inch))

    weight_val = athlete_info["weight_cat"] if is_sparring else "N/A"

    athlete_table_data = [
        [Paragraph("Athlete Name", label_style), athlete_info["athlete_name"]],
        [Paragraph("Evaluation Date", label_style), athlete_info["eval_date"].strftime("%Y-%m-%d")],
        [Paragraph("Age Division", label_style), athlete_info["age_group"]],
        [Paragraph("Gender", label_style), athlete_info["gender"]],
        [Paragraph("Weight Category", label_style), weight_val],
        [Paragraph("Context", label_style), athlete_info["context"]],
        [Paragraph("Evaluation Type", label_style), athlete_info["eval_type"]],
        [Paragraph("Mode", label_style), "Sparring" if is_sparring else "Poomsae"],
    ]

    athlete_table = Table(athlete_table_data, colWidths=[2.6 * inch, 2.9 * inch])
    athlete_table.setStyle(get_table_style_info())
    elements.append(athlete_table)
    elements.append(Spacer(1, 0.2 * inch))

    if is_sparring:
        elements.append(Paragraph("Technical & Tactical Observation", heading_style))
        elements.append(Paragraph(assessment_data.get("Technical_Observation", "N/A"), body_style))
        elements.append(Spacer(1, 0.1 * inch))

        elements.append(Paragraph("Competition Behaviour", heading_style))
        elements.append(Paragraph(assessment_data.get("Competition_Observation", "N/A"), body_style))
        elements.append(Spacer(1, 0.1 * inch))

        sparring_data = [
            ["Metric", "Value"],
            ["Scoring Effectiveness (%)", f"{assessment_data.get('Scoring_Effectiveness', 'N/A')}%"],
            ["Match Control (1–5)", f"{assessment_data.get('Match_Control', 'N/A')}"],
            ["Counters Conceded per Match", f"{assessment_data.get('Counters_Conceded', 'N/A')}"],
            ["Penalties per Match", f"{assessment_data.get('Penalties_Received', 'N/A')}"],
            ["Attendance Rate (%)", f"{assessment_data.get('Attendance_Rate', 0):.1f}%"],
            ["Sessions Required", f"{assessment_data.get('Sessions_Required', 0)}"],
            ["Sessions Attended", f"{assessment_data.get('Sessions_Attended', 0)}"],
        ]
        sparring_table = Table(sparring_data, colWidths=[3.1 * inch, 2.4 * inch])
        sparring_table.setStyle(get_table_style_header())
        elements.append(sparring_table)
        elements.append(Spacer(1, 0.15 * inch))
    else:
        elements.append(Paragraph("Technical Execution", heading_style))
        elements.append(Paragraph(assessment_data.get("Technical_Observation", "N/A"), body_style))
        elements.append(Spacer(1, 0.1 * inch))

        elements.append(Paragraph("Competition Performance", heading_style))
        elements.append(Paragraph(assessment_data.get("Competition_Observation", "N/A"), body_style))
        elements.append(Spacer(1, 0.1 * inch))

        poomsae_data = [
            ["Metric", "Value"],
            ["Technical Accuracy", f"{assessment_data.get('Accuracy_Score', 'N/A')}"],
            ["Power Level", f"{assessment_data.get('Power_Score', 'N/A')}"],
            ["Movement Flow", f"{assessment_data.get('Flow_Score', 'N/A')}"],
            ["Rhythm Consistency", f"{assessment_data.get('Rhythm_Score', 'N/A')}"],
            ["Attendance Rate (%)", f"{assessment_data.get('Attendance_Rate', 0):.1f}%"],
            ["Sessions Required", f"{assessment_data.get('Sessions_Required', 0)}"],
            ["Sessions Attended", f"{assessment_data.get('Sessions_Attended', 0)}"],
        ]
        poomsae_table = Table(poomsae_data, colWidths=[3.1 * inch, 2.4 * inch])
        poomsae_table.setStyle(get_table_style_header())
        elements.append(poomsae_table)
        elements.append(Spacer(1, 0.15 * inch))

    elements.append(Paragraph("Health Status & Risk Assessment", heading_style))
    elements.append(Paragraph(assessment_data.get("Health_Status", "N/A"), body_style))
    elements.append(Spacer(1, 0.1 * inch))

    elements.append(PageBreak())
    elements.append(Paragraph("Executive Summary & Action Plan", heading_style))
    elements.append(Paragraph(f"Overall Athlete Status: {athlete_info['athlete_status']}", body_style))
    elements.append(Spacer(1, 0.08 * inch))
    elements.append(Paragraph("Executive Summary:", label_style))
    elements.append(Paragraph(athlete_info["exec_summary"], body_style))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("Recommended Next Actions:", label_style))
    elements.append(Paragraph(athlete_info["next_actions"], body_style))
    elements.append(Spacer(1, 0.2 * inch))

    footer_text = f"Report generated on {date.today().strftime('%Y-%m-%d')} – Singapore Taekwondo National Team"
    elements.append(Paragraph(footer_text, styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ================================================================
# Upload & Download
# ================================================================

if "pdf_buffer" not in st.session_state:
    st.session_state.pdf_buffer = None
if "pdf_filename" not in st.session_state:
    st.session_state.pdf_filename = "report.pdf"

if submit_btn or download_btn:
    if not athlete_name:
        st.error("⚠️ Please enter Athlete Name.")
        st.stop()

    athlete_info = {
        "athlete_name": athlete_name,
        "eval_date": eval_date,
        "age_group": age_group,
        "gender": gender,
        "weight_cat": weight_cat,
        "context": context,
        "eval_type": eval_type,
        "athlete_status": athlete_status,
        "exec_summary": exec_summary,
        "next_actions": next_actions,
    }

    assessment_data["Eval_Mode"] = "Sparring" if is_sparring else "Poomsae"
    assessment_data["Athlete_Status"] = athlete_status
    assessment_data["Risk_Flags"] = risk_flags

    try:
        pdf_buffer = generate_pdf_report(athlete_info, assessment_data, is_sparring)
        st.session_state.pdf_buffer = pdf_buffer
        st.session_state.pdf_filename = f"{athlete_name}_Assessment_{eval_date.strftime('%Y%m%d')}.pdf"
        st.success("PDF report generated successfully.")
    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")
        logger.error(f"PDF error: {str(e)}", exc_info=True)

    if submit_btn:
        with st.spinner("Uploading data to Google Sheets..."):
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                row_data = {
                    "Date": eval_date.strftime("%Y-%m-%d"),
                    "Name": athlete_name,
                    "Age Group": age_group,
                    "Gender": gender,
                    "Weight": weight_cat if is_sparring else "N/A",
                    "Mode": "Sparring" if is_sparring else "Poomsae",
                    "Status": athlete_status,
                    "Risk Flags": risk_flags,
                    "Attendance Rate (%)": assessment_data.get("Attendance_Rate", 0),
                    "Sessions Required": assessment_data.get("Sessions_Required", 0),
                    "Sessions Attended": assessment_data.get("Sessions_Attended", 0),
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
                except Exception:
                    updated_df = new_df

                conn.update(worksheet="sheet1", data=updated_df)
                st.success(f"Assessment for {athlete_name} has been uploaded.")
                st.balloons()
            except Exception as e:
                st.error(f"Upload failed: {str(e)}")
                logger.error(f"Upload error: {str(e)}", exc_info=True)

if st.session_state.pdf_buffer:
    st.divider()
    st.markdown("### 📥 Download Report")
    col_d1, col_d2, col_d3 = st.columns([2, 2, 2])

    with col_d1:
        st.download_button(
            label="📄 Download PDF Report",
            data=st.session_state.pdf_buffer.getvalue(),
            file_name=st.session_state.pdf_filename,
            mime="application/pdf",
            key="pdf_download_btn",
            use_container_width=True,
        )

    with col_d2:
        st.info(f"Current file: {st.session_state.pdf_filename}")

    with col_d3:
        if st.button("🔄 Clear & Start New", use_container_width=True):
            st.session_state.pdf_buffer = None
            st.session_state.pdf_filename = "report.pdf"
            st.rerun()

st.divider()
st.caption(
    "🥋 Singapore Taekwondo National Team – Athlete Scorecard | Coaching observation-first, with structured data support."
)
