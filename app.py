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
# Daily training first: attendance, monthly evaluation (technique / attitude / fitness), trends
# 以平時訓練為核心：點名、月度評估（技術／態度／體能）、趨勢追蹤
# ═══════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Singapore Taekwondo – Training Tracker", page_icon="🥋", layout="wide")

st.markdown(
    """
    <style>
    .zh { font-size: 0.55em; color: #8a8a8a; font-weight: 400; margin-left: 0.35em; }
    /* Chinese part of labels written as :gray[:small[...]] */
    .stMarkdownColoredText:has(> span[style*="font-size"]) { color: #9a9a9a !important; font-weight: 400; }
    .stMarkdownColoredText > span[style*="font-size"] { font-size: 0.78em !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

APP_DIR = Path(__file__).parent
LOCAL_DATA_DIR = APP_DIR / "data"


def L(en, zh):
    """Widget label: English first, Chinese in small grey text."""
    return f"{en} :gray[:small[{zh}]]"


def page_title(icon, en, zh):
    st.markdown(f"# {icon} {en}<span class='zh'>{zh}</span>", unsafe_allow_html=True)


def section(en, zh):
    st.markdown(f"### {en}<span class='zh'>{zh}</span>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Settings: evaluation items, options, thresholds
# ─────────────────────────────────────────────────────────────

DISCIPLINES = ["Sparring", "Poomsae"]
DISCIPLINE_ZH = {"Sparring": "對打", "Poomsae": "品勢"}
AGE_GROUPS = ["Senior", "Junior", "Cadet"]
AGE_GROUP_ZH = {"Senior": "成人", "Junior": "青少年", "Cadet": "少年"}
GENDERS = ["Male", "Female"]
SESSIONS = ["AM", "PM", "Evening"]

PRESENT, LATE, EXCUSED, ABSENT = "Present", "Late", "Excused", "Absent"
STATUSES = [PRESENT, LATE, EXCUSED, ABSENT]
STATUS_HELP = "Present 出席 / Late 遲到 / Excused 請假 / Absent 缺席"

INJURY_LEVELS = ["None", "Minor", "Moderate", "Serious"]
INJURY_FLAG_LEVELS = {"Moderate", "Serious"}
INJURY_HELP = "None 無 / Minor 輕微 / Moderate 中度 / Serious 嚴重"

RESULTS = ["Gold", "Silver", "Bronze", "5th or lower", "Participated"]

# (column, English, Chinese)
TECH_ITEMS = {
    "Sparring": [
        ("Tech_Footwork", "Footwork", "步法"),
        ("Tech_Kicking", "Kicking", "踢擊技術"),
        ("Tech_Combinations", "Combinations", "組合攻擊"),
        ("Tech_Defense", "Defense & Counter", "防守與反擊"),
        ("Tech_Distance", "Distance & Timing", "距離與時機"),
    ],
    "Poomsae": [
        ("Tech_Accuracy", "Accuracy", "動作正確度"),
        ("Tech_Power", "Power", "力量"),
        ("Tech_Balance", "Balance & Stance", "平衡與站姿"),
        ("Tech_Flow", "Flow & Rhythm", "流暢與節奏"),
        ("Tech_Expression", "Expression", "表現力"),
    ],
}
ATTITUDE_ITEMS = [
    ("Att_Focus", "Focus", "專注度"),
    ("Att_Effort", "Effort", "努力程度"),
    ("Att_Coachability", "Coachability", "接受指導"),
    ("Att_Discipline", "Discipline & Punctuality", "紀律與守時"),
    ("Att_Teamwork", "Teamwork", "團隊合作"),
]
ALL_TECH_COLS = [c for items in TECH_ITEMS.values() for c, _, _ in items]
ATT_COLS = [c for c, _, _ in ATTITUDE_ITEMS]
SCORE_COLS = ALL_TECH_COLS + ATT_COLS + ["Fitness"]

SCORE_GUIDE = "1 = Needs major work · 2 = Developing · 3 = Meets standard · 4 = Good · 5 = Excellent"

# Overview alert thresholds
ATTENDANCE_TARGET = 80  # %
ATTITUDE_MIN = 3.0
TECH_DROP = 0.5

# Columns of each worksheet
SHEETS = {
    "athletes": ["Name", "Discipline", "Age Group", "Gender", "Weight", "Active", "Notes"],
    "attendance": ["Date", "Session", "Name", "Status", "Recorded At"],
    "evaluations": ["Period", "Name", "Discipline"]
    + ALL_TECH_COLS
    + ATT_COLS
    + ["Fitness", "Injury", "Attendance Rate (%)", "Comment", "Next Goal", "Coach", "Recorded At"],
    "competitions": ["Date", "Name", "Event", "Division", "Result", "Notes", "Recorded At"],
}


def normalize(value, options):
    """Map older bilingual values (e.g. '出席 Present', 'Senior 成人') onto the English option."""
    text = str(value).strip()
    for opt in sorted(options, key=len, reverse=True):
        if opt in text:
            return opt
    return text


def disc_label(d):
    return f"{d} ({DISCIPLINE_ZH[d]})" if d in DISCIPLINE_ZH else str(d)


# ═══════════════════════════════════════════════════════════════════
# Storage: Google Sheets with a service account, otherwise local CSV
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
    """Google Sheets. New records are always appended, so simultaneous saves never overwrite each other."""

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
    """Local CSV files (used when no Google Sheets config is present – handy for testing)."""

    label = "Local CSV (test mode)"

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
# Data preparation
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
    df["Discipline"] = df["Discipline"].map(lambda v: normalize(v, DISCIPLINES))
    df["Age Group"] = df["Age Group"].map(lambda v: normalize(v, AGE_GROUPS))
    df["Gender"] = df["Gender"].map(lambda v: normalize(v, GENDERS))
    df["Active"] = df["Active"].astype(str).str.strip().str.lower().isin(["yes", "true", "1", ""])
    if active_only:
        df = df[df["Active"]]
    return df.reset_index(drop=True)


def load_attendance():
    df = load("attendance").copy()
    df["Session"] = df["Session"].map(lambda v: normalize(v, SESSIONS))
    df["Status"] = df["Status"].map(lambda v: normalize(v, STATUSES))
    df = df.sort_values("Recorded At").drop_duplicates(["Date", "Session", "Name"], keep="last")
    df["Period"] = df["Date"].astype(str).str[:7]
    return df


def load_evaluations():
    df = load("evaluations").copy()
    df = df.sort_values("Recorded At").drop_duplicates(["Period", "Name"], keep="last")
    for col in SCORE_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Injury"] = df["Injury"].map(lambda v: normalize(v, INJURY_LEVELS) if str(v).strip() else "")
    df["Tech_Avg"] = df[ALL_TECH_COLS].mean(axis=1).round(2)
    df["Att_Avg"] = df[ATT_COLS].mean(axis=1).round(2)
    return df.sort_values("Period").reset_index(drop=True)


def attendance_summary(att, period=None):
    """Per-athlete counts. Rate = (Present + Late) ÷ (Present + Late + Absent); Excused is not counted."""
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
    if discipline != "All":
        roster = roster[roster["Discipline"] == discipline]
    if age_group != "All":
        roster = roster[roster["Age Group"] == age_group]
    return roster


def tech_items_for(discipline):
    return TECH_ITEMS.get(discipline, [])


# ═══════════════════════════════════════════════════════════════════
# PDF (monthly report)
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
    """User input → Paragraph-safe text: escape < > &, keep line breaks."""
    if text is None or (isinstance(text, float) and np.isnan(text)):
        text = ""
    text = str(text).strip()
    if not text:
        return "—"
    return escape(text).replace("\r\n", "\n").replace("\n", "<br/>")


def bi(en, zh):
    """PDF label: English, followed by small grey Chinese."""
    return f"{escape(en)} <font size='7' color='#8a8a8a'>{escape(zh)}</font>"


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
        """Cells must already be Paragraph-safe (use rich() for user values, bi() for labels)."""
        t = Table([[Paragraph(str(v), cell) for v in row] for row in data], colWidths=widths)
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
        Paragraph(f"Monthly Training Report – {period} <font size='8' color='#8a8a8a'>月度訓練報告</font>", sub),
        Spacer(1, 0.2 * inch),
        table(
            [
                [bi("Athlete", "選手"), rich(athlete["Name"])],
                [bi("Discipline", "項目"), rich(disc_label(athlete["Discipline"]))],
                [bi("Age Group", "組別"), rich(athlete.get("Age Group", ""))],
                [bi("Gender", "性別"), rich(athlete.get("Gender", ""))],
                [bi("Weight", "量級"), rich(athlete.get("Weight", ""))],
            ],
            [1.8 * inch, 4.2 * inch],
            header=False,
        ),
    ]

    el.append(Paragraph(bi("Attendance", "出席"), h2))
    a = att_period
    el.append(
        table(
            [
                [bi("Sessions", "課次"), bi("Present", "出席"), bi("Late", "遲到"), bi("Excused", "請假"), bi("Absent", "缺席"), bi("Rate", "出席率")],
                [
                    int(a["Sessions"]),
                    int(a[PRESENT]),
                    int(a[LATE]),
                    int(a[EXCUSED]),
                    int(a[ABSENT]),
                    "—" if pd.isna(a["Rate"]) else f"{a['Rate']:.1f}%",
                ],
            ],
            [1.0 * inch] * 6,
        )
    )

    def score_rows(items):
        rows = [[bi("Item", "項目"), bi("This month", "本月"), bi("Last month", "上月")]]
        for col, en, zh in items:
            rows.append([bi(en, zh), fmt_score(cur[col] if cur is not None else None), fmt_score(prev[col] if prev is not None else None)])
        return rows

    el.append(Paragraph(bi("Technique (1–5)", "技術"), h2))
    el.append(table(score_rows(tech_items_for(athlete["Discipline"])), [3.0 * inch, 1.5 * inch, 1.5 * inch]))
    el.append(Paragraph(bi("Training Attitude (1–5)", "訓練態度"), h2))
    el.append(table(score_rows(ATTITUDE_ITEMS), [3.0 * inch, 1.5 * inch, 1.5 * inch]))

    el.append(Paragraph(bi("Fitness & Health", "體能與健康"), h2))
    el.append(
        table(
            [
                [bi("Fitness (1–5)", "體能"), fmt_score(cur["Fitness"] if cur is not None else None)],
                [bi("Injury", "傷病"), rich(cur["Injury"] if cur is not None else "")],
            ],
            [3.0 * inch, 3.0 * inch],
            header=False,
        )
    )

    el.append(Paragraph(bi("Coach Comment", "教練評語"), h2))
    el.append(Paragraph(rich(cur["Comment"] if cur is not None else ""), body))
    el.append(Paragraph(bi("Goal for Next Month", "下月目標"), h2))
    el.append(Paragraph(rich(cur["Next Goal"] if cur is not None else ""), body))

    if len(history):
        el.append(Paragraph(bi("Recent Trend", "近期趨勢"), h2))
        rows = [[bi("Month", "月份"), bi("Technique avg", "技術均分"), bi("Attitude avg", "態度均分"), bi("Attendance", "出席率")]]
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
# Sidebar
# ═══════════════════════════════════════════════════════════════════

PAGES = {
    "overview": ("🏠", "Team Overview", "團隊總覽"),
    "attendance": ("✅", "Attendance", "點名"),
    "evaluation": ("📝", "Monthly Evaluation", "月度評估"),
    "profile": ("📈", "Athlete Profile", "選手檔案"),
    "roster": ("👥", "Roster", "選手名單"),
}

with st.sidebar:
    st.title("🥋 Training Tracker")
    page = st.radio(
        "Menu",
        list(PAGES),
        format_func=lambda k: f"{PAGES[k][0]} {PAGES[k][1]}",
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Filters · 篩選")
    f_discipline = st.selectbox(L("Discipline", "項目"), ["All"] + DISCIPLINES, format_func=disc_label)
    f_age = st.selectbox(
        L("Age Group", "組別"), ["All"] + AGE_GROUPS, format_func=lambda a: f"{a} ({AGE_GROUP_ZH[a]})" if a in AGE_GROUP_ZH else a
    )
    st.divider()
    st.caption(f"Data source · 資料來源: {get_store().label}")
    if st.button("🔄 Reload data", use_container_width=True, help="重新載入資料"):
        load.clear()
        st.rerun()

try:
    roster_all = load_roster(active_only=False)
    roster = roster_all[roster_all["Active"]]
    attendance = load_attendance()
    evaluations = load_evaluations()
except Exception as e:
    st.error(f"❌ Could not load data（無法讀取資料）: {e}")
    logger.error("Load error", exc_info=True)
    st.stop()

roster_view = filter_roster(roster, f_discipline, f_age)


def need_roster():
    if roster.empty:
        st.info("No athletes yet — add them on the **👥 Roster** page first.（請先到選手名單新增選手）")
        st.stop()
    if roster_view.empty:
        st.info("No athletes match the current filters.（目前的篩選條件下沒有選手）")
        st.stop()


# ═══════════════════════════════════════════════════════════════════
# 🏠 Team Overview
# ═══════════════════════════════════════════════════════════════════

if page == "overview":
    page_title("🏠", "Team Overview", "團隊總覽")
    need_roster()

    period = st.selectbox(L("Month", "月份"), month_options())
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
            flags.append("Low attendance")
        if not pd.isna(att_avg) and att_avg < ATTITUDE_MIN:
            flags.append("Attitude")
        if not pd.isna(delta) and delta <= -TECH_DROP:
            flags.append("Technique drop")
        if injury in INJURY_FLAG_LEVELS:
            flags.append("Injury")
        if e is None:
            flags.append("Not evaluated")

        rows.append(
            {
                "Athlete": name,
                "Discipline": a["Discipline"],
                "Age Group": a["Age Group"],
                "Attendance": rate,
                "Sessions": int(att_sum["Sessions"].get(name, 0)),
                "Technique": tech,
                "Tech Δ": delta,
                "Attitude": att_avg,
                "Injury": injury,
                "Alerts": ", ".join(flags),
                "_n": len([f for f in flags if f != "Not evaluated"]),
            }
        )
    table_df = pd.DataFrame(rows).sort_values(["_n", "Attendance"], ascending=[False, True])
    flagged = table_df[table_df["_n"] > 0]
    table_df = table_df.drop(columns="_n")

    sessions_held = attendance[attendance["Period"] == period][["Date", "Session"]].drop_duplicates()
    att_in_view = att_sum[att_sum.index.isin(roster_view["Name"])]
    attended_total = att_in_view[PRESENT].sum() + att_in_view[LATE].sum()
    denom_total = attended_total + att_in_view[ABSENT].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(L("Athletes", "選手人數"), len(roster_view))
    c2.metric(L("Sessions this month", "本月課次"), len(sessions_held))
    c3.metric(L("Team attendance", "團隊出席率"), f"{attended_total / denom_total * 100:.1f}%" if denom_total else "—")
    c4.metric(L("Evaluated", "已評估"), f"{table_df['Technique'].notna().sum()} / {len(table_df)}")

    if len(flagged):
        st.warning(f"⚠️ {len(flagged)} athlete(s) need attention（需要留意）: " + ", ".join(flagged["Athlete"]))

    st.dataframe(
        table_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Athlete": st.column_config.TextColumn("Athlete", help="選手"),
            "Discipline": st.column_config.TextColumn("Discipline", help="項目"),
            "Age Group": st.column_config.TextColumn("Age Group", help="組別"),
            "Attendance": st.column_config.ProgressColumn("Attendance", help="出席率", min_value=0, max_value=100, format="%.0f%%"),
            "Sessions": st.column_config.NumberColumn("Sessions", help="課次"),
            "Technique": st.column_config.NumberColumn("Technique", help="技術均分", format="%.1f"),
            "Tech Δ": st.column_config.NumberColumn("Tech Δ", help="技術變化（較上月）", format="%+.1f"),
            "Attitude": st.column_config.NumberColumn("Attitude", help="態度均分", format="%.1f"),
            "Injury": st.column_config.TextColumn("Injury", help="傷病"),
            "Alerts": st.column_config.TextColumn("Alerts", help="提醒", width="medium"),
        },
    )
    st.caption(
        f"Alerts: attendance < {ATTENDANCE_TARGET}% · attitude avg < {ATTITUDE_MIN:g} · technique avg down ≥ {TECH_DROP:g} vs last month · "
        "moderate or serious injury. Attendance = (Present + Late) ÷ (Present + Late + Absent); Excused is not counted.  \n"
        f":small[提醒規則：出席率 < {ATTENDANCE_TARGET}%、態度均分 < {ATTITUDE_MIN:g}、技術均分比上月退步 ≥ {TECH_DROP:g}、傷病為中度以上。請假不計入出席率。]"
    )

    chart_df = table_df.dropna(subset=["Attendance"]).sort_values("Attendance")
    if len(chart_df):
        fig = px.bar(chart_df, x="Attendance", y="Athlete", orientation="h", range_x=[0, 100], title=f"Attendance – {period}", labels={"Attendance": "Attendance (%)"})
        fig.add_vline(x=ATTENDANCE_TARGET, line_dash="dash", line_color="#e74c3c")
        fig.update_layout(height=max(300, 24 * len(chart_df) + 100), yaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

    st.download_button(
        "⬇️ Download overview (CSV)",
        table_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"team_overview_{period}.csv",
        mime="text/csv",
        help="下載總覽 CSV",
    )


# ═══════════════════════════════════════════════════════════════════
# ✅ Attendance
# ═══════════════════════════════════════════════════════════════════

elif page == "attendance":
    page_title("✅", "Attendance", "點名")
    need_roster()

    c1, c2 = st.columns(2)
    att_date = c1.date_input(L("Date", "日期"), date.today())
    session = c2.selectbox(L("Session", "時段"), SESSIONS)
    date_str = att_date.strftime("%Y-%m-%d")

    existing = attendance[(attendance["Date"] == date_str) & (attendance["Session"] == session)]
    existing_status = dict(zip(existing["Name"], existing["Status"]))
    if len(existing):
        st.info(
            f"This session already has a record ({len(existing)} athletes). Saving again will replace it.  \n"
            ":small[這堂課已經點過名，修改後再儲存會覆蓋舊紀錄。]"
        )
    else:
        st.caption("Everyone starts as **Present** — just change the athletes who were late, excused or absent.  \n:small[預設全部出席，只要修改遲到、請假、缺席的選手即可。]")

    editor_df = pd.DataFrame(
        {
            "Athlete": roster_view["Name"],
            "Discipline": roster_view["Discipline"],
            "Age Group": roster_view["Age Group"],
            "Status": [existing_status.get(n, PRESENT) for n in roster_view["Name"]],
        }
    )
    edited = st.data_editor(
        editor_df,
        hide_index=True,
        use_container_width=True,
        disabled=["Athlete", "Discipline", "Age Group"],
        column_config={"Status": st.column_config.SelectboxColumn("Status", help=STATUS_HELP, options=STATUSES, required=True)},
        key=f"att_{date_str}_{session}_{f_discipline}_{f_age}",
    )

    counts = edited["Status"].value_counts()
    st.caption(" · ".join(f"{s}: {counts.get(s, 0)}" for s in STATUSES))

    if st.button("💾 Save attendance", type="primary", help="儲存點名"):
        ts = now_str()
        rows = [{"Date": date_str, "Session": session, "Name": r["Athlete"], "Status": r["Status"], "Recorded At": ts} for _, r in edited.iterrows()]
        try:
            append_rows("attendance", rows)
            st.success(f"✅ Saved attendance for {date_str} {session} ({len(rows)} athletes)")
        except Exception as e:
            st.error(f"❌ Save failed（儲存失敗）: {e}")
            logger.error("Attendance save error", exc_info=True)

    st.divider()
    period = date_str[:7]
    section(f"Attendance – {period}", "本月出席統計")
    summary = attendance_summary(load_attendance(), period)
    summary = summary[summary.index.isin(roster_view["Name"])].reset_index().rename(columns={"Name": "Athlete", "Rate": "Attendance"})
    if summary.empty:
        st.caption("No attendance recorded this month yet.（本月還沒有點名紀錄）")
    else:
        st.dataframe(
            summary.sort_values("Attendance"),
            hide_index=True,
            use_container_width=True,
            column_config={"Attendance": st.column_config.ProgressColumn("Attendance", help="出席率", min_value=0, max_value=100, format="%.0f%%")},
        )


# ═══════════════════════════════════════════════════════════════════
# 📝 Monthly Evaluation (whole squad in one table)
# ═══════════════════════════════════════════════════════════════════

elif page == "evaluation":
    page_title("📝", "Monthly Evaluation", "月度評估")
    need_roster()

    c1, c2, c3 = st.columns(3)
    period = c1.selectbox(L("Month", "月份"), month_options())
    default_disc = DISCIPLINES.index(f_discipline) if f_discipline in DISCIPLINES else 0
    discipline = c2.radio(L("Discipline", "項目"), DISCIPLINES, index=default_disc, horizontal=True, format_func=disc_label)
    coach = c3.text_input(L("Coach (optional)", "評估教練，選填"))

    group = roster_view[roster_view["Discipline"] == discipline]
    if group.empty:
        st.info(f"No {discipline} athletes match the current filters.（目前篩選條件下沒有{DISCIPLINE_ZH[discipline]}選手）")
        st.stop()

    st.caption(
        f"Scoring: {SCORE_GUIDE}. Only athletes with at least one score are saved; saving the same month again keeps the latest version.  \n"
        ":small[評分：1 需大幅加強 · 2 待加強 · 3 達標 · 4 良好 · 5 優秀。只有填了分數的選手會被儲存；同月重複儲存以最新為準。"
        "欄位前綴 T = 技術、A = 態度；把滑鼠移到欄位名稱上可看中文說明。]"
    )

    tech_items = tech_items_for(discipline)
    att_sum = attendance_summary(attendance, period)
    cur = evaluations[evaluations["Period"] == period].set_index("Name")
    prev = evaluations[evaluations["Period"] == prev_period(period)].set_index("Name")

    def existing(name, col, default=np.nan):
        return cur.loc[name, col] if name in cur.index else default

    data = {
        "Name": group["Name"].tolist(),
        "Attendance": [att_sum["Rate"].get(n, np.nan) for n in group["Name"]],
        "Last Tech": [prev.loc[n, "Tech_Avg"] if n in prev.index else np.nan for n in group["Name"]],
    }
    for col, _, _ in tech_items + ATTITUDE_ITEMS:
        data[col] = pd.to_numeric(pd.Series([existing(n, col) for n in group["Name"]]), errors="coerce").tolist()
    data["Fitness"] = pd.to_numeric(pd.Series([existing(n, "Fitness") for n in group["Name"]]), errors="coerce").tolist()
    data["Injury"] = [existing(n, "Injury", INJURY_LEVELS[0]) or INJURY_LEVELS[0] for n in group["Name"]]
    data["Comment"] = [existing(n, "Comment", "") for n in group["Name"]]
    data["Next Goal"] = [existing(n, "Next Goal", "") for n in group["Name"]]
    editor_df = pd.DataFrame(data)

    def score_cfg(label, zh):
        return st.column_config.NumberColumn(label, help=zh, min_value=1, max_value=5, step=1, format="%d")

    column_config = {
        "Name": st.column_config.TextColumn("Athlete", help="選手", width="small"),
        "Attendance": st.column_config.NumberColumn("Attendance", help="出席率（由點名紀錄自動計算）", format="%.0f%%", width="small"),
        "Last Tech": st.column_config.NumberColumn("Last Tech", help="上月技術均分（參考）", format="%.1f", width="small"),
        "Fitness": score_cfg("Fitness", "體能"),
        "Injury": st.column_config.SelectboxColumn("Injury", help=INJURY_HELP, options=INJURY_LEVELS, required=True, width="small"),
        "Comment": st.column_config.TextColumn("Coach Comment", help="教練短評", width="large"),
        "Next Goal": st.column_config.TextColumn("Next Goal", help="下月目標", width="medium"),
    }
    for col, en, zh in tech_items:
        column_config[col] = score_cfg(f"T · {en}", f"技術：{zh}")
    for col, en, zh in ATTITUDE_ITEMS:
        column_config[col] = score_cfg(f"A · {en}", f"態度：{zh}")

    if len(cur.index.intersection(group["Name"])):
        st.info("This month already has evaluations — the table is pre-filled with the last saved version.  \n:small[本月已有評估紀錄，表格已帶入上次儲存的內容。]")

    edited = st.data_editor(
        editor_df,
        hide_index=True,
        use_container_width=True,
        disabled=["Name", "Attendance", "Last Tech"],
        column_config=column_config,
        key=f"eval_{period}_{discipline}_{f_age}",
    )

    if st.button("💾 Save evaluations", type="primary", help="儲存評估"):
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
                "Attendance Rate (%)": r["Attendance"],
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
            st.warning("No scores entered — nothing was saved.（沒有任何選手填了分數，未儲存）")
        else:
            try:
                append_rows("evaluations", rows)
                skipped = len(edited) - len(rows)
                st.success(f"✅ Saved {period} evaluations for {len(rows)} athlete(s)" + (f" ({skipped} without scores skipped)" if skipped else ""))
            except Exception as e:
                st.error(f"❌ Save failed（儲存失敗）: {e}")
                logger.error("Evaluation save error", exc_info=True)


# ═══════════════════════════════════════════════════════════════════
# 📈 Athlete Profile
# ═══════════════════════════════════════════════════════════════════

elif page == "profile":
    page_title("📈", "Athlete Profile", "選手檔案")
    need_roster()

    name = st.selectbox(L("Athlete", "選手"), roster_view["Name"].tolist())
    athlete = roster_view[roster_view["Name"] == name].iloc[0]
    st.caption(
        " | ".join(
            str(x) for x in [disc_label(athlete["Discipline"]), athlete["Age Group"], athlete["Gender"], athlete["Weight"]] if str(x).strip()
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

    def delta(col):
        if latest is None or before is None or pd.isna(latest[col]) or pd.isna(before[col]):
            return None
        return f"{latest[col] - before[col]:+.1f}"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(L("Attendance this month", "本月出席率"), "—" if pd.isna(rate_now) else f"{rate_now:.0f}%")
    c2.metric(
        L(f"Technique ({latest['Period']})" if latest is not None else "Technique", "技術均分"),
        "—" if latest is None or pd.isna(latest["Tech_Avg"]) else f"{latest['Tech_Avg']:.1f}",
        delta("Tech_Avg"),
    )
    c3.metric(L("Attitude", "態度均分"), "—" if latest is None or pd.isna(latest["Att_Avg"]) else f"{latest['Att_Avg']:.1f}", delta("Att_Avg"))
    c4.metric(L("Injury", "傷病"), latest["Injury"] if latest is not None and latest["Injury"] else "—")

    if history.empty:
        st.info("No attendance or evaluations for this athlete yet.（這位選手還沒有點名或評估紀錄）")
    else:
        col_l, col_r = st.columns(2)
        with col_l:
            trend = history.melt(id_vars="Period", value_vars=["Tech_Avg", "Att_Avg"], var_name="Category", value_name="Score").dropna()
            trend["Category"] = trend["Category"].map({"Tech_Avg": "Technique", "Att_Avg": "Attitude"})
            if len(trend):
                fig = px.line(trend, x="Period", y="Score", color="Category", markers=True, range_y=[0.8, 5.2], title="Technique & Attitude Trend")
                fig.update_xaxes(type="category", title=None)
                st.plotly_chart(fig, use_container_width=True)
            rates = history.dropna(subset=["Rate"])
            if len(rates):
                fig = px.bar(rates, x="Period", y="Rate", range_y=[0, 100], title="Monthly Attendance", labels={"Rate": "Attendance (%)"})
                fig.add_hline(y=ATTENDANCE_TARGET, line_dash="dash", line_color="#e74c3c")
                fig.update_xaxes(type="category", title=None)
                st.plotly_chart(fig, use_container_width=True)
        with col_r:
            if latest is not None:
                items = tech_items_for(athlete["Discipline"]) + ATTITUDE_ITEMS
                labels = [en for _, en, _ in items]
                fig = go.Figure()
                if before is not None:
                    fig.add_trace(go.Scatterpolar(r=[before[c] for c, _, _ in items], theta=labels, fill="toself", name=before["Period"], opacity=0.45))
                fig.add_trace(go.Scatterpolar(r=[latest[c] for c, _, _ in items], theta=labels, fill="toself", name=latest["Period"]))
                fig.update_layout(polar=dict(radialaxis=dict(range=[0, 5], dtick=1)), title="Latest vs Previous Evaluation")
                st.plotly_chart(fig, use_container_width=True)

    if len(ev):
        section("Evaluation History", "評估紀錄")
        show = ev.sort_values("Period", ascending=False)[["Period", "Tech_Avg", "Att_Avg", "Fitness", "Injury", "Comment", "Next Goal", "Coach"]]
        st.dataframe(
            show.rename(columns={"Period": "Month", "Tech_Avg": "Technique", "Att_Avg": "Attitude", "Comment": "Coach Comment"}),
            hide_index=True,
            use_container_width=True,
        )

    with st.expander(L("🗓️ Recent attendance", "最近點名紀錄")):
        if att.empty:
            st.caption("No attendance records.（沒有點名紀錄）")
        else:
            st.dataframe(
                att.sort_values(["Date", "Session"], ascending=False)[["Date", "Session", "Status"]].head(40),
                hide_index=True,
                use_container_width=True,
            )

    with st.expander(L("🏆 Competition record (optional)", "比賽紀錄，選填")):
        comps = load("competitions").copy()
        comps["Result"] = comps["Result"].map(lambda v: normalize(v, RESULTS))
        comps = comps[comps["Name"] == name].sort_values("Date", ascending=False)
        if len(comps):
            st.dataframe(comps[["Date", "Event", "Division", "Result", "Notes"]], hide_index=True, use_container_width=True)
        with st.form("competition_form", clear_on_submit=True):
            cc1, cc2, cc3, cc4 = st.columns(4)
            comp_date = cc1.date_input(L("Date", "日期"), date.today())
            event = cc2.text_input(L("Event", "賽事名稱"))
            division = cc3.text_input(L("Division", "組別／量級"), value=str(athlete["Weight"]))
            result = cc4.selectbox(L("Result", "成績"), RESULTS)
            notes = st.text_input(L("Notes", "備註"))
            if st.form_submit_button("➕ Add competition"):
                if not event.strip():
                    st.error("Please enter the event name.（請輸入賽事名稱）")
                else:
                    append_rows(
                        "competitions",
                        [{"Date": comp_date.strftime("%Y-%m-%d"), "Name": name, "Event": event, "Division": division, "Result": result, "Notes": notes, "Recorded At": now_str()}],
                    )
                    st.success("Added.（已新增）")
                    st.rerun()

    st.divider()
    section("📄 Monthly Report (PDF)", "月報")
    periods = sorted(set(ev["Period"]) | set(monthly_rates.index), reverse=True) or [this_month]
    pdf_period = st.selectbox(L("Month", "月份"), periods)
    pdf_att = attendance_summary(att, pdf_period)
    pdf_att = pdf_att.loc[name] if name in pdf_att.index else pd.Series({**{s: 0 for s in STATUSES}, "Sessions": 0, "Rate": np.nan})
    try:
        pdf = generate_monthly_pdf(athlete, pdf_period, ev, pdf_att, history[history["Period"] <= pdf_period])
        st.download_button(
            "⬇️ Download report (PDF)",
            pdf.getvalue(),
            file_name=f"{name}_Training_Report_{pdf_period}.pdf",
            mime="application/pdf",
            type="primary",
            help="下載月報 PDF",
        )
    except Exception as e:
        st.error(f"❌ PDF generation failed（PDF 產生失敗）: {e}")
        logger.error("PDF error", exc_info=True)


# ═══════════════════════════════════════════════════════════════════
# 👥 Roster
# ═══════════════════════════════════════════════════════════════════

elif page == "roster":
    page_title("👥", "Roster", "選手名單")
    st.caption(
        "Add athletes in the last row. For athletes who leave, untick **Active** — their history is kept. "
        "⚠️ Avoid renaming athletes: old records are linked by name.  \n"
        ":small[在表格最下方新增選手；不再訓練的選手取消「Active」即可（保留歷史紀錄）。請盡量不要改名字，舊紀錄是用名字對應的。]"
    )

    editor_df = roster_all[SHEETS["athletes"]].copy()
    edited = st.data_editor(
        editor_df,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        column_config={
            "Name": st.column_config.TextColumn("Name", help="姓名", required=True),
            "Discipline": st.column_config.SelectboxColumn("Discipline", help="項目：Sparring 對打 / Poomsae 品勢", options=DISCIPLINES, required=True, default="Sparring"),
            "Age Group": st.column_config.SelectboxColumn(
                "Age Group", help="組別：Senior 成人 / Junior 青少年 / Cadet 少年", options=AGE_GROUPS, required=True, default=AGE_GROUPS[0]
            ),
            "Gender": st.column_config.SelectboxColumn("Gender", help="性別", options=GENDERS, required=True, default=GENDERS[0]),
            "Weight": st.column_config.TextColumn("Weight", help="量級，例如 -68 kg；品勢可留空"),
            "Active": st.column_config.CheckboxColumn("Active", help="在隊", default=True),
            "Notes": st.column_config.TextColumn("Notes", help="備註"),
        },
        key="roster_editor",
    )

    if st.button("💾 Save roster", type="primary", help="儲存名單"):
        edited = edited.copy()
        edited["Name"] = edited["Name"].fillna("").astype(str).str.strip()
        edited = edited[edited["Name"] != ""]
        dupes = edited["Name"][edited["Name"].duplicated()].unique()
        if len(dupes):
            st.error("Duplicate names（姓名重複）: " + ", ".join(dupes))
        else:
            edited["Active"] = edited["Active"].fillna(True).astype(bool)
            edited = edited.fillna("")
            try:
                overwrite_sheet("athletes", edited)
                st.success(f"✅ Roster saved ({len(edited)} athletes)")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Save failed（儲存失敗）: {e}")
                logger.error("Roster save error", exc_info=True)
