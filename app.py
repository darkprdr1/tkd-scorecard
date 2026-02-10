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

# ═══════════════════════════════════════════════════════════════════
# 🥋 SINGAPORE TAEKWONDO NATIONAL TEAM – ATHLETE SCORECARD
# ═══════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Singapore Taekwondo National Team – Athlete Scorecard", page_icon="🥋", layout="wide")

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
    "<p class='report-note'>Coaching observation-first; data supports, not drives, decisions.（以教練專業觀察為核心，數據為輔助參考）</p>",
    unsafe_allow_html=True,
)

# --- Weight Categories ---
weight_categories = {
    "Senior (成人)": {
        "Male (男)": ["-54 kg", "-58 kg", "-63 kg", "-68 kg", "-74 kg", "-80 kg", "-87 kg", "+87 kg"],
        "Female (女)": ["-46 kg", "-49 kg", "-53 kg", "-57 kg", "-62 kg", "-67 kg", "-73 kg", "+73 kg"],
    },
    "Junior – Ages 15–17 (青少年)": {
        "Male (男)": [
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
        "Female (女)": [
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
    "Cadet – Ages 12–14 (少年)": {
        "Male (男)": ["-33 kg", "-37 kg", "-41 kg", "-45 kg", "-49 kg", "-53 kg", "-57 kg", "-61 kg", "-65 kg", "+65 kg"],
        "Female (女)": ["-29 kg", "-33 kg", "-37 kg", "-41 kg", "-44 kg", "-47 kg", "-51 kg", "-55 kg", "-59 kg", "+59 kg"],
    },
}

# ═══════════════════════════════════════════════════════════════════
# Evaluation Mode
# ═══════════════════════════════════════════════════════════════════

eval_mode = st.radio(
    "Evaluation Mode (評估模式)",
    ["Sparring / Kyorugi (對打)", "Poomsae (品勢)"],
    horizontal=True,
    help="Please select the assessment type for this session.（請選擇本次評估項目）",
)

is_sparring = "Sparring" in eval_mode or "對打" in eval_mode
is_poomsae = "Poomsae" in eval_mode or "品勢" in eval_mode

st.divider()

# ═══════════════════════════════════════════════════════════════════
# 1. Athlete Profile
# ═══════════════════════════════════════════════════════════════════

st.header("1️⃣ Athlete Profile (選手基本資料)")

col1, col2, col3, col4 = st.columns(4)

with col1:
    athlete_name = st.text_input("Athlete Name (選手姓名)")

with col2:
    eval_date = st.date_input("Evaluation Date (評估日期)", datetime.today())

with col3:
    age_group = st.selectbox("Age Division (年齡組別)", list(weight_categories.keys()))

with col4:
    gender = st.selectbox("Gender (性別)", ["Male (男)", "Female (女)"])

col5, col6, col7 = st.columns(3)

with col5:
    if is_sparring:
        available_weights = weight_categories[age_group][gender]
        weight_cat = st.selectbox("Weight Category (量級)", available_weights)
    else:
        weight_cat = "N/A"

with col6:
    context = st.selectbox(
        "Context (參賽情境)",
        ["Domestic Competition (國內賽)", "International Competition (國際賽)", "Training Camp (移地訓練)"],
    )

with col7:
    eval_type = st.selectbox(
        "Evaluation Type (評估類型)",
        ["Regular Check (例行評估)", "Event-based (賽事前後)", "Boot Camp (集訓期間)"],
    )

st.divider()

# ═══════════════════════════════════════════════════════════════════
# 2. Technical / Competition / Health Assessment (inside form)
# ═══════════════════════════════════════════════════════════════════

st.header("2️⃣ Assessment (技術與比賽表現評估)")

with st.form("assessment_form"):

    assessment_data = {}

    if is_sparring:
        # ─────────────────────────────────────────────────────────────
        # Sparring Mode
        # ─────────────────────────────────────────────────────────────
        st.subheader("A. Technical & Tactical Execution (技術與戰術執行)")
        st.markdown(
            "Focus: Tactical planning, match control, adaptation to different opponent styles, and technical consistency under pressure.（戰術規劃、比賽掌控、對手風格調整與壓力下的技術穩定度）"
        )

        col_tact1, col_tact2 = st.columns(2)

        with col_tact1:
            st.markdown("**Pre-match Tactical Planning (賽前戰術規劃)**")
            pregame_tactic = st.text_area(
                "Coaching Observation – Pre-match (教練觀察－賽前)",
                height=80,
                placeholder="Tactical clarity, opponent analysis, strategy selection, readiness.（戰術計畫清晰度、對手分析、策略選擇與準備狀態）",
                key="pregame_tactic",
            )
            assessment_data["Pre_Match_Tactic"] = pregame_tactic

        with col_tact2:
            st.markdown("**In-match Tactical Execution (比賽中戰術執行)**")
            inmatch_tactic = st.text_area(
                "Coaching Observation – In-match (教練觀察－比賽中)",
                height=80,
                placeholder="Consistency of execution, tactical adjustments, tempo control.（戰術執行連貫度、臨場調整與節奏掌握）",
                key="inmatch_tactic",
            )
            assessment_data["In_Match_Tactic"] = inmatch_tactic

        st.markdown("**Match Control & Opponent Adaptation (比賽掌控與對手風格適應)**")
        tech_observation = st.text_area(
            "Coaching Observation (教練綜合觀察)",
            height=100,
            placeholder="Match control, response to aggressive/defensive/tempo-based opponents, quality under pressure.（面對不同風格對手時的掌控與調整）",
            key="tech_obs",
        )
        assessment_data["Technical_Observation"] = tech_observation

        st.markdown("**Supporting Metrics (佐證數據)：**")
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)

        with col_a1:
            scoring_eff = st.number_input("Scoring Effectiveness (%) (得分效率)", min_value=0, max_value=100, step=5, value=50)
            assessment_data["Scoring_Effectiveness"] = scoring_eff

        with col_a2:
            match_control = st.number_input("Match Control (1–5) (比賽掌控度)", min_value=1, max_value=5, step=1, value=3)
            assessment_data["Match_Control"] = match_control

        with col_a3:
            counters = st.number_input("Counters Conceded per Match (每場被反擊次數)", min_value=0, step=1, value=0)
            assessment_data["Counters_Conceded"] = counters

        with col_a4:
            penalties = st.number_input("Penalties per Match (每場受罰次數)", min_value=0, step=1, value=0)
            assessment_data["Penalties_Received"] = penalties

        st.divider()

        st.subheader("B. Competition Behaviour & Readiness (競賽行為與準備度)")
        st.markdown(
            "Focus: Response after scoring/penalties, decision-making when behind, and tolerance to international match tempo.（得分／受罰後反應、落後時決策、國際賽節奏承受度）"
        )

        comp_observation = st.text_area(
            "Coaching Observation (教練綜合觀察)",
            height=100,
            placeholder="Post-score reactions, decisions when trailing, pressure response, match-load tolerance.（比分變化時的反應、壓力與負荷承受度）",
            key="comp_obs",
        )
        assessment_data["Competition_Observation"] = comp_observation

        st.markdown("**Supporting Metrics (佐證數據)：**")
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)

        with col_b1:
            intl_matches = st.number_input("International Matches (累積國際賽場次)", min_value=0, step=1, value=0)
            assessment_data["Intl_Matches"] = intl_matches

        with col_b2:
            consistency = st.selectbox("Performance Consistency (表現穩定度)", ["High", "Moderate", "Low"])
            assessment_data["Performance_Consistency"] = consistency

        with col_b3:
            pressure_response = st.selectbox("Pressure Response (壓力反應)", ["Positive", "Neutral", "Negative"])
            assessment_data["Pressure_Response"] = pressure_response

        with col_b4:
            load_tolerance = st.selectbox("Match Load Tolerance (比賽負荷耐受度)", ["High", "Moderate", "Low"])
            assessment_data["Match_Load_Tolerance"] = load_tolerance

        st.divider()

        st.subheader("C. Health Status & Risk Flags (健康狀態與風險指標)")
        st.markdown(
            "Focus: Current physical/mental condition, injury history, fatigue level, and any red flags affecting performance or safety.（目前身心狀態、傷病與疲勞狀況）"
        )

        health_observation = st.text_area(
            "Health & Injury Status (健康與傷病狀況)",
            height=100,
            placeholder="Describe current injuries, fatigue, recovery, and any areas requiring close monitoring.（目前傷病、疲勞與需留意部位）",
            key="health_obs",
        )
        assessment_data["Health_Status"] = health_observation

        st.markdown("**Risk Flags (風險標記)：**")
        col_c1, col_c2, col_c3 = st.columns(3)

        with col_c1:
            injury_flag = st.selectbox("Injury Risk (傷病風險)", ["None", "Minor", "Moderate", "High"])
            assessment_data["Injury_Risk"] = injury_flag

        with col_c2:
            fatigue_flag = st.selectbox("Fatigue Level (疲勞程度)", ["Low", "Moderate", "High", "Critical"])
            assessment_data["Fatigue_Level"] = fatigue_flag

        with col_c3:
            mental_flag = st.selectbox("Mental Status (心理狀態)", ["Positive", "Stable", "Concerned"])
            assessment_data["Mental_Status"] = mental_flag

    else:
        # ─────────────────────────────────────────────────────────────
        # Poomsae Mode
        # ─────────────────────────────────────────────────────────────
        st.subheader("A. Technical Execution (品勢技術執行)")
        st.markdown(
            "Focus: Accuracy, power, stance stability, movement precision, and rhythm consistency.（動作正確度、力量、穩定度與節奏）"
        )

        col_tact1, col_tact2 = st.columns(2)

        with col_tact1:
            st.markdown("**Form Accuracy & Technique Quality (動作正確性與技術品質)**")
            form_accuracy = st.text_area(
                "Coaching Observation – Form (教練觀察－動作)",
                height=80,
                placeholder="Sequence accuracy, stance, hand and foot positions, body alignment.（動作順序、站姿、手腳位置與身體線條）",
                key="form_accuracy",
            )
            assessment_data["Form_Accuracy"] = form_accuracy

        with col_tact2:
            st.markdown("**Power & Delivery (力量與表現)**")
            power_delivery = st.text_area(
                "Coaching Observation – Power (教練觀察－力量)",
                height=80,
                placeholder="Kick power and height, hand speed, overall explosiveness.（踢擊力量與高度、出手速度與爆發力）",
                key="power_delivery",
            )
            assessment_data["Power_Delivery"] = power_delivery

        st.markdown("**Movement Flow & Rhythm (動作流暢度與節奏)**")
        tech_observation = st.text_area(
            "Coaching Observation (教練綜合觀察)",
            height=100,
            placeholder="Transitions, weight shift, balance, rhythm stability.（動作銜接、重心轉移、平衡與節奏穩定性）",
            key="poomsae_obs",
        )
        assessment_data["Technical_Observation"] = tech_observation

        st.markdown("**Supporting Metrics (佐證數據)：**")
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)

        with col_a1:
            accuracy_score = st.number_input("Technical Accuracy (1–10) (技術正確度)", min_value=1, max_value=10, step=1, value=5)
            assessment_data["Accuracy_Score"] = accuracy_score

        with col_a2:
            power_score = st.number_input("Power Level (1–10) (力量表現)", min_value=1, max_value=10, step=1, value=5)
            assessment_data["Power_Score"] = power_score

        with col_a3:
            flow_score = st.number_input("Movement Flow (1–10) (動作流暢度)", min_value=1, max_value=10, step=1, value=5)
            assessment_data["Flow_Score"] = flow_score

        with col_a4:
            rhythm_score = st.number_input("Rhythm Consistency (1–10) (節奏穩定度)", min_value=1, max_value=10, step=1, value=5)
            assessment_data["Rhythm_Score"] = rhythm_score

        st.divider()

        st.subheader("B. Competition Behaviour & Presentation (競賽行為與台風)")
        st.markdown("Focus: Stage presence, focus, recovery from mistakes, and consistency.（台風、專注度、失誤後恢復與穩定度）")

        comp_observation = st.text_area(
            "Coaching Observation (教練綜合觀察)",
            height=100,
            placeholder="Presence, confidence, recovery after errors, emotional control.（台風、自信、失誤後恢復與情緒管理）",
            key="poomsae_comp_obs",
        )
        assessment_data["Competition_Observation"] = comp_observation

        st.markdown("**Supporting Metrics (佐證數據)：**")
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)

        with col_b1:
            competition_score = st.number_input("Competition Experience (累積品勢比賽場次)", min_value=0, step=1, value=0)
            assessment_data["Competition_Exp"] = competition_score

        with col_b2:
            focus = st.selectbox("Focus Under Pressure (壓力下專注度)", ["Excellent", "Good", "Fair", "Poor"])
            assessment_data["Focus_Under_Pressure"] = focus

        with col_b3:
            consistency_poom = st.selectbox("Attempt Consistency (表現穩定度)", ["High", "Moderate", "Variable"])
            assessment_data["Attempt_Consistency"] = consistency_poom

        with col_b4:
            stage_presence = st.selectbox("Stage Presence (台風)", ["Strong", "Neutral", "Weak"])
            assessment_data["Stage_Presence"] = stage_presence

        st.divider()

        st.subheader("C. Health, Consistency & Risks (健康、訓練穩定度與風險)")
        st.markdown("Focus: Flexibility, strength limitations, movement quality, and training consistency.（柔軟度、肌力、動作品質與穩定性）")

        health_observation = st.text_area(
            "Health & Movement Status (健康與動作狀態)",
            height=100,
            placeholder="Joint mobility, strength imbalance, pain, recovery status.（關節活動度、肌力不平衡、疼痛與恢復狀況）",
            key="poomsae_health_obs",
        )
        assessment_data["Health_Status"] = health_observation

        st.markdown("**Risk Flags (風險標記)：**")
        col_c1, col_c2, col_c3 = st.columns(3)

        with col_c1:
            flexibility_flag = st.selectbox("Flexibility Concern (柔軟度疑慮)", ["None", "Minor", "Moderate", "High"])
            assessment_data["Flexibility_Concern"] = flexibility_flag

        with col_c2:
            strength_flag = st.selectbox("Strength/Power Concern (力量／爆發力疑慮)", ["None", "Minor", "Moderate", "High"])
            assessment_data["Strength_Concern"] = strength_flag

        with col_c3:
            mental_flag = st.selectbox("Mental Status (心理狀態)", ["Positive", "Stable", "Concerned"])
            assessment_data["Mental_Status"] = mental_flag

    st.divider()

    # ═══════════════════════════════════════════════════════════════════
    # 3. Executive Summary & Action Plan
    # ═══════════════════════════════════════════════════════════════════

    st.header("3️⃣ Executive Summary & Action Plan (總結與行動建議)")

    col_status1, col_status2 = st.columns(2)

    with col_status1:
        athlete_status = st.selectbox(
            "Overall Athlete Status (選手整體狀態)",
            ["Excellent", "Good", "Fair", "Needs Support"],
        )

    with col_status2:
        risk_flags = st.selectbox(
            "Risk Flag Summary (風險整體評估)",
            ["None", "Minor", "Moderate", "High"],
        )

    st.markdown("**Executive Summary (評估摘要)：**")
    exec_summary = st.text_area(
        "Summary of Assessment (2–3 sentences) (請以 2–3 句整理本次評估重點)",
        height=120,
        placeholder="Highlight key strengths, main areas for development, and readiness for upcoming events.（說明優勢、待加強面向與整體準備度）",
        key="exec_summary",
    )
    assessment_data["Executive_Summary"] = exec_summary

    st.markdown("**Recommended Next Actions (建議行動計畫)：**")
    next_actions = st.text_area(
        "Action Plan for Next 2–4 Weeks (未來 2–4 週行動計畫)",
        height=120,
        placeholder=(
            "- Technical / tactical focus areas（技術與戰術重點）\n"
            "- Training / competition adjustments（訓練與比賽規劃調整）\n"
            "- Recovery / injury prevention（恢復與傷害預防）\n"
            "- Mental preparation（心理與賽前準備）"
        ),
        key="next_actions",
    )
    assessment_data["Next_Actions"] = next_actions

    st.divider()

    col_submit1, col_submit2, col_submit3 = st.columns(3)
    with col_submit1:
        submit_btn = st.form_submit_button("✅ Submit & Upload (儲存並上傳)", use_container_width=True)
    with col_submit2:
        download_btn = st.form_submit_button("📄 Generate PDF Only (僅產生 PDF)", use_container_width=True)
    with col_submit3:
        st.form_submit_button("❌ Clear Form (清除表單)", type="secondary", use_container_width=True)

# ═══════════════════════════════════════════════════════════════════
# 4. Live Training Attendance (即時訓練出席率與圖表)
# ═══════════════════════════════════════════════════════════════════

st.divider()
st.header("4️⃣ Training Attendance Overview (訓練出席概況)")

if is_sparring:
    st.subheader("Sparring Training Attendance (對打訓練出席率)")
else:
    st.subheader("Poomsae Training Attendance (品勢訓練出席率)")

col_att1, col_att2 = st.columns(2)

with col_att1:
    live_sessions_required = st.number_input(
        "Sessions Required (this period) (本期應出席課次)",
        min_value=0,
        step=1,
        value=20,
        key="live_sessions_required",
    )
    live_sessions_attended = st.number_input(
        "Sessions Attended (實際出席課次)",
        min_value=0,
        step=1,
        value=18,
        key="live_sessions_attended",
    )

    if live_sessions_required > 0:
        live_attendance_rate = (live_sessions_attended / live_sessions_required) * 100
    else:
        live_attendance_rate = 0.0

    rate_label = "On track (進度正常)" if live_attendance_rate >= 85 else "Below target (出席率偏低)"
    st.metric("Attendance Rate (訓練出席率)", f"{live_attendance_rate:.1f}%", rate_label)

with col_att2:
    if live_sessions_required > 0:
        df_live = pd.DataFrame(
            {
                "Status (狀態)": ["Attended (已出席)", "Missed (缺席)"],
                "Sessions (課次)": [live_sessions_attended, max(live_sessions_required - live_sessions_attended, 0)],
            }
        )
        fig_live = px.pie(
            df_live,
            names="Status (狀態)",
            values="Sessions (課次)",
            hole=0.55,
            color="Status (狀態)",
            color_discrete_map={"Attended (已出席)": "#2ecc71", "Missed (缺席)": "#e74c3c"},
            title="Attendance Breakdown (出席分布)",
        )
        fig_live.update_layout(showlegend=True)
        st.plotly_chart(fig_live, use_container_width=True)

# 將即時出席率存入 assessment_data，供 PDF 與上傳使用
assessment_data["Attendance_Rate"] = live_attendance_rate

# ═══════════════════════════════════════════════════════════════════
# PDF Generation
# ═══════════════════════════════════════════════════════════════════


def generate_pdf_report(athlete_info, assessment_data, is_sparring):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)

    try:
        pdfmetrics.registerFont(TTFont("ChineseFont", "NotoSansTC-VariableFont_wght.ttf"))
        font_name = "ChineseFont"
    except Exception:
        font_name = "Helvetica"
        logger.warning("⚠️ Font file not found; Chinese text may not render correctly in PDF.")

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
    elements.append(Paragraph("新加坡跆拳道國家隊選手評估報告", title_style))
    elements.append(Spacer(1, 0.15 * inch))

    weight_val = athlete_info["weight_cat"] if is_sparring else "N/A"

    athlete_table_data = [
        [Paragraph("Athlete Name (選手姓名)", label_style), athlete_info["athlete_name"]],
        [Paragraph("Evaluation Date (評估日期)", label_style), athlete_info["eval_date"].strftime("%Y-%m-%d")],
        [Paragraph("Age Division (年齡組別)", label_style), athlete_info["age_group"]],
        [Paragraph("Gender (性別)", label_style), athlete_info["gender"]],
        [Paragraph("Weight Category (量級)", label_style), weight_val],
        [Paragraph("Context (參賽情境)", label_style), athlete_info["context"]],
        [Paragraph("Evaluation Type (評估類型)", label_style), athlete_info["eval_type"]],
        [Paragraph("Mode (評估模式)", label_style), "Sparring (對打)" if is_sparring else "Poomsae (品勢)"],
    ]

    athlete_table = Table(athlete_table_data, colWidths=[2.6 * inch, 2.9 * inch])
    athlete_table.setStyle(get_table_style_info())
    elements.append(athlete_table)
    elements.append(Spacer(1, 0.2 * inch))

    if is_sparring:
        elements.append(Paragraph("Technical & Tactical Observation (技術與戰術觀察)", heading_style))
        elements.append(Paragraph(assessment_data.get("Technical_Observation", "N/A"), body_style))
        elements.append(Spacer(1, 0.1 * inch))

        elements.append(Paragraph("Competition Behaviour (競賽行為表現)", heading_style))
        elements.append(Paragraph(assessment_data.get("Competition_Observation", "N/A"), body_style))
        elements.append(Spacer(1, 0.1 * inch))

        sparring_data = [
            ["Metric (指標)", "Value (數值)"],
            ["Scoring Effectiveness (%) (得分效率)", f"{assessment_data.get('Scoring_Effectiveness', 'N/A')}%"],
            ["Match Control (1–5) (比賽掌控度)", f"{assessment_data.get('Match_Control', 'N/A')}"],
            ["Counters Conceded per Match (每場被反擊次數)", f"{assessment_data.get('Counters_Conceded', 'N/A')}"],
            ["Penalties per Match (每場受罰次數)", f"{assessment_data.get('Penalties_Received', 'N/A')}"],
            ["Attendance Rate (%) (訓練出席率)", f"{assessment_data.get('Attendance_Rate', 0):.1f}%"],
        ]
        sparring_table = Table(sparring_data, colWidths=[3.1 * inch, 2.4 * inch])
        sparring_table.setStyle(get_table_style_header())
        elements.append(sparring_table)
        elements.append(Spacer(1, 0.15 * inch))
    else:
        elements.append(Paragraph("Technical Execution (品勢技術執行)", heading_style))
        elements.append(Paragraph(assessment_data.get("Technical_Observation", "N/A"), body_style))
        elements.append(Spacer(1, 0.1 * inch))

        elements.append(Paragraph("Competition Performance (競賽表現)", heading_style))
        elements.append(Paragraph(assessment_data.get("Competition_Observation", "N/A"), body_style))
        elements.append(Spacer(1, 0.1 * inch))

        poomsae_data = [
            ["Metric (指標)", "Value (數值)"],
            ["Technical Accuracy (技術正確度)", f"{assessment_data.get('Accuracy_Score', 'N/A')}"],
            ["Power Level (力量表現)", f"{assessment_data.get('Power_Score', 'N/A')}"],
            ["Movement Flow (動作流暢度)", f"{assessment_data.get('Flow_Score', 'N/A')}"],
            ["Rhythm Consistency (節奏穩定度)", f"{assessment_data.get('Rhythm_Score', 'N/A')}"],
            ["Attendance Rate (%) (訓練出席率)", f"{assessment_data.get('Attendance_Rate', 0):.1f}%"],
        ]
        poomsae_table = Table(poomsae_data, colWidths=[3.1 * inch, 2.4 * inch])
        poomsae_table.setStyle(get_table_style_header())
        elements.append(poomsae_table)
        elements.append(Spacer(1, 0.15 * inch))

    elements.append(Paragraph("Health Status & Risk Assessment (健康狀態與風險評估)", heading_style))
    elements.append(Paragraph(assessment_data.get("Health_Status", "N/A"), body_style))
    elements.append(Spacer(1, 0.1 * inch))

    elements.append(PageBreak())
    elements.append(Paragraph("Executive Summary & Action Plan (總結與行動建議)", heading_style))
    elements.append(Paragraph(f"Overall Athlete Status (整體狀態)：{athlete_info['athlete_status']}", body_style))
    elements.append(Spacer(1, 0.08 * inch))
    elements.append(Paragraph("Executive Summary (評估摘要)：", label_style))
    elements.append(Paragraph(athlete_info["exec_summary"], body_style))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("Recommended Next Actions (建議行動)：", label_style))
    elements.append(Paragraph(athlete_info["next_actions"], body_style))
    elements.append(Spacer(1, 0.2 * inch))

    footer_text = f"Report generated on {date.today().strftime('%Y-%m-%d')} – Singapore Taekwondo National Team"
    elements.append(Paragraph(footer_text, styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ═══════════════════════════════════════════════════════════════════
# Upload & Download
# ═══════════════════════════════════════════════════════════════════

if "pdf_buffer" not in st.session_state:
    st.session_state.pdf_buffer = None
if "pdf_filename" not in st.session_state:
    st.session_state.pdf_filename = "report.pdf"

if submit_btn or download_btn:
    if not athlete_name:
        st.error("⚠️ Please enter Athlete Name (請先輸入選手姓名)。")
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

    assessment_data["Eval_Mode"] = "Sparring (對打)" if is_sparring else "Poomsae (品勢)"
    assessment_data["Athlete_Status"] = athlete_status
    assessment_data["Risk_Flags"] = risk_flags

    try:
        pdf_buffer = generate_pdf_report(athlete_info, assessment_data, is_sparring)
        st.session_state.pdf_buffer = pdf_buffer
        st.session_state.pdf_filename = f"{athlete_name}_Assessment_{eval_date.strftime('%Y%m%d')}.pdf"
        st.success("📄 PDF report generated successfully.（PDF 報告已產生）")
    except Exception as e:
        st.error(f"❌ PDF generation failed: {str(e)}")
        logger.error(f"PDF error: {str(e)}", exc_info=True)

    if submit_btn:
        with st.spinner("🔄 Uploading data to Google Sheets, please wait…（資料上傳中）"):
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
                st.success(f"✅ Assessment for {athlete_name} has been uploaded.（已成功上傳）")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Upload failed: {str(e)}")
                logger.error(f"Upload error: {str(e)}", exc_info=True)

if st.session_state.pdf_buffer:
    st.divider()
    st.markdown("### 📥 Download Report (報告下載)")
    col_d1, col_d2, col_d3 = st.columns([2, 2, 2])

    with col_d1:
        st.download_button(
            label="📄 Download PDF Report (下載 PDF 報告)",
            data=st.session_state.pdf_buffer.getvalue(),
            file_name=st.session_state.pdf_filename,
            mime="application/pdf",
            key="pdf_download_btn",
            use_container_width=True,
        )

    with col_d2:
        st.info(f"Current file: {st.session_state.pdf_filename}")

    with col_d3:
        if st.button("🔄 Clear & Start New (清除並重新開始)", use_container_width=True):
            st.session_state.pdf_buffer = None
            st.session_state.pdf_filename = "report.pdf"
            st.rerun()

st.divider()
st.caption(
    "🥋 Singapore Taekwondo National Team – Athlete Scorecard ｜ Coaching observation-first, with data as structured support."
)
