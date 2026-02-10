import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import logging
from reportlab.lib.pagesizes import letter, A4
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
# 🥋 TAEKWONDO ATHLETE SCORECARD (Taiwan/Singapore) - DUAL MODE + PDF REPORT
# ═══════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Taekwondo Athlete Scorecard", page_icon="🥋", layout="wide")

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

st.title("🥋 Taekwondo Athlete Scorecard")
st.markdown(
    "<p class='report-note'>以教練觀察為核心，數據僅作輔助決策使用。</p>",
    unsafe_allow_html=True,
)

# --- Weight Categories ---
weight_categories = {
    "Senior (成人)": {
        "Male (男)": ["-54 kg", "-58 kg", "-63 kg", "-68 kg", "-74 kg", "-80 kg", "-87 kg", "+87 kg"],
        "Female (女)": ["-46 kg", "-49 kg", "-53 kg", "-57 kg", "-62 kg", "-67 kg", "-73 kg", "+73 kg"],
    },
    "Junior - Ages 15-17 (青少年)": {
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
    "Cadet - Ages 12-14 (少年)": {
        "Male (男)": ["-33 kg", "-37 kg", "-41 kg", "-45 kg", "-49 kg", "-53 kg", "-57 kg", "-61 kg", "-65 kg", "+65 kg"],
        "Female (女)": ["-29 kg", "-33 kg", "-37 kg", "-41 kg", "-44 kg", "-47 kg", "-51 kg", "-55 kg", "-59 kg", "+59 kg"],
    },
}

# ═══════════════════════════════════════════════════════════════════
# 評估模式
# ═══════════════════════════════════════════════════════════════════

eval_mode = st.radio(
    "📌 評估模式 (Evaluation Mode)",
    ["🥋 對打 (Sparring / Kyorugi)", "🎭 品勢 (Poomsae)"],
    horizontal=True,
    help="請選擇本次評估的項目。",
)

is_sparring = "對打" in eval_mode
is_poomsae = "品勢" in eval_mode

st.divider()

# ═══════════════════════════════════════════════════════════════════
# 1. 基本資料
# ═══════════════════════════════════════════════════════════════════

st.header("1️⃣ 選手基本資料 / Athlete Profile")

col1, col2, col3, col4 = st.columns(4)

with col1:
    athlete_name = st.text_input("選手姓名 (Athlete Name)")

with col2:
    eval_date = st.date_input("評估日期 (Evaluation Date)", datetime.today())

with col3:
    age_group = st.selectbox("年齡組別 (Age Division)", list(weight_categories.keys()))

with col4:
    gender = st.selectbox("性別 (Gender)", ["Male (男)", "Female (女)"])

col5, col6, col7 = st.columns(3)

with col5:
    if is_sparring:
        available_weights = weight_categories[age_group][gender]
        weight_cat = st.selectbox("量級 (Weight Category)", available_weights)
    else:
        weight_cat = "N/A"

with col6:
    context = st.selectbox("參賽情境 (Context)", ["國內賽 (Domestic)", "國際賽 (International)", "移地訓練 (Training Camp)"])

with col7:
    eval_type = st.selectbox("評估類型 (Evaluation Type)", ["例行評估 (Regular)", "賽事前後 (Event-based)", "集訓期間 (Boot camp)"])

st.divider()

# ═══════════════════════════════════════════════════════════════════
# 2. 技術 / 比賽 / 健康評估 (放在表單裡)
# ═══════════════════════════════════════════════════════════════════

st.header("2️⃣ 技術與比賽表現評估 / Assessment")

with st.form("assessment_form"):

    assessment_data = {}

    if is_sparring:
        # ─────────────────────────────────────────────────────────────
        # 對打模式
        # ─────────────────────────────────────────────────────────────
        st.subheader("A. 技術與戰術執行 (Technical & Tactical Execution)")
        st.markdown(
            "重點：戰術規劃、比賽掌控、面對不同對手風格的調整能力，以及壓力下技術穩定度。"
        )

        col_tact1, col_tact2 = st.columns(2)

        with col_tact1:
            st.markdown("**賽前戰術規劃 (Pre-match Tactical Planning)**")
            pregame_tactic = st.text_area(
                "教練觀察 (Pre-game observation)",
                height=80,
                placeholder="包含對手分析、戰術選擇、比賽計畫清晰度、心理/身體準備狀況等。",
                key="pregame_tactic",
            )
            assessment_data["Pre_Match_Tactic"] = pregame_tactic

        with col_tact2:
            st.markdown("**比賽中戰術執行 (In-match Tactical Execution)**")
            inmatch_tactic = st.text_area(
                "教練觀察 (In-match observation)",
                height=80,
                placeholder="例如：戰術執行連貫度、臨場調整、節奏掌握與反應速度等。",
                key="inmatch_tactic",
            )
            assessment_data["In_Match_Tactic"] = inmatch_tactic

        st.markdown("**比賽掌控與對手風格適應 (Match Control & Opponent-Style Adaptation)**")
        tech_observation = st.text_area(
            "教練綜合觀察 (Coaching Observation)",
            height=100,
            placeholder=(
                "例如：面對進攻型 / 拉距型 / 節奏型選手的對應方式，壓力下技術品質與比賽掌控能力等。"
            ),
            key="tech_obs",
        )
        assessment_data["Technical_Observation"] = tech_observation

        st.markdown("**佐證數據 (Supporting Evidence)：**")
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)

        with col_a1:
            scoring_eff = st.number_input("得分效率 (Scoring %) ", min_value=0, max_value=100, step=5, value=50)
            assessment_data["Scoring_Effectiveness"] = scoring_eff

        with col_a2:
            match_control = st.number_input("比賽掌控度 (1-5)", min_value=1, max_value=5, step=1, value=3)
            assessment_data["Match_Control"] = match_control

        with col_a3:
            counters = st.number_input("被反擊次數 / 每場 (Counters against)", min_value=0, step=1, value=0)
            assessment_data["Counters_Conceded"] = counters

        with col_a4:
            penalties = st.number_input("受罰次數 / 每場 (Penalties)", min_value=0, step=1, value=0)
            assessment_data["Penalties_Received"] = penalties

        st.divider()

        st.subheader("B. 比賽行為與準備度 (Competition Behaviour & Readiness)")
        st.markdown("重點：得分 / 受罰後反應、落後時決策品質、在高強度比賽節奏下的承受度。")

        comp_observation = st.text_area(
            "教練綜合觀察 (Coaching Observation)",
            height=100,
            placeholder="例如：比分落後時的決策、國際賽節奏適應度、情緒管理、比賽負荷耐受度等。",
            key="comp_obs",
        )
        assessment_data["Competition_Observation"] = comp_observation

        st.markdown("**佐證數據 (Supporting Evidence)：**")
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)

        with col_b1:
            intl_matches = st.number_input("累積國際賽出賽場次", min_value=0, step=1, value=0)
            assessment_data["Intl_Matches"] = intl_matches

        with col_b2:
            consistency = st.selectbox("表現穩定度", ["High (穩定)", "Moderate (中等)", "Low (不穩定)"])
            assessment_data["Performance_Consistency"] = consistency

        with col_b3:
            pressure_response = st.selectbox("壓力反應", ["Positive (正向)", "Neutral (中性)", "Negative (負向)"])
            assessment_data["Pressure_Response"] = pressure_response

        with col_b4:
            load_tolerance = st.selectbox("比賽負荷耐受度", ["High (高)", "Moderate (中等)", "Low (低)"])
            assessment_data["Match_Load_Tolerance"] = load_tolerance

        st.divider()

        st.subheader("C. 身體狀態與風險提示 (Athlete Status & Risk Flags)")
        st.markdown("重點：目前身體狀態、傷病史、疲勞程度與潛在風險。")

        health_observation = st.text_area(
            "健康與傷病狀況 (Health & Injury Status)",
            height=100,
            placeholder="請描述目前傷病、疲勞程度、恢復狀況及任何需要特別留意的部位與情況。",
            key="health_obs",
        )
        assessment_data["Health_Status"] = health_observation

        st.markdown("**風險標記 (Risk Flags)：**")
        col_c1, col_c2, col_c3 = st.columns(3)

        with col_c1:
            injury_flag = st.selectbox("傷病風險 (Injury Risk)", ["None (無)", "Minor (輕微)", "Moderate (中等)", "High (高)"])
            assessment_data["Injury_Risk"] = injury_flag

        with col_c2:
            fatigue_flag = st.selectbox("疲勞程度 (Fatigue Level)", ["Low (低)", "Moderate (中等)", "High (高)", "Critical (嚴重)"])
            assessment_data["Fatigue_Level"] = fatigue_flag

        with col_c3:
            mental_flag = st.selectbox("心理狀態 (Mental Status)", ["Positive (正向)", "Stable (穩定)", "Concerned (需留意)"])
            assessment_data["Mental_Status"] = mental_flag

    else:
        # ─────────────────────────────────────────────────────────────
        # 品勢模式
        # ─────────────────────────────────────────────────────────────
        st.subheader("A. 品勢技術執行 (Technical Execution)")
        st.markdown("重點：動作精準度、力量表現、站姿穩定度、動作連貫與節奏。")

        col_tact1, col_tact2 = st.columns(2)

        with col_tact1:
            st.markdown("**動作正確性與技術品質 (Form Accuracy & Technique Quality)**")
            form_accuracy = st.text_area(
                "教練觀察 (Form observation)",
                height=80,
                placeholder="如：動作順序是否正確、手腳位置、重心控制、身體線條等。",
                key="form_accuracy",
            )
            assessment_data["Form_Accuracy"] = form_accuracy

        with col_tact2:
            st.markdown("**力量與表現 (Power & Delivery)**")
            power_delivery = st.text_area(
                "教練觀察 (Power observation)",
                height=80,
                placeholder="如：踢擊高度與力量、出手速度、整體爆發力與動作張力。",
                key="power_delivery",
            )
            assessment_data["Power_Delivery"] = power_delivery

        st.markdown("**動作流暢與節奏穩定度 (Movement Flow & Rhythm)**")
        tech_observation = st.text_area(
            "教練綜合觀察 (Coaching Observation)",
            height=100,
            placeholder="如：動作銜接、重心轉移、平衡控制、節奏穩定性與過渡品質等。",
            key="poomsae_obs",
        )
        assessment_data["Technical_Observation"] = tech_observation

        st.markdown("**佐證數據 (Supporting Evidence)：**")
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)

        with col_a1:
            accuracy_score = st.number_input("技術正確度 (1-10)", min_value=1, max_value=10, step=1, value=5)
            assessment_data["Accuracy_Score"] = accuracy_score

        with col_a2:
            power_score = st.number_input("力量表現 (1-10)", min_value=1, max_value=10, step=1, value=5)
            assessment_data["Power_Score"] = power_score

        with col_a3:
            flow_score = st.number_input("動作流暢度 (1-10)", min_value=1, max_value=10, step=1, value=5)
            assessment_data["Flow_Score"] = flow_score

        with col_a4:
            rhythm_score = st.number_input("節奏穩定度 (1-10)", min_value=1, max_value=10, step=1, value=5)
            assessment_data["Rhythm_Score"] = rhythm_score

        st.divider()

        st.subheader("B. 競賽表現與台風 (Competition Behaviour & Presentation)")
        st.markdown("重點：台風、自信度、失誤後的恢復能力與穩定性。")

        comp_observation = st.text_area(
            "教練綜合觀察 (Coaching Observation)",
            height=100,
            placeholder="如：台風、自信、失誤後恢復、情緒管理與整體表現完整度等。",
            key="poomsae_comp_obs",
        )
        assessment_data["Competition_Observation"] = comp_observation

        st.markdown("**佐證數據 (Supporting Evidence)：**")
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)

        with col_b1:
            competition_score = st.number_input("累積品勢比賽場次", min_value=0, step=1, value=0)
            assessment_data["Competition_Exp"] = competition_score

        with col_b2:
            focus = st.selectbox("壓力下專注度", ["Excellent (優秀)", "Good (良好)", "Fair (普通)", "Poor (待加強)"])
            assessment_data["Focus_Under_Pressure"] = focus

        with col_b3:
            consistency_poom = st.selectbox("表現穩定度", ["High (穩定)", "Moderate (中等)", "Variable (易波動)"])
            assessment_data["Attempt_Consistency"] = consistency_poom

        with col_b4:
            stage_presence = st.selectbox("台風 (Stage Presence)", ["Strong (突出)", "Neutral (中性)", "Weak (不足)"])
            assessment_data["Stage_Presence"] = stage_presence

        st.divider()

        st.subheader("C. 身體狀態、訓練穩定度與風險 (Health, Consistency & Risks)")
        st.markdown("重點：柔軟度、力量限制、動作品質與整體訓練穩定性。")

        health_observation = st.text_area(
            "健康與動作狀況 (Health & Movement Status)",
            height=100,
            placeholder="如：關節活動度、肌力不平衡、疼痛部位、恢復情況與動作品質等。",
            key="poomsae_health_obs",
        )
        assessment_data["Health_Status"] = health_observation

        st.markdown("**風險標記 (Risk Flags)：**")
        col_c1, col_c2, col_c3 = st.columns(3)

        with col_c1:
            flexibility_flag = st.selectbox("柔軟度疑慮", ["None (無)", "Minor (輕微)", "Moderate (中等)", "High (明顯)"])
            assessment_data["Flexibility_Concern"] = flexibility_flag

        with col_c2:
            strength_flag = st.selectbox("力量 / 爆發力疑慮", ["None (無)", "Minor (輕微)", "Moderate (中等)", "High (明顯)"])
            assessment_data["Strength_Concern"] = strength_flag

        with col_c3:
            mental_flag = st.selectbox("心理狀態 (Mental Status)", ["Positive (正向)", "Stable (穩定)", "Concerned (需留意)"])
            assessment_data["Mental_Status"] = mental_flag

    st.divider()

    # ═══════════════════════════════════════════════════════════════════
    # 3. 總結與行動計畫
    # ═══════════════════════════════════════════════════════════════════

    st.header("3️⃣ 總結與後續建議 / Executive Summary & Action Plan")

    col_status1, col_status2 = st.columns(2)

    with col_status1:
        athlete_status = st.selectbox(
            "整體狀態判斷 (Overall Athlete Status)",
            ["🟢 優良 (Excellent)", "🟡 良好 (Good)", "🟠 可 (Fair)", "🔴 需協助 (Needs Support)"],
        )

    with col_status2:
        risk_flags = st.selectbox(
            "風險整體評估 (Risk Flag Summary)",
            ["🟢 無明顯風險", "🟡 輕微風險", "🟠 中度風險", "🔴 高風險"],
        )

    st.markdown("**評估摘要 (Executive Summary)：**")
    exec_summary = st.text_area(
        "請以 2–3 句說明本次評估重點",
        height=120,
        placeholder="建議說明選手目前優勢、主要待加強面向，以及與比賽/培訓相關的關鍵觀察。",
        key="exec_summary",
    )
    assessment_data["Executive_Summary"] = exec_summary

    st.markdown("**建議行動計畫 (Recommended Next Actions)：**")
    next_actions = st.text_area(
        "未來 2–4 週具體行動建議",
        height=120,
        placeholder=(
            "建議包含：\n"
            "- 技術與戰術重點\n- 訓練內容與比賽規劃調整\n"
            "- 恢復與傷害預防策略\n- 心理與賽前準備建議"
        ),
        key="next_actions",
    )
    assessment_data["Next_Actions"] = next_actions

    st.divider()

    col_submit1, col_submit2, col_submit3 = st.columns(3)
    with col_submit1:
        submit_btn = st.form_submit_button("✅ 儲存並上傳雲端 (Submit & Upload)", use_container_width=True)
    with col_submit2:
        download_btn = st.form_submit_button("📄 僅產生 PDF 報告 (Generate PDF)", use_container_width=True)
    with col_submit3:
        st.form_submit_button("❌ 清除表單 (Clear Form)", type="secondary", use_container_width=True)

# ═══════════════════════════════════════════════════════════════════
# 4. 出席率即時圖表（在表單外，即改即更新）
# ═══════════════════════════════════════════════════════════════════

st.divider()
st.header("4️⃣ 訓練出席概況 / Training Attendance Overview")

if is_sparring:
    st.subheader("對打訓練出席率 (Sparring Attendance)")
else:
    st.subheader("品勢訓練出席率 (Poomsae Attendance)")

col_att1, col_att2 = st.columns(2)

with col_att1:
    live_sessions_required = st.number_input(
        "本期應出席課次 (Sessions Required)",
        min_value=0,
        step=1,
        value=20,
        key="live_sessions_required",
    )
    live_sessions_attended = st.number_input(
        "實際出席課次 (Sessions Attended)",
        min_value=0,
        step=1,
        value=18,
        key="live_sessions_attended",
    )

    if live_sessions_required > 0:
        live_attendance_rate = (live_sessions_attended / live_sessions_required) * 100
    else:
        live_attendance_rate = 0.0

    rate_label = "✅ 目前進度正常" if live_attendance_rate >= 85 else "⚠️ 出席率偏低，需留意"
    st.metric("出席率 (Attendance Rate)", f"{live_attendance_rate:.1f}%", rate_label)

with col_att2:
    if live_sessions_required > 0:
        df_live = pd.DataFrame(
            {
                "狀態 (Status)": ["已出席 (Attended)", "缺席 (Missed)"],
                "課次 (Sessions)": [live_sessions_attended, max(live_sessions_required - live_sessions_attended, 0)],
            }
        )
        fig_live = px.pie(
            df_live,
            names="狀態 (Status)",
            values="課次 (Sessions)",
            hole=0.55,
            color="狀態 (Status)",
            color_discrete_map={"已出席 (Attended)": "#2ecc71", "缺席 (Missed)": "#e74c3c"},
            title="訓練出席分布 (Attendance Breakdown)",
        )
        fig_live.update_layout(showlegend=True)
        st.plotly_chart(fig_live, use_container_width=True)

# 把即時出席率存入 assessment_data，供 PDF / Google Sheet 使用
assessment_data["Attendance_Rate"] = live_attendance_rate

# ═══════════════════════════════════════════════════════════════════
# PDF 產生函式
# ═══════════════════════════════════════════════════════════════════


def generate_pdf_report(athlete_info, assessment_data, is_sparring):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)

    try:
        pdfmetrics.registerFont(TTFont("ChineseFont", "NotoSansTC-VariableFont_wght.ttf"))
        font_name = "ChineseFont"
    except Exception:
        font_name = "Helvetica"
        logger.warning("⚠️ 找不到字型檔，PDF 中文可能無法正常顯示。")

    styles = getSampleStyleSheet()
    styles["Normal"].fontName = font_name
    styles["Heading1"].fontName = font_name
    styles["Heading2"].fontName = font_name

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#1f4e78"),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName=font_name,
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
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

    elements.append(Paragraph("TAEKWONDO ATHLETE ASSESSMENT REPORT", title_style))
    elements.append(Paragraph("跆拳道選手評估報告", title_style))
    elements.append(Spacer(1, 0.15 * inch))

    weight_val = athlete_info["weight_cat"] if is_sparring else "N/A"

    athlete_table_data = [
        [Paragraph("姓名 (Name)", label_style), athlete_info["athlete_name"]],
        [Paragraph("評估日期 (Date)", label_style), athlete_info["eval_date"].strftime("%Y-%m-%d")],
        [Paragraph("年齡組別 (Age Division)", label_style), athlete_info["age_group"]],
        [Paragraph("性別 (Gender)", label_style), athlete_info["gender"]],
        [Paragraph("量級 (Weight Category)", label_style), weight_val],
        [Paragraph("情境 (Context)", label_style), athlete_info["context"]],
        [Paragraph("評估類型 (Evaluation Type)", label_style), athlete_info["eval_type"]],
        [Paragraph("模式 (Mode)", label_style), "Sparring (對打)" if is_sparring else "Poomsae (品勢)"],
    ]

    athlete_table = Table(athlete_table_data, colWidths=[2.4 * inch, 3.1 * inch])
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
            ["指標 (Metric)", "數值 (Value)"],
            ["得分效率 (Scoring %)", f"{assessment_data.get('Scoring_Effectiveness', 'N/A')}%"],
            ["比賽掌控度 (1-5)", f"{assessment_data.get('Match_Control', 'N/A')}"],
            ["被反擊次數 / 場", f"{assessment_data.get('Counters_Conceded', 'N/A')}"],
            ["受罰次數 / 場", f"{assessment_data.get('Penalties_Received', 'N/A')}"],
            ["訓練出席率 (Attendance %)", f"{assessment_data.get('Attendance_Rate', 0):.1f}%"],
        ]
        sparring_table = Table(sparring_data, colWidths=[3 * inch, 2.5 * inch])
        sparring_table.setStyle(get_table_style_header())
        elements.append(sparring_table)
        elements.append(Spacer(1, 0.15 * inch))
    else:
        elements.append(Paragraph("Technical Execution (技術執行)", heading_style))
        elements.append(Paragraph(assessment_data.get("Technical_Observation", "N/A"), body_style))
        elements.append(Spacer(1, 0.1 * inch))

        elements.append(Paragraph("Competition Performance (競賽表現)", heading_style))
        elements.append(Paragraph(assessment_data.get("Competition_Observation", "N/A"), body_style))
        elements.append(Spacer(1, 0.1 * inch))

        poomsae_data = [
            ["指標 (Metric)", "數值 (Value)"],
            ["技術正確度 (Accuracy)", f"{assessment_data.get('Accuracy_Score', 'N/A')}"],
            ["力量表現 (Power)", f"{assessment_data.get('Power_Score', 'N/A')}"],
            ["動作流暢度 (Flow)", f"{assessment_data.get('Flow_Score', 'N/A')}"],
            ["節奏穩定度 (Rhythm)", f"{assessment_data.get('Rhythm_Score', 'N/A')}"],
            ["訓練出席率 (Attendance %)", f"{assessment_data.get('Attendance_Rate', 0):.1f}%"],
        ]
        poomsae_table = Table(poomsae_data, colWidths=[3 * inch, 2.5 * inch])
        poomsae_table.setStyle(get_table_style_header())
        elements.append(poomsae_table)
        elements.append(Spacer(1, 0.15 * inch))

    elements.append(Paragraph("Health Status & Risk Assessment (健康狀態與風險評估)", heading_style))
    elements.append(Paragraph(assessment_data.get("Health_Status", "N/A"), body_style))
    elements.append(Spacer(1, 0.1 * inch))

    elements.append(PageBreak())
    elements.append(Paragraph("Executive Summary & Action Plan (總結與行動建議)", heading_style))
    elements.append(Paragraph(f"整體狀態 (Overall Status)：{athlete_info['athlete_status']}", body_style))
    elements.append(Spacer(1, 0.08 * inch))
    elements.append(Paragraph("評估摘要 (Summary)：", label_style))
    elements.append(Paragraph(athlete_info["exec_summary"], body_style))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("建議行動計畫 (Recommended Actions)：", label_style))
    elements.append(Paragraph(athlete_info["next_actions"], body_style))
    elements.append(Spacer(1, 0.2 * inch))

    footer_text = f"報告產出日期：{date.today().strftime('%Y-%m-%d')} ｜ 以教練專業觀察為主，數據為輔助參考。"
    elements.append(Paragraph(footer_text, styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ═══════════════════════════════════════════════════════════════════
# 上傳與下載
# ═══════════════════════════════════════════════════════════════════

if "pdf_buffer" not in st.session_state:
    st.session_state.pdf_buffer = None
if "pdf_filename" not in st.session_state:
    st.session_state.pdf_filename = "report.pdf"

if submit_btn or download_btn:
    if not athlete_name:
        st.error("⚠️ 請先輸入選手姓名。")
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

    assessment_data["Eval_Mode"] = "對打 (Sparring)" if is_sparring else "品勢 (Poomsae)"
    assessment_data["Athlete_Status"] = athlete_status
    assessment_data["Risk_Flags"] = risk_flags

    try:
        pdf_buffer = generate_pdf_report(athlete_info, assessment_data, is_sparring)
        st.session_state.pdf_buffer = pdf_buffer
        st.session_state.pdf_filename = f"{athlete_name}_Assessment_{eval_date.strftime('%Y%m%d')}.pdf"
        st.success("📄 PDF 報告已產生。")
    except Exception as e:
        st.error(f"❌ PDF 產生失敗：{str(e)}")
        logger.error(f"PDF error: {str(e)}", exc_info=True)

    if submit_btn:
        with st.spinner("🔄 資料上傳至 Google 試算表中，請稍候…"):
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                row_data = {
                    "Date (日期)": eval_date.strftime("%Y-%m-%d"),
                    "Name (姓名)": athlete_name,
                    "Age Group (年齡組)": age_group,
                    "Gender (性別)": gender,
                    "Weight (量級)": weight_cat if is_sparring else "N/A",
                    "Mode (模式)": "Sparring" if is_sparring else "Poomsae",
                    "Status (狀態)": athlete_status,
                    "Risk Flags (風險旗標)": risk_flags,
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
                st.success(f"✅ {athlete_name} 的評估紀錄已成功上傳。")
                st.balloons()
            except Exception as e:
                st.error(f"❌ 上傳失敗：{str(e)}")
                logger.error(f"Upload error: {str(e)}", exc_info=True)

if st.session_state.pdf_buffer:
    st.divider()
    st.markdown("### 📥 報告下載 (Download Report)")
    col_d1, col_d2, col_d3 = st.columns([2, 2, 2])

    with col_d1:
        st.download_button(
            label="📄 下載 PDF 報告",
            data=st.session_state.pdf_buffer.getvalue(),
            file_name=st.session_state.pdf_filename,
            mime="application/pdf",
            key="pdf_download_btn",
            use_container_width=True,
        )

    with col_d2:
        st.info(f"目前檔案：{st.session_state.pdf_filename}")

    with col_d3:
        if st.button("🔄 清除報告並重新開始", use_container_width=True):
            st.session_state.pdf_buffer = None
            st.session_state.pdf_filename = "report.pdf"
            st.rerun()

st.divider()
st.caption("🥋 Taekwondo Athlete Scorecard ｜ 以教練專業判斷為核心，結合客觀數據支援訓練與選手發展。")
