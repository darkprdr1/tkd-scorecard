import io
import logging
import os
from datetime import date, datetime
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ═══════════════════════════════════════════════════════════════════
# 🥋 SINGAPORE TAEKWONDO NATIONAL TEAM – TRAINING TRACKER
# 以平時訓練為核心：點名、月度評估（技術／態度／體能）、趨勢追蹤
# ═══════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Singapore Taekwondo – Training Tracker", page_icon="🥋", layout="wide")

APP_DIR = Path(__file__).parent
LOCAL_DATA_DIR = APP_DIR / "data"

# ─────────────────────────────────────────────────────────────
# 設定：評估項目、選項、門檻
# ─────────────────────────────────────────────────────────────

DISCIPLINES = ["Sparring", "Poomsae"]
DISCIPLINE_LABELS = {"Sparring": "對打 Sparring", "Poomsae": "品勢 Poomsae"}
AGE_GROUPS = ["Senior 成人", "Junior 青少年", "Cadet 少年"]
GENDERS = ["Male 男", "Female 女"]
SESSIONS = ["上午 AM", "下午 PM", "晚上 Evening"]

PRESENT, LATE, EXCUSED, ABSENT = "出席 Present", "遲到 Late", "請假 Excused", "缺席 Absent"
STATUSES = [PRESENT, LATE, EXCUSED, ABSENT]

INJURY_LEVELS = ["無 None", "輕微 Minor", "中度 Moderate", "嚴重 Serious"]
INJURY_FLAG_LEVELS = {"中度 Moderate", "嚴重 Serious"}

# (欄位名稱, 中文, 英文)
TECH_ITEMS = {
    "Sparring": [
        ("Tech_Footwork", "步法", "Footwork"),
        ("Tech_Kicking", "踢擊技術", "Kicking technique"),
        ("Tech_Combinations", "組合攻擊", "Combinations"),
        ("Tech_Defense", "防守與反擊", "Defense & counter"),
        ("Tech_Distance", "距離與時機", "Distance & timing"),
    ],
    "Poomsae": [
        ("Tech_Accuracy", "動作正確度", "Accuracy"),
        ("Tech_Power", "力量", "Power"),
        ("Tech_Balance", "平衡與站姿", "Balance & stance"),
        ("Tech_Flow", "流暢與節奏", "Flow & rhythm"),
        ("Tech_Expression", "表現力", "Expression"),
    ],
}
ATTITUDE_ITEMS = [
    ("Att_Focus", "專注度", "Focus"),
    ("Att_Effort", "努力程度", "Effort"),
    ("Att_Coachability", "接受指導", "Coachability"),
    ("Att_Discipline", "紀律與守時", "Discipline & punctuality"),
    ("Att_Teamwork", "團隊合作", "Teamwork"),
]
ALL_TECH_COLS = [c for items in TECH_ITEMS.values() for c, _, _ in items]
ATT_COLS = [c for c, _, _ in ATTITUDE_ITEMS]
SCORE_COLS = ALL_TECH_COLS + ATT_COLS + ["Fitness"]

SCORE_GUIDE = "1 = 需大幅加強　2 = 待加強　3 = 達標　4 = 良好　5 = 優秀"

# 總覽頁的警示門檻
ATTENDANCE_TARGET = 80  # %
ATTITUDE_MIN = 3.0
TECH_DROP = 0.5

# 每個工作表的欄位
SHEETS = {
    "athletes": ["Name", "Discipline", "Age Group", "Gender", "Weight", "Active", "Notes"],
    "attendance": ["Date", "Session", "Name", "Status", "Recorded At"],
    "evaluations": ["Period", "Name", "Discipline"]
    + ALL_TECH_COLS
    + ATT_COLS
    + ["Fitness", "Injury", "Attendance Rate (%)", "Comment", "Next Goal", "Coach", "Recorded At"],
    "competitions": ["Date", "Name", "Event", "Division", "Result", "Notes", "Recorded At"],
}


# ═══════════════════════════════════════════════════════════════════
# 資料儲存：有 service account 時用 Google Sheets，否則存本機 CSV
# ═══════════════════════════════════════════════════════════════════


def to_cell(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    if isinstance(value, (bool, np.bool_)):
        return "Yes" if value else "No"
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value) if isinstance(value, (float, np.floating)) else int(value)
    return str(value)


def ensure_columns(df, name):
    for col in SHEETS[name]:
        if col not in df.columns:
            df[col] = ""
    return df


class SheetsStore:
    """Google Sheets。新增資料一律用 append，不會覆蓋別人同時寫入的內容。"""

    label = "Google Sheets"

    def __init__(self, cfg):
        import gspread

        self._gspread = gspread
        cfg = dict(cfg)
        spreadsheet = str(cfg.pop("spreadsheet"))
        cfg.pop("worksheet", None)
        client = gspread.service_account_from_dict(cfg)
        self.sh = client.open_by_url(spreadsheet) if spreadsheet.startswith("http") else client.open_by_key(spreadsheet)

    def _ws(self, name):
        try:
            return self.sh.worksheet(name)
        except self._gspread.WorksheetNotFound:
            ws = self.sh.add_worksheet(title=name, rows=1000, cols=max(26, len(SHEETS[name])))
            ws.update(range_name="A1", values=[SHEETS[name]])
            return ws

    def read(self, name):
        values = self._ws(name).get_all_values()
        if not values:
            return pd.DataFrame(columns=SHEETS[name])
        header, rows = values[0], values[1:]
        width = len(header)
        rows = [r + [""] * (width - len(r)) if len(r) < width else r[:width] for r in rows]
        return ensure_columns(pd.DataFrame(rows, columns=header), name)

    def append(self, name, rows):
        ws = self._ws(name)
        header = ws.row_values(1)
        if not header:
            header = SHEETS[name]
            ws.update(range_name="A1", values=[header])
        missing = [c for c in SHEETS[name] if c not in header]
        if missing:
            header = header + missing
            if len(header) > ws.col_count:
                ws.add_cols(len(header) - ws.col_count)
            ws.update(range_name="A1", values=[header])
        ws.append_rows([[to_cell(r.get(c, "")) for c in header] for r in rows], value_input_option="RAW")

    def overwrite(self, name, df):
        ws = self._ws(name)
        cols = SHEETS[name]
        values = [cols] + [[to_cell(v) for v in row] for row in df[cols].itertuples(index=False)]
        ws.clear()
        ws.update(range_name="A1", values=values)


class LocalStore:
    """本機 CSV（沒有 Google Sheets 設定時使用，方便測試）。"""

    label = "本機 CSV（測試模式）"

    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)

    def _path(self, name):
        return self.folder / f"{name}.csv"

    def read(self, name):
        path = self._path(name)
        if not path.exists():
            return pd.DataFrame(columns=SHEETS[name])
        return ensure_columns(pd.read_csv(path, dtype=str, keep_default_na=False), name)

    def append(self, name, rows):
        df = pd.concat([self.read(name), pd.DataFrame(rows)], ignore_index=True)
        df.to_csv(self._path(name), index=False)

    def overwrite(self, name, df):
        df[SHEETS[name]].to_csv(self._path(name), index=False)


@st.cache_resource
def get_store():
    cfg = None
    try:
        cfg = st.secrets["connections"]["gsheets"]
    except Exception:
        pass
    if cfg and cfg.get("type") == "service_account":
        return SheetsStore(cfg)
    return LocalStore(LOCAL_DATA_DIR)


@st.cache_data(ttl=120, show_spinner=False)
def load(name):
    return get_store().read(name)


def append_rows(name, rows):
    get_store().append(name, rows)
    load.clear()


def overwrite_sheet(name, df):
    get_store().overwrite(name, df)
    load.clear()


# ─────────────────────────────────────────────────────────────
# 資料整理
# ─────────────────────────────────────────────────────────────


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def month_options(n=12):
    y, m = date.today().year, date.today().month
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return out


def prev_period(period):
    y, m = map(int, period.split("-"))
    y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return f"{y:04d}-{m:02d}"


def load_roster(active_only=True):
    df = load("athletes").copy()
    df["Name"] = df["Name"].astype(str).str.strip()
    df = df[df["Name"] != ""]
    df["Active"] = df["Active"].astype(str).str.strip().str.lower().isin(["yes", "true", "1", ""])
    if active_only:
        df = df[df["Active"]]
    return df.reset_index(drop=True)


def load_attendance():
    df = load("attendance").copy()
    df = df.sort_values("Recorded At").drop_duplicates(["Date", "Session", "Name"], keep="last")
    df["Period"] = df["Date"].astype(str).str[:7]
    return df


def load_evaluations():
    df = load("evaluations").copy()
    df = df.sort_values("Recorded At").drop_duplicates(["Period", "Name"], keep="last")
    for col in SCORE_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Tech_Avg"] = df[ALL_TECH_COLS].mean(axis=1).round(2)
    df["Att_Avg"] = df[ATT_COLS].mean(axis=1).round(2)
    return df.sort_values("Period").reset_index(drop=True)


def attendance_summary(att, period=None):
    """每位選手的出席統計。出席率 =（出席＋遲到）÷（出席＋遲到＋缺席），請假不計入分母。"""
    if period:
        att = att[att["Period"] == period]
    if att.empty:
        counts = pd.DataFrame(columns=STATUSES)
    else:
        counts = pd.crosstab(att["Name"], att["Status"])
    for s in STATUSES:
        if s not in counts.columns:
            counts[s] = 0
    counts = counts[STATUSES].astype(int)
    attended = counts[PRESENT] + counts[LATE]
    denom = (attended + counts[ABSENT]).replace(0, np.nan)
    counts["Sessions"] = counts[STATUSES].sum(axis=1)
    counts["Rate"] = (attended / denom * 100).round(1)
    return counts


def filter_roster(roster, discipline, age_group):
    if discipline != "全部 All":
        roster = roster[roster["Discipline"] == discipline]
    if age_group != "全部 All":
        roster = roster[roster["Age Group"] == age_group]
    return roster


def tech_items_for(discipline):
    return TECH_ITEMS.get(discipline, [])


# ═══════════════════════════════════════════════════════════════════
# PDF（月報）
# ═══════════════════════════════════════════════════════════════════

CJK_FONT_CANDIDATES = [
    (str(APP_DIR / "fonts" / "NotoSansTC-Regular.ttf"), 0),
    ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 0),
    ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 0),
    ("C:/Windows/Fonts/msjh.ttc", 0),
    ("C:/Windows/Fonts/mingliu.ttc", 0),
    ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0),
]


def get_pdf_font():
    if "CJK" in pdfmetrics.getRegisteredFontNames():
        return "CJK"
    for path, index in CJK_FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("CJK", path, subfontIndex=index))
                return "CJK"
            except Exception as e:
                logger.warning(f"Failed to load font {path}: {e}")
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
        return "MSung-Light"
    except Exception:
        return "Helvetica"


def rich(text):
    """使用者輸入 → Paragraph 文字：跳脫 < > &，保留換行。"""
    if text is None or (isinstance(text, float) and np.isnan(text)):
        text = ""
    text = str(text).strip()
    if not text:
        return "—"
    return escape(text).replace("\r\n", "\n").replace("\n", "<br/>")


def fmt_score(v):
    return "—" if v is None or pd.isna(v) else f"{v:g}"


def generate_monthly_pdf(athlete, period, evals, att_period, history):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    font = get_pdf_font()

    styles = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=styles["Title"], fontName=font, fontSize=18, textColor=colors.HexColor("#1f4e78"))
    sub = ParagraphStyle("S", parent=styles["Normal"], fontName=font, fontSize=11, alignment=TA_CENTER, textColor=colors.HexColor("#555555"))
    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"], fontName=font, fontSize=12.5, textColor=colors.HexColor("#2e5c8a"), spaceBefore=10, spaceAfter=6
    )
    body = ParagraphStyle("B", parent=styles["Normal"], fontName=font, fontSize=10, leading=15)
    cell = ParagraphStyle("C", parent=styles["Normal"], fontName=font, fontSize=9, leading=12)

    def table(data, widths, header=True):
        t = Table([[Paragraph(rich(v), cell) for v in row] for row in data], colWidths=widths)
        style = [
            ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#cccccc")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        if header:
            style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f0f7"))]
        else:
            style += [("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f0f7"))]
        t.setStyle(TableStyle(style))
        return t

    cur = evals[evals["Period"] == period]
    prev = evals[evals["Period"] == prev_period(period)]
    cur = cur.iloc[0] if len(cur) else None
    prev = prev.iloc[0] if len(prev) else None

    el = [
        Paragraph("SINGAPORE TAEKWONDO NATIONAL TEAM", title),
        Paragraph(f"Monthly Training Report 月度訓練報告 – {period}", sub),
        Spacer(1, 0.2 * inch),
        table(
            [
                ["Athlete 選手", athlete["Name"]],
                ["Discipline 項目", DISCIPLINE_LABELS.get(athlete["Discipline"], athlete["Discipline"])],
                ["Age Group 組別", athlete.get("Age Group", "")],
                ["Gender 性別", athlete.get("Gender", "")],
                ["Weight 量級", athlete.get("Weight", "")],
            ],
            [1.8 * inch, 4.2 * inch],
            header=False,
        ),
    ]

    el.append(Paragraph("Attendance 出席", h2))
    a = att_period
    el.append(
        table(
            [
                ["Sessions 課次", "Present 出席", "Late 遲到", "Excused 請假", "Absent 缺席", "Rate 出席率"],
                [
                    a["Sessions"],
                    a[PRESENT],
                    a[LATE],
                    a[EXCUSED],
                    a[ABSENT],
                    "—" if pd.isna(a["Rate"]) else f"{a['Rate']:.1f}%",
                ],
            ],
            [1.0 * inch] * 6,
        )
    )

    def score_rows(items):
        rows = [["Item 項目", "This month 本月", "Last month 上月"]]
        for col, zh, en in items:
            rows.append([f"{zh} {en}", fmt_score(cur[col] if cur is not None else None), fmt_score(prev[col] if prev is not None else None)])
        return rows

    el.append(Paragraph("Technique 技術（1–5）", h2))
    el.append(table(score_rows(tech_items_for(athlete["Discipline"])), [3.0 * inch, 1.5 * inch, 1.5 * inch]))
    el.append(Paragraph("Attitude 訓練態度（1–5）", h2))
    el.append(table(score_rows(ATTITUDE_ITEMS), [3.0 * inch, 1.5 * inch, 1.5 * inch]))

    el.append(Paragraph("Physical 體能與健康", h2))
    el.append(
        table(
            [
                ["Fitness 體能（1–5）", fmt_score(cur["Fitness"] if cur is not None else None)],
                ["Injury 傷病", cur["Injury"] if cur is not None else "—"],
            ],
            [3.0 * inch, 3.0 * inch],
            header=False,
        )
    )

    el.append(Paragraph("Coach Comment 教練評語", h2))
    el.append(Paragraph(rich(cur["Comment"] if cur is not None else ""), body))
    el.append(Paragraph("Next Month Goal 下月目標", h2))
    el.append(Paragraph(rich(cur["Next Goal"] if cur is not None else ""), body))

    if len(history):
        el.append(Paragraph("Recent Trend 近期趨勢", h2))
        rows = [["Period 月份", "Technique avg 技術均分", "Attitude avg 態度均分", "Attendance 出席率"]]
        for _, r in history.tail(6).iterrows():
            rate = r.get("Rate")
            rows.append([r["Period"], fmt_score(r["Tech_Avg"]), fmt_score(r["Att_Avg"]), "—" if pd.isna(rate) else f"{rate:.0f}%"])
        el.append(table(rows, [1.5 * inch] * 4))

    el.append(Spacer(1, 0.25 * inch))
    el.append(Paragraph(f"Generated {date.today():%Y-%m-%d} – Singapore Taekwondo National Team", cell))

    doc.build(el)
    buffer.seek(0)
    return buffer


# ═══════════════════════════════════════════════════════════════════
# 側邊欄
# ═══════════════════════════════════════════════════════════════════

PAGES = ["🏠 團隊總覽", "✅ 點名", "📝 月度評估", "📈 選手檔案", "👥 選手名單"]

with st.sidebar:
    st.title("🥋 Training Tracker")
    page = st.radio("功能 Menu", PAGES, label_visibility="collapsed")
    st.divider()
    st.caption("篩選 Filters")
    f_discipline = st.selectbox("項目 Discipline", ["全部 All"] + DISCIPLINES, format_func=lambda d: DISCIPLINE_LABELS.get(d, d))
    f_age = st.selectbox("組別 Age Group", ["全部 All"] + AGE_GROUPS)
    st.divider()
    st.caption(f"資料來源：{get_store().label}")
    if st.button("🔄 重新載入資料", use_container_width=True):
        load.clear()
        st.rerun()

try:
    roster_all = load_roster(active_only=False)
    roster = roster_all[roster_all["Active"]]
    attendance = load_attendance()
    evaluations = load_evaluations()
except Exception as e:
    st.error(f"❌ 無法讀取資料：{e}")
    logger.error("Load error", exc_info=True)
    st.stop()

roster_view = filter_roster(roster, f_discipline, f_age)


def need_roster():
    if roster.empty:
        st.info("還沒有選手資料，請先到「👥 選手名單」新增選手。")
        st.stop()
    if roster_view.empty:
        st.info("目前的篩選條件下沒有選手。")
        st.stop()


# ═══════════════════════════════════════════════════════════════════
# 🏠 團隊總覽
# ═══════════════════════════════════════════════════════════════════

if page == "🏠 團隊總覽":
    st.title("🏠 團隊總覽 Team Overview")
    need_roster()

    period = st.selectbox("月份 Month", month_options())
    att_sum = attendance_summary(attendance, period)
    cur = evaluations[evaluations["Period"] == period].set_index("Name")
    prev = evaluations[evaluations["Period"] == prev_period(period)].set_index("Name")

    rows = []
    for _, a in roster_view.iterrows():
        name = a["Name"]
        rate = att_sum["Rate"].get(name, np.nan)
        e = cur.loc[name] if name in cur.index else None
        p = prev.loc[name] if name in prev.index else None
        tech = e["Tech_Avg"] if e is not None else np.nan
        att_avg = e["Att_Avg"] if e is not None else np.nan
        delta = tech - p["Tech_Avg"] if (e is not None and p is not None) else np.nan
        injury = e["Injury"] if e is not None else ""

        flags = []
        if not pd.isna(rate) and rate < ATTENDANCE_TARGET:
            flags.append("出席率低")
        if not pd.isna(att_avg) and att_avg < ATTITUDE_MIN:
            flags.append("態度待關注")
        if not pd.isna(delta) and delta <= -TECH_DROP:
            flags.append("技術退步")
        if injury in INJURY_FLAG_LEVELS:
            flags.append("傷病")
        if e is None:
            flags.append("未評估")

        rows.append(
            {
                "選手": name,
                "項目": DISCIPLINE_LABELS.get(a["Discipline"], a["Discipline"]),
                "組別": a["Age Group"],
                "出席率": rate,
                "課次": int(att_sum["Sessions"].get(name, 0)),
                "技術均分": tech,
                "技術變化": delta,
                "態度均分": att_avg,
                "傷病": injury,
                "提醒": "、".join(flags),
                "_n": len([f for f in flags if f != "未評估"]),
            }
        )
    table_df = pd.DataFrame(rows).sort_values(["_n", "出席率"], ascending=[False, True]).drop(columns="_n")

    sessions_held = attendance[attendance["Period"] == period][["Date", "Session"]].drop_duplicates()
    att_in_view = att_sum[att_sum.index.isin(roster_view["Name"])]
    attended_total = att_in_view[PRESENT].sum() + att_in_view[LATE].sum()
    denom_total = attended_total + att_in_view[ABSENT].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("選手人數", len(roster_view))
    c2.metric("本月訓練課次", len(sessions_held))
    c3.metric("團隊出席率", f"{attended_total / denom_total * 100:.1f}%" if denom_total else "—")
    c4.metric("已完成評估", f"{table_df['技術均分'].notna().sum()} / {len(table_df)}")

    flagged = table_df[table_df["提醒"].str.replace("未評估", "").str.strip("、") != ""]
    if len(flagged):
        st.warning(f"⚠️ 有 {len(flagged)} 位選手需要留意：" + "、".join(flagged["選手"]))

    st.dataframe(
        table_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "出席率": st.column_config.ProgressColumn("出席率", min_value=0, max_value=100, format="%.0f%%"),
            "技術均分": st.column_config.NumberColumn("技術均分", format="%.1f"),
            "技術變化": st.column_config.NumberColumn("技術變化（較上月）", format="%+.1f"),
            "態度均分": st.column_config.NumberColumn("態度均分", format="%.1f"),
        },
    )
    st.caption(
        f"提醒規則：出席率 < {ATTENDANCE_TARGET}%、態度均分 < {ATTITUDE_MIN:g}、技術均分比上月退步 ≥ {TECH_DROP:g}、傷病為中度以上。"
        "出席率 =（出席＋遲到）÷（出席＋遲到＋缺席），請假不計入。"
    )

    chart_df = table_df.dropna(subset=["出席率"]).sort_values("出席率")
    if len(chart_df):
        fig = px.bar(chart_df, x="出席率", y="選手", orientation="h", range_x=[0, 100], title=f"{period} 出席率")
        fig.add_vline(x=ATTENDANCE_TARGET, line_dash="dash", line_color="#e74c3c")
        fig.update_layout(height=max(300, 24 * len(chart_df) + 100), yaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

    st.download_button(
        "⬇️ 下載總覽 CSV",
        table_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"team_overview_{period}.csv",
        mime="text/csv",
    )


# ═══════════════════════════════════════════════════════════════════
# ✅ 點名
# ═══════════════════════════════════════════════════════════════════

elif page == "✅ 點名":
    st.title("✅ 點名 Attendance")
    need_roster()

    c1, c2 = st.columns(2)
    att_date = c1.date_input("日期 Date", date.today())
    session = c2.selectbox("時段 Session", SESSIONS)
    date_str = att_date.strftime("%Y-%m-%d")

    existing = attendance[(attendance["Date"] == date_str) & (attendance["Session"] == session)]
    existing_status = dict(zip(existing["Name"], existing["Status"]))
    if len(existing):
        st.info(f"這堂課已經點過名（{len(existing)} 人），修改後再儲存會覆蓋舊紀錄。")
    else:
        st.caption("預設全部「出席」，只要修改遲到、請假、缺席的選手即可。")

    editor_df = pd.DataFrame(
        {
            "選手": roster_view["Name"],
            "項目": roster_view["Discipline"].map(lambda d: DISCIPLINE_LABELS.get(d, d)),
            "組別": roster_view["Age Group"],
            "狀態": [existing_status.get(n, PRESENT) for n in roster_view["Name"]],
        }
    )
    edited = st.data_editor(
        editor_df,
        hide_index=True,
        use_container_width=True,
        disabled=["選手", "項目", "組別"],
        column_config={"狀態": st.column_config.SelectboxColumn("狀態 Status", options=STATUSES, required=True)},
        key=f"att_{date_str}_{session}_{f_discipline}_{f_age}",
    )

    counts = edited["狀態"].value_counts()
    st.caption("　".join(f"{s}：{counts.get(s, 0)}" for s in STATUSES))

    if st.button("💾 儲存點名", type="primary"):
        ts = now_str()
        rows = [{"Date": date_str, "Session": session, "Name": r["選手"], "Status": r["狀態"], "Recorded At": ts} for _, r in edited.iterrows()]
        try:
            append_rows("attendance", rows)
            st.success(f"✅ 已儲存 {date_str} {session} 的點名（{len(rows)} 人）")
        except Exception as e:
            st.error(f"❌ 儲存失敗：{e}")
            logger.error("Attendance save error", exc_info=True)

    st.divider()
    period = date_str[:7]
    st.subheader(f"{period} 出席統計")
    summary = attendance_summary(load_attendance(), period)
    summary = summary[summary.index.isin(roster_view["Name"])].reset_index().rename(columns={"Name": "選手", "Sessions": "課次", "Rate": "出席率"})
    if summary.empty:
        st.caption("本月還沒有點名紀錄。")
    else:
        st.dataframe(
            summary.sort_values("出席率"),
            hide_index=True,
            use_container_width=True,
            column_config={"出席率": st.column_config.ProgressColumn("出席率", min_value=0, max_value=100, format="%.0f%%")},
        )


# ═══════════════════════════════════════════════════════════════════
# 📝 月度評估（整隊一次填）
# ═══════════════════════════════════════════════════════════════════

elif page == "📝 月度評估":
    st.title("📝 月度評估 Monthly Evaluation")
    need_roster()

    c1, c2, c3 = st.columns(3)
    period = c1.selectbox("月份 Month", month_options())
    default_disc = DISCIPLINES.index(f_discipline) if f_discipline in DISCIPLINES else 0
    discipline = c2.radio("項目 Discipline", DISCIPLINES, index=default_disc, horizontal=True, format_func=lambda d: DISCIPLINE_LABELS[d])
    coach = c3.text_input("評估教練 Coach（選填）")

    group = roster_view[roster_view["Discipline"] == discipline]
    if group.empty:
        st.info(f"目前篩選條件下沒有{DISCIPLINE_LABELS[discipline]}選手。")
        st.stop()

    st.caption(f"評分標準：{SCORE_GUIDE}。只要有填任一分數的選手才會被儲存；同一個月重複儲存會以最新的為準。")

    tech_items = tech_items_for(discipline)
    att_sum = attendance_summary(attendance, period)
    cur = evaluations[evaluations["Period"] == period].set_index("Name")
    prev = evaluations[evaluations["Period"] == prev_period(period)].set_index("Name")

    def existing(name, col, default=np.nan):
        return cur.loc[name, col] if name in cur.index else default

    data = {
        "Name": group["Name"].tolist(),
        "出席率": [att_sum["Rate"].get(n, np.nan) for n in group["Name"]],
        "上月技術": [prev.loc[n, "Tech_Avg"] if n in prev.index else np.nan for n in group["Name"]],
    }
    for col, _, _ in tech_items + ATTITUDE_ITEMS:
        data[col] = pd.to_numeric(pd.Series([existing(n, col) for n in group["Name"]]), errors="coerce").tolist()
    data["Fitness"] = pd.to_numeric(pd.Series([existing(n, "Fitness") for n in group["Name"]]), errors="coerce").tolist()
    data["Injury"] = [existing(n, "Injury", INJURY_LEVELS[0]) or INJURY_LEVELS[0] for n in group["Name"]]
    data["Comment"] = [existing(n, "Comment", "") for n in group["Name"]]
    data["Next Goal"] = [existing(n, "Next Goal", "") for n in group["Name"]]
    editor_df = pd.DataFrame(data)

    score_cfg = lambda zh, en: st.column_config.NumberColumn(zh, help=en, min_value=1, max_value=5, step=1, format="%d", width="small")
    column_config = {
        "Name": st.column_config.TextColumn("選手", width="small"),
        "出席率": st.column_config.NumberColumn("出席率", help="由點名紀錄自動計算", format="%.0f%%", width="small"),
        "上月技術": st.column_config.NumberColumn("上月技術", help="上個月技術均分（參考）", format="%.1f", width="small"),
        "Fitness": score_cfg("體能", "Fitness"),
        "Injury": st.column_config.SelectboxColumn("傷病", options=INJURY_LEVELS, required=True, width="small"),
        "Comment": st.column_config.TextColumn("教練短評", width="large"),
        "Next Goal": st.column_config.TextColumn("下月目標", width="medium"),
    }
    for col, zh, en in tech_items:
        column_config[col] = score_cfg(f"技·{zh}", en)
    for col, zh, en in ATTITUDE_ITEMS:
        column_config[col] = score_cfg(f"態·{zh}", en)

    if len(cur.index.intersection(group["Name"])):
        st.info("本月已有評估紀錄，表格已帶入上次儲存的內容。")

    edited = st.data_editor(
        editor_df,
        hide_index=True,
        use_container_width=True,
        disabled=["Name", "出席率", "上月技術"],
        column_config=column_config,
        key=f"eval_{period}_{discipline}_{f_age}",
    )

    if st.button("💾 儲存評估", type="primary"):
        ts = now_str()
        score_cols = [c for c, _, _ in tech_items + ATTITUDE_ITEMS] + ["Fitness"]
        rows = []
        for _, r in edited.iterrows():
            if r[score_cols].isna().all():
                continue
            row = {
                "Period": period,
                "Name": r["Name"],
                "Discipline": discipline,
                "Attendance Rate (%)": r["出席率"],
                "Injury": r["Injury"],
                "Comment": r["Comment"],
                "Next Goal": r["Next Goal"],
                "Coach": coach,
                "Recorded At": ts,
            }
            for c in score_cols:
                row[c] = r[c]
            rows.append(row)
        if not rows:
            st.warning("沒有任何選手填了分數，未儲存。")
        else:
            try:
                append_rows("evaluations", rows)
                skipped = len(edited) - len(rows)
                st.success(f"✅ 已儲存 {len(rows)} 位選手的 {period} 評估" + (f"（{skipped} 位未填分數，略過）" if skipped else ""))
            except Exception as e:
                st.error(f"❌ 儲存失敗：{e}")
                logger.error("Evaluation save error", exc_info=True)


# ═══════════════════════════════════════════════════════════════════
# 📈 選手檔案
# ═══════════════════════════════════════════════════════════════════

elif page == "📈 選手檔案":
    st.title("📈 選手檔案 Athlete Profile")
    need_roster()

    name = st.selectbox("選手 Athlete", roster_view["Name"].tolist())
    athlete = roster_view[roster_view["Name"] == name].iloc[0]
    st.caption(
        " ｜ ".join(
            str(x) for x in [DISCIPLINE_LABELS.get(athlete["Discipline"], athlete["Discipline"]), athlete["Age Group"], athlete["Gender"], athlete["Weight"]] if str(x).strip()
        )
    )

    ev = evaluations[evaluations["Name"] == name].copy()
    att = attendance[attendance["Name"] == name]
    monthly_rates = pd.Series(
        {p: attendance_summary(att, p)["Rate"].get(name, np.nan) for p in sorted(att["Period"].unique())},
        name="Rate",
        dtype=float,
    )
    history = ev[["Period", "Tech_Avg", "Att_Avg"]].merge(monthly_rates, left_on="Period", right_index=True, how="outer")
    history = history.sort_values("Period").reset_index(drop=True)

    this_month = month_options(1)[0]
    rate_now = monthly_rates.get(this_month, np.nan)
    latest = ev.iloc[-1] if len(ev) else None
    before = ev.iloc[-2] if len(ev) > 1 else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("本月出席率", "—" if pd.isna(rate_now) else f"{rate_now:.0f}%")
    c2.metric(
        f"技術均分（{latest['Period']}）" if latest is not None else "技術均分",
        "—" if latest is None or pd.isna(latest["Tech_Avg"]) else f"{latest['Tech_Avg']:.1f}",
        None if before is None or pd.isna(before["Tech_Avg"]) or pd.isna(latest["Tech_Avg"]) else f"{latest['Tech_Avg'] - before['Tech_Avg']:+.1f}",
    )
    c3.metric(
        "態度均分",
        "—" if latest is None or pd.isna(latest["Att_Avg"]) else f"{latest['Att_Avg']:.1f}",
        None if before is None or pd.isna(before["Att_Avg"]) or pd.isna(latest["Att_Avg"]) else f"{latest['Att_Avg'] - before['Att_Avg']:+.1f}",
    )
    c4.metric("傷病", latest["Injury"] if latest is not None and latest["Injury"] else "—")

    if history.empty:
        st.info("這位選手還沒有點名或評估紀錄。")
    else:
        col_l, col_r = st.columns(2)
        with col_l:
            trend = history.melt(id_vars="Period", value_vars=["Tech_Avg", "Att_Avg"], var_name="類別", value_name="分數").dropna()
            trend["類別"] = trend["類別"].map({"Tech_Avg": "技術均分", "Att_Avg": "態度均分"})
            if len(trend):
                fig = px.line(trend, x="Period", y="分數", color="類別", markers=True, range_y=[0.8, 5.2], title="技術／態度趨勢")
                fig.update_xaxes(type="category", title=None)
                st.plotly_chart(fig, use_container_width=True)
            rates = history.dropna(subset=["Rate"])
            if len(rates):
                fig = px.bar(rates, x="Period", y="Rate", range_y=[0, 100], title="每月出席率", labels={"Rate": "出席率 (%)"})
                fig.add_hline(y=ATTENDANCE_TARGET, line_dash="dash", line_color="#e74c3c")
                fig.update_xaxes(type="category", title=None)
                st.plotly_chart(fig, use_container_width=True)
        with col_r:
            if latest is not None:
                items = tech_items_for(athlete["Discipline"]) + ATTITUDE_ITEMS
                labels = [zh for _, zh, _ in items]
                fig = go.Figure()
                if before is not None:
                    fig.add_trace(go.Scatterpolar(r=[before[c] for c, _, _ in items], theta=labels, fill="toself", name=before["Period"], opacity=0.45))
                fig.add_trace(go.Scatterpolar(r=[latest[c] for c, _, _ in items], theta=labels, fill="toself", name=latest["Period"]))
                fig.update_layout(polar=dict(radialaxis=dict(range=[0, 5], dtick=1)), title="最新評估 vs 前一次")
                st.plotly_chart(fig, use_container_width=True)

    if len(ev):
        st.subheader("評估紀錄")
        show = ev.sort_values("Period", ascending=False)[["Period", "Tech_Avg", "Att_Avg", "Fitness", "Injury", "Comment", "Next Goal", "Coach"]]
        st.dataframe(
            show.rename(columns={"Period": "月份", "Tech_Avg": "技術均分", "Att_Avg": "態度均分", "Fitness": "體能", "Injury": "傷病", "Comment": "教練短評", "Next Goal": "下月目標", "Coach": "教練"}),
            hide_index=True,
            use_container_width=True,
        )

    with st.expander("🗓️ 最近點名紀錄"):
        if att.empty:
            st.caption("沒有點名紀錄。")
        else:
            st.dataframe(
                att.sort_values(["Date", "Session"], ascending=False)[["Date", "Session", "Status"]].head(40).rename(columns={"Date": "日期", "Session": "時段", "Status": "狀態"}),
                hide_index=True,
                use_container_width=True,
            )

    with st.expander("🏆 比賽紀錄（選填）"):
        comps = load("competitions")
        comps = comps[comps["Name"] == name].sort_values("Date", ascending=False)
        if len(comps):
            st.dataframe(comps[["Date", "Event", "Division", "Result", "Notes"]], hide_index=True, use_container_width=True)
        with st.form("competition_form", clear_on_submit=True):
            cc1, cc2, cc3, cc4 = st.columns(4)
            comp_date = cc1.date_input("日期", date.today())
            event = cc2.text_input("賽事名稱")
            division = cc3.text_input("組別／量級", value=str(athlete["Weight"]))
            result = cc4.selectbox("成績", ["金牌 Gold", "銀牌 Silver", "銅牌 Bronze", "第 5 名以後", "參賽 Participated"])
            notes = st.text_input("備註")
            if st.form_submit_button("➕ 新增比賽紀錄"):
                if not event.strip():
                    st.error("請輸入賽事名稱。")
                else:
                    append_rows(
                        "competitions",
                        [{"Date": comp_date.strftime("%Y-%m-%d"), "Name": name, "Event": event, "Division": division, "Result": result, "Notes": notes, "Recorded At": now_str()}],
                    )
                    st.success("已新增。")
                    st.rerun()

    st.divider()
    st.subheader("📄 月報 PDF")
    periods = sorted(set(ev["Period"]) | set(monthly_rates.index), reverse=True) or [this_month]
    pdf_period = st.selectbox("月份", periods)
    pdf_att = attendance_summary(att, pdf_period)
    pdf_att = pdf_att.loc[name] if name in pdf_att.index else pd.Series({**{s: 0 for s in STATUSES}, "Sessions": 0, "Rate": np.nan})
    try:
        pdf = generate_monthly_pdf(athlete, pdf_period, ev, pdf_att, history[history["Period"] <= pdf_period])
        st.download_button(
            "⬇️ 下載月報 PDF",
            pdf.getvalue(),
            file_name=f"{name}_Training_Report_{pdf_period}.pdf",
            mime="application/pdf",
            type="primary",
        )
    except Exception as e:
        st.error(f"❌ PDF 產生失敗：{e}")
        logger.error("PDF error", exc_info=True)


# ═══════════════════════════════════════════════════════════════════
# 👥 選手名單
# ═══════════════════════════════════════════════════════════════════

elif page == "👥 選手名單":
    st.title("👥 選手名單 Roster")
    st.caption("在表格最下方新增選手；不再訓練的選手取消「在隊」即可（保留歷史紀錄）。⚠️ 改名字會讓舊紀錄對不上，請盡量不要改。")

    editor_df = roster_all[SHEETS["athletes"]].copy()
    edited = st.data_editor(
        editor_df,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        column_config={
            "Name": st.column_config.TextColumn("姓名", required=True),
            "Discipline": st.column_config.SelectboxColumn("項目", options=DISCIPLINES, required=True, default="Sparring"),
            "Age Group": st.column_config.SelectboxColumn("組別", options=AGE_GROUPS, required=True, default=AGE_GROUPS[0]),
            "Gender": st.column_config.SelectboxColumn("性別", options=GENDERS, required=True, default=GENDERS[0]),
            "Weight": st.column_config.TextColumn("量級", help="例如 -68 kg；品勢可留空"),
            "Active": st.column_config.CheckboxColumn("在隊", default=True),
            "Notes": st.column_config.TextColumn("備註"),
        },
        key="roster_editor",
    )

    if st.button("💾 儲存名單", type="primary"):
        edited = edited.copy()
        edited["Name"] = edited["Name"].fillna("").astype(str).str.strip()
        edited = edited[edited["Name"] != ""]
        dupes = edited["Name"][edited["Name"].duplicated()].unique()
        if len(dupes):
            st.error("姓名重複：" + "、".join(dupes))
        else:
            edited["Active"] = edited["Active"].fillna(True).astype(bool)
            edited = edited.fillna("")
            try:
                overwrite_sheet("athletes", edited)
                st.success(f"✅ 名單已儲存（{len(edited)} 人）")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 儲存失敗：{e}")
                logger.error("Roster save error", exc_info=True)
