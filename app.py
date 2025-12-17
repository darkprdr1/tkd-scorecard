import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Singapore Athlete Scorecard",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== GOOGLE SHEETS CONFIG ====================
# Replace with your own service account credentials
SHEETS_CREDENTIALS = {
    "type": "service_account",
    "project_id": "YOUR_PROJECT_ID",
    "private_key_id": "YOUR_PRIVATE_KEY_ID",
    "private_key": "YOUR_PRIVATE_KEY",
    "client_email": "YOUR_CLIENT_EMAIL",
    "client_id": "YOUR_CLIENT_ID",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "YOUR_CERT_URL"
}

SHEET_ID = "YOUR_GOOGLE_SHEET_ID"

def get_gsheet_client():
    try:
        creds = Credentials.from_service_account_info(
            SHEETS_CREDENTIALS,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        return gspread.authorize(creds)
    except:
        st.warning("⚠️ Google Sheets 連線失敗，使用本機儲存")
        return None

# ==================== SIDEBAR - MODE SELECTION ====================
st.sidebar.title("🥋 評分卡模式")
mode = st.sidebar.radio(
    "選擇評估模式",
    ["季度評估 (Quarterly)", "Boot Camp 快速評估"]
)

# ==================== BOOT CAMP MODE ====================
if mode == "Boot Camp 快速評估":
    st.title("🏋️ Boot Camp 一週評估")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        athlete_name = st.text_input("選手名字", placeholder="e.g., 李小明")
    with col2:
        weight_class = st.selectbox("量級", ["-48kg", "-55kg", "-63kg", "-70kg", "+70kg"])
    with col3:
        age_group = st.selectbox("年齡組", ["U-21", "Senior", "Master"])
    
    col4, col5 = st.columns(2)
    with col4:
        bootcamp_name = st.text_input("Boot Camp 名稱", value=f"Boot Camp {datetime.now().strftime('%b %Y')}")
    with col5:
        bootcamp_date = st.date_input("評估日期", value=datetime.now())
    
    st.markdown("---")
    
    # ==================== FIVE CORE INDICATORS ====================
    st.subheader("📊 五大核心評估指標")
    
    # 1. Technical & Tactical
    with st.expander("1️⃣ Technical & Tactical（技術與戰術）", expanded=True):
        st.write("**評估範圍：** Pre-match planning、In-match execution、Match control、對手風格適應")
        technical_score = st.slider(
            "評分 (1-5)",
            1, 5, 3,
            key="technical",
            help="""
            5 = 五天內表現持續穩定，戰術執行 >85%
            4 = 多數表現良好，偶有執行偏差
            3 = 表現中等，戰術執行有起伏
            2 = 執行不穩，需要重點改進
            1 = 基本功不足，需要基礎訓練
            """
        )
        technical_note = st.text_area(
            "教練簡短觀察",
            placeholder="記錄該選手在技術和戰術層面的重點表現（100字內）",
            max_chars=100,
            key="technical_note"
        )
    
    # 2. Physical Capacity
    with st.expander("2️⃣ Physical Capacity（體能狀態）"):
        st.write("**評估範圍：** 訓練完成度、後期技術品質、疲勞恢復、傷病風險")
        physical_score = st.slider(
            "評分 (1-5)",
            1, 5, 3,
            key="physical",
            help="""
            5 = 五天全勤，後期技術品質無明顯下降，恢復快
            4 = 全勤或僅1次缺課，後期有輕微品質下降
            3 = 出席 >80%，中期明顯疲勞跡象
            2 = 多次缺課或疲勞過度，技術品質明顯衰退
            1 = 無法完成集訓強度，存在傷病風險
            """
        )
        physical_note = st.text_area(
            "備註（傷病、疲勞程度等）",
            placeholder="記錄體能或傷病相關狀況",
            max_chars=100,
            key="physical_note"
        )
    
    # 3. Competition Behavior
    with st.expander("3️⃣ Competition Behavior（競賽行為）"):
        st.write("**評估範圍：** 失分後反應、落後時決策、教練指令執行、情緒管理")
        behavior_score = st.slider(
            "評分 (1-5)",
            1, 5, 3,
            key="behavior",
            help="""
            5 = 臨場反應穩定，能快速調整，情緒控制好
            4 = 多數表現良好，偶有過度反應或延遲調整
            3 = 部分比賽反應不佳，需要提醒才能調整
            2 = 多場比賽出現過度衝動或消極反應
            1 = 臨場行為不穩定，無法自主調整
            """
        )
        behavior_note = st.text_area(
            "關鍵事件記錄",
            placeholder="記錄關鍵比賽的行為表現或特殊事件",
            max_chars=100,
            key="behavior_note"
        )
    
    # 4. Competition Readiness
    with st.expander("4️⃣ Competition Readiness（競賽準備度）"):
        st.write("**評估範圍：** 國際標準接近度、對手風格適應、高強度承受力、國際賽就緒度")
        readiness_score = st.slider(
            "評分 (1-5)",
            1, 5, 3,
            key="readiness",
            help="""
            5 = 完全符合國際標準，可直接參賽
            4 = 大部分符合，個別細節需調整
            3 = 接近國際標準，需要 1-2 場國際賽磨合
            2 = 有基礎但差距明顯，不建議立即參賽
            1 = 與國際標準差距大，需要長期培養
            """
        )
        readiness_note = st.text_area(
            "國際準備度評論",
            placeholder="當前水準 vs 國際對手差距",
            max_chars=100,
            key="readiness_note"
        )
    
    # 5. Attendance & Commitment
    with st.expander("5️⃣ Attendance & Commitment（出席與投入）"):
        st.write("**評估範圍：** 出席率、關鍵課程參與、訓練態度、與教練配合度")
        attendance_score = st.slider(
            "評分 (1-5)",
            1, 5, 3,
            key="attendance",
            help="""
            5 = 100% 出席，全程投入，主動配合
            4 = >95% 出席，僅輕微心不在焉
            3 = 80-95% 出席，或投入度波動
            2 = <80% 出席，或明顯缺乏專注
            1 = 多次缺課，態度不佳，配合度差
            """
        )
        attendance_note = st.text_area(
            "出席記錄",
            placeholder="缺課原因、特殊狀況等",
            max_chars=100,
            key="attendance_note"
        )
    
    st.markdown("---")
    
    # ==================== RISK FLAGS ====================
    st.subheader("⚠️ 風險標誌")
    risk_cols = st.columns(3)
    risks = []
    
    with risk_cols[0]:
        if st.checkbox("傷病風險"):
            risks.append("傷病風險")
        if st.checkbox("疲勞過度"):
            risks.append("疲勞過度")
    
    with risk_cols[1]:
        if st.checkbox("表現波動"):
            risks.append("表現波動")
        if st.checkbox("決策能力差"):
            risks.append("決策能力差")
    
    with risk_cols[2]:
        if st.checkbox("對手適應差"):
            risks.append("對手適應差")
        other_risk = st.text_input("其他風險", placeholder="如有其他風險，請輸入")
        if other_risk:
            risks.append(other_risk)
    
    st.markdown("---")
    
    # ==================== ATHLETE STATUS ====================
    st.subheader("🎯 選手定位")
    status = st.radio(
        "選手狀態",
        ["Ready Now", "Developing", "Re-assess"],
        format_func=lambda x: {
            "Ready Now": "✅ Ready Now — 可立即參加國際賽",
            "Developing": "🚀 Developing — 需要 1-2 場磨合賽",
            "Re-assess": "⚠️ Re-assess — 需要重新評估或特殊訓練"
        }[x]
    )
    
    st.markdown("---")
    
    # ==================== KEY TAKEAWAYS ====================
    st.subheader("📝 Boot Camp 重點成果")
    
    col_top = st.columns(3)
    with col_top[0]:
        st.write("**本次集訓的 TOP 3 收穫**")
        top1 = st.text_input("收穫 1", key="top1")
        top2 = st.text_input("收穫 2", key="top2")
        top3 = st.text_input("收穫 3", key="top3")
    
    with col_top[1]:
        st.write("**主要改進項目（下階段重點）**")
        improve1 = st.text_input("改進項 1", key="improve1")
        improve2 = st.text_input("改進項 2", key="improve2")
        improve3 = st.text_input("改進項 3", key="improve3")
    
    with col_top[2]:
        st.write("**建議下一步行動（2-4週）**")
        action1 = st.text_input("行動 1", key="action1")
        action2 = st.text_input("行動 2", key="action2")
        action3 = st.text_input("行動 3", key="action3")
    
    st.markdown("---")
    
    # ==================== FIVE-DIMENSION RADAR CHART ====================
    st.subheader("📊 五維雷達圖")
    
    scores_dict = {
        "技術與戰術": technical_score,
        "體能狀態": physical_score,
        "競賽行為": behavior_score,
        "競賽準備度": readiness_score,
        "出席與投入": attendance_score
    }
    
    # Create radar chart
    fig = go.Figure(data=go.Scatterpolar(
        r=list(scores_dict.values()),
        theta=list(scores_dict.keys()),
        fill='toself',
        name=athlete_name if athlete_name else "選手",
        line_color='#2080A0',
        fillcolor='rgba(32, 128, 160, 0.5)'
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=True,
        height=500,
        title=f"Boot Camp 評估 — {athlete_name or '選手'} ({bootcamp_date})"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ==================== SUMMARY CARD ====================
    st.markdown("---")
    st.subheader("📋 評估摘要")
    
    summary_col1, summary_col2 = st.columns(2)
    
    with summary_col1:
        st.metric("平均評分", f"{sum(scores_dict.values()) / 5:.1f} / 5.0")
        st.metric("最強項", max(scores_dict, key=scores_dict.get))
        st.metric("改進項", min(scores_dict, key=scores_dict.get))
    
    with summary_col2:
        st.metric("選手定位", status)
        st.metric("風險數", len(risks))
        if risks:
            st.write("**識別風險：**")
            for risk in risks:
                st.write(f"• {risk}")
    
    st.markdown("---")
    
    # ==================== SAVE TO GOOGLE SHEETS ====================
    col_save1, col_save2, col_save3 = st.columns([2, 1, 1])
    
    with col_save1:
        st.write("### 💾 儲存評估")
    
    with col_save2:
        if st.button("📤 儲存到 Google Sheets", use_container_width=True):
            # Prepare data for saving
            data_row = {
                "Timestamp": datetime.now().isoformat(),
                "Evaluation Type": "Boot Camp",
                "Athlete Name": athlete_name,
                "Weight Class": weight_class,
                "Age Group": age_group,
                "Boot Camp Name": bootcamp_name,
                "Boot Camp Date": str(bootcamp_date),
                "Technical & Tactical": technical_score,
                "Physical Capacity": physical_score,
                "Competition Behavior": behavior_score,
                "Competition Readiness": readiness_score,
                "Attendance & Commitment": attendance_score,
                "Status": status,
                "Risks": ", ".join(risks),
                "Technical Note": technical_note,
                "Physical Note": physical_note,
                "Behavior Note": behavior_note,
                "Readiness Note": readiness_note,
                "Attendance Note": attendance_note,
                "Top Achievements": f"{top1} | {top2} | {top3}",
                "Improvements": f"{improve1} | {improve2} | {improve3}",
                "Next Actions": f"{action1} | {action2} | {action3}"
            }
            
            st.success("✅ 評估已儲存！")
            st.json(data_row)
    
    with col_save3:
        if st.button("📊 檢視歷史", use_container_width=True):
            st.info("📊 歷史評估功能待開發")

# ==================== QUARTERLY MODE ====================
else:
    st.title("📅 季度評估")
    st.info("季度評估模式內容（保留原有功能）")
