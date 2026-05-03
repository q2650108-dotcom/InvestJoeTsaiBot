from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def hydrate_env_from_streamlit_secrets() -> None:
    try:
        for key, value in st.secrets.items():
            if key not in os.environ:
                os.environ[key] = str(value)
    except Exception:
        return


hydrate_env_from_streamlit_secrets()

from investbot.config import get_settings
from investbot.data_sources.market_data import YahooMarketDataClient
from investbot.db.repositories import DailyAnalysisRepository
from investbot.services.analysis_engine import AnalysisEngine
from investbot.services.dashboard_service import DashboardService
from investbot.services.decision_support import DecisionSupportService
from investbot.services.event_risk_service import EventRiskService
from investbot.services.market_overview_service import MarketOverviewService
from investbot.services.portfolio_service import PortfolioService
from investbot.services.summary_service import SummaryService
from investbot.services.universe_builder import UniverseBuilder
from investbot.services.user_settings_service import UserSettingsService

st.set_page_config(page_title="Smart Swing Agent", layout="wide", initial_sidebar_state="expanded")

settings = get_settings()
chat_id = settings.telegram_allowed_chat_id
user_settings_service = UserSettingsService()
runtime_settings = user_settings_service.get_runtime_namespace(chat_id)
repo = DailyAnalysisRepository()
portfolio_service = PortfolioService()
market_data = YahooMarketDataClient()
dashboard_service = DashboardService(portfolio_service=portfolio_service, market_data=market_data)
decision_support = DecisionSupportService()
summary_service = SummaryService(repository=repo, decision_support=decision_support)
overview_service = MarketOverviewService(repository=repo, summary_service=summary_service, market_data=market_data)


COPY = {
    "zh-TW": {
        "app_title": "Smart Swing Agent",
        "app_caption": "先看總體市場，再看資金流與動能，最後再看個股。",
        "language": "語言",
        "view": "檢視",
        "dashboard": "總覽",
        "portfolio": "持股",
        "screener": "篩選",
        "health": "健康檢查",
        "run_analysis": "執行分析",
        "run_tw": "執行台股分析",
        "run_us": "執行美股分析",
        "analysis_done": "分析完成",
        "analysis_failed": "分析失敗",
        "records": "寫入筆數",
        "market_state": "市場狀態",
        "overall_trend": "整體趨勢",
        "sentiment": "市場情緒",
        "fear_greed": "恐慌 / 貪婪",
        "fear_greed_gauge": "情緒儀表",
        "breadth": "市場廣度",
        "momentum_zones": "動能區域",
        "cautions": "提醒",
        "macro_calendar": "重大事件行事曆",
        "market_overview": "市場總覽",
        "taiwan": "台股",
        "us": "美股",
        "candidates": "候選數",
        "actionable": "可行動",
        "safer": "相對安全延續",
        "focus_lists": "重點名單",
        "decision_cards": "決策卡",
        "core_pool": "核心池",
        "explore_pool": "觀察池",
        "watchlist": "觀察",
        "no_data": "目前沒有資料，先跑一次分析。",
        "vix": "VIX",
        "open_pnl": "未實現報酬",
        "win_rate": "勝率",
        "portfolio_curve": "資金曲線",
        "open_positions": "持有部位",
        "no_positions": "目前沒有持倉。",
        "no_closed_trades": "目前還沒有已平倉交易。",
        "stop_buffer": "停損緩衝",
        "market": "市場",
        "bucket": "分組",
        "all": "全部",
        "min_score": "最低綜合分數",
        "ticker": "代號",
        "company": "公司",
        "sector": "類股",
        "price_trend": "價格趨勢",
        "funnel_scores": "漏斗分數",
        "suggested_action": "建議動作",
        "rationale": "推薦理由",
        "risks": "主要風險",
        "forward_score": "前瞻分數",
        "forward_notes": "前瞻因子",
        "win_label": "勝率評估",
        "risk_label": "風險等級",
        "reward_risk": "風報比",
        "event_risk": "事件風險",
        "next_event": "下一事件",
        "universe": "池別",
        "score": "分數",
        "signal_type": "訊號",
        "unknown": "未知",
        "calm": "平穩",
        "neutral": "中性",
        "risk_off": "避險",
        "clear": "正常",
        "vix_zone": "VIX 區間",
        "vix_meaning": "VIX 解讀",
        "market_read": "市場判讀",
        "day1": "第 1 天",
        "day2": "第 2 天",
        "day3": "第 3 天以上",
        "core_tab": "核心",
        "explore_tab": "觀察",
        "risk_tab": "風險",
        "why_tab": "原因",
        "detail_tab": "細節",
        "settings_panel": "偏好設定",
        "save_settings": "儲存設定",
        "settings_saved": "設定已寫入資料庫",
        "high_risk_dates": "手動補充事件日期",
    },
    "en": {
        "app_title": "Smart Swing Agent",
        "app_caption": "Start with market context, then capital flow and momentum, then single names.",
        "language": "Language",
        "view": "View",
        "dashboard": "Dashboard",
        "portfolio": "Portfolio",
        "screener": "Screener",
        "health": "Health",
        "run_analysis": "Run Analysis",
        "run_tw": "Run Taiwan Analysis",
        "run_us": "Run US Analysis",
        "analysis_done": "Analysis completed",
        "analysis_failed": "Analysis failed",
        "records": "Records written",
        "market_state": "Market State",
        "overall_trend": "Overall Trend",
        "sentiment": "Sentiment",
        "fear_greed": "Fear / Greed",
        "fear_greed_gauge": "Sentiment Gauge",
        "breadth": "Breadth",
        "momentum_zones": "Momentum Zones",
        "cautions": "Cautions",
        "macro_calendar": "Macro Calendar",
        "market_overview": "Market Overview",
        "taiwan": "Taiwan",
        "us": "US",
        "candidates": "Candidates",
        "actionable": "Actionable",
        "safer": "Safer Follow-Through",
        "focus_lists": "Focus Lists",
        "decision_cards": "Decision Cards",
        "core_pool": "Core Pool",
        "explore_pool": "Explore Pool",
        "watchlist": "Watchlist",
        "no_data": "No data yet. Run an analysis first.",
        "vix": "VIX",
        "open_pnl": "Open PnL",
        "win_rate": "Win Rate",
        "portfolio_curve": "Portfolio Curve",
        "open_positions": "Open Positions",
        "no_positions": "No open positions.",
        "no_closed_trades": "No closed trades yet.",
        "stop_buffer": "Stop Buffer",
        "market": "Market",
        "bucket": "Bucket",
        "all": "All",
        "min_score": "Minimum Composite Score",
        "ticker": "Ticker",
        "company": "Company",
        "sector": "Sector",
        "price_trend": "Price Trend",
        "funnel_scores": "Funnel Scores",
        "suggested_action": "Suggested Action",
        "rationale": "Why It Ranks",
        "risks": "Main Risks",
        "forward_score": "Forward Score",
        "forward_notes": "Forward Factors",
        "win_label": "Win-Rate View",
        "risk_label": "Risk Level",
        "reward_risk": "Reward / Risk",
        "event_risk": "Event Risk",
        "next_event": "Next Event",
        "universe": "Universe",
        "score": "Score",
        "signal_type": "Signal",
        "unknown": "Unknown",
        "calm": "Calm",
        "neutral": "Neutral",
        "risk_off": "Risk-Off",
        "clear": "Clear",
        "vix_zone": "VIX Zone",
        "vix_meaning": "VIX Meaning",
        "market_read": "Market Read",
        "day1": "Day 1 Early",
        "day2": "Day 2 Building",
        "day3": "Day 3+ Safer",
        "core_tab": "Core",
        "explore_tab": "Explore",
        "risk_tab": "Risk",
        "why_tab": "Why",
        "detail_tab": "Detail",
        "settings_panel": "Preferences",
        "save_settings": "Save Settings",
        "settings_saved": "Settings saved to database",
        "high_risk_dates": "Manual Fallback Event Dates",
    },
}


ZH_DECISION_TEXT = {
    "Institutional buying has persisted for 3 sessions.": "法人買超已連續 3 天。",
    "Institutional buying has persisted for 4 sessions.": "法人買超已連續 4 天。",
    "Institutional buying has persisted for 5 sessions.": "法人買超已連續 5 天。",
    "Institutional buying is building into a second session.": "法人買超延續到第 2 天，動能正在建立。",
    "Institutional buying has just turned positive.": "法人買盤剛轉正。",
    "Relative strength is decisively above the market benchmark.": "相對強度明顯優於市場基準。",
    "Relative strength is supportive versus the benchmark.": "相對強度優於基準，屬於正向支持。",
    "Price location is constructive and not excessively extended.": "價格位階健康，且未過度乖離。",
    "Entry quality is acceptable if execution stays disciplined.": "進場品質尚可，前提是執行紀律要嚴格。",
    "The market regime is supportive for trend-following entries.": "市場環境偏向有利順勢操作。",
    "The broader market is neutral, so follow-through may be slower.": "大盤偏中性，延續力可能較慢。",
    "The broader market is risk-off, so hit rates can fall quickly.": "市場偏避險，命中率可能快速下滑。",
    "This idea is in the Explore pool, so it should not outrank core large-cap names.": "此標的屬於觀察池，不應優先於核心大型股。",
    "This name belongs to the core monitoring pool.": "此標的屬於核心追蹤池。",
    "Event risk is manageable but still worth monitoring.": "事件風險可控，但仍需持續追蹤。",
    "No major risk flags are active right now, but standard stop discipline still applies.": "目前無重大風險警訊，但仍需遵守停損紀律。",
    "The current signal does not yet have enough stacked evidence.": "目前訊號累積證據仍不足。",
    "Normal position sizing or staged entries on minor pullbacks.": "可採正常部位，或在小幅拉回時分批進場。",
    "Pilot size first, then add if confirmation holds.": "先用試單部位，確認延續後再加碼。",
    "Observe only until the odds improve.": "先觀察，等待勝率提升再行動。",
    "Small trial size only; keep core capital focused on large caps.": "僅小部位試單，核心資金維持在大型股。",
    "High Conviction Core": "高把握核心標的",
    "Actionable Setup": "可執行設定",
    "Watch and Wait": "觀望等待",
    "High": "高",
    "Medium-High": "中高",
    "Medium-Low": "中低",
    "Medium": "中",
    "Medium-High": "中高",
    "Favorable": "風報比佳",
    "Balanced": "風報平衡",
    "Unclear": "風報不明",
}


def current_language() -> str:
    runtime_language = getattr(runtime_settings, "app_language", "")
    if runtime_language:
        return str(runtime_language)
    try:
        accept = str(st.context.headers.get("Accept-Language", "")).lower()
    except Exception:
        accept = ""
    if "zh" in accept:
        return "zh-TW"
    return os.environ.get("APP_LANGUAGE", "zh-TW")


LANG = current_language()
TEXT = COPY["zh-TW"] | COPY.get(LANG, {})


def t(key: str) -> str:
    return TEXT[key]


def localize_value(value: object) -> str:
    text_value = str(value)
    mapping = {
        "Unknown": t("unknown"),
        "Calm": t("calm"),
        "Neutral": t("neutral"),
        "Risk-Off": t("risk_off"),
        "Risk-On": "偏多" if LANG == "zh-TW" else "Risk-On",
        "Risk-On Uptrend": "偏多上升趨勢" if LANG == "zh-TW" else "Risk-On Uptrend",
        "Balanced / Selective": "平衡 / 精選" if LANG == "zh-TW" else "Balanced / Selective",
        "Defensive / Risk-Off": "防禦 / 避險" if LANG == "zh-TW" else "Defensive / Risk-Off",
        "Greed": "貪婪" if LANG == "zh-TW" else "Greed",
        "Constructive": "偏正向" if LANG == "zh-TW" else "Constructive",
        "Cautious": "謹慎" if LANG == "zh-TW" else "Cautious",
        "Fear": "恐慌" if LANG == "zh-TW" else "Fear",
        "Watchlist": t("watchlist"),
        "Actionable": t("actionable"),
        "Safer Follow-Through": t("safer"),
        "core": t("core_pool"),
        "explore": t("explore_pool"),
        "clear": t("clear"),
        "DAY_1_EARLY": t("day1"),
        "DAY_2_BUILDING": t("day2"),
        "DAY_3_PLUS_SAFER": t("day3"),
        "Institutional Accumulation": "法人連續布局" if LANG == "zh-TW" else "Institutional Accumulation",
        "Panic Reversal": "恐慌反轉" if LANG == "zh-TW" else "Panic Reversal",
    }
    if text_value in mapping:
        return mapping[text_value]
    if text_value.startswith("macro_event_imminent:") or text_value.startswith("macro_event_near:"):
        prefix, label = text_value.split(":", 1)
        prefix_label = "總經事件臨近" if prefix == "macro_event_imminent" and LANG == "zh-TW" else "Macro imminent"
        if prefix == "macro_event_near":
            prefix_label = "總經事件接近" if LANG == "zh-TW" else "Macro near"
        return f"{prefix_label}: {label.replace('_', ' ')}"
    return text_value


def maybe_translate_text(text_value: str) -> str:
    if LANG != "zh-TW":
        return text_value
    if text_value.startswith("Institutional buying has persisted for ") and text_value.endswith(" sessions."):
        days = text_value.replace("Institutional buying has persisted for ", "").replace(" sessions.", "").strip()
        return f"法人買超已連續 {days} 天。"
    if text_value.startswith("Event risk is elevated:"):
        return text_value.replace("Event risk is elevated:", "事件風險偏高：")
    if text_value.startswith("macro_event_imminent ("):
        return text_value.replace("macro_event_imminent (", "總經事件臨近（").replace(")", "）")
    if text_value.startswith("macro_event_near ("):
        return text_value.replace("macro_event_near (", "總經事件接近（").replace(")", "）")
    if text_value.startswith("Volatility is elevated; position sizing should stay conservative."):
        return "波動率偏高，建議保守控管部位。"
    if text_value.startswith("Breadth is weak, so single-name breakouts may fail more often."):
        return "市場廣度偏弱，個股突破失敗率可能較高。"
    if text_value.endswith(" names are carrying event-risk flags."):
        count = text_value.split(" ", 1)[0]
        return f"{count} 檔標的帶有事件風險旗標。"
    if text_value.startswith("No major market-wide warnings are flashing right now."):
        return "目前沒有市場級重大風險警訊。"
    if text_value.startswith("Theme support:"):
        return text_value.replace("Theme support:", "主題支撐：")
    if text_value.startswith("Institutional flow persistence supports the forward setup."):
        return "法人資金延續支持前瞻設定。"
    if text_value.startswith("Relative strength confirms demand leadership."):
        return "相對強度確認需求領先。"
    if text_value.startswith("Forward demand narrative is strong enough for a starter position."):
        return "前瞻需求敘事偏強，可採試單起步。"
    if " | " in text_value and len(text_value.split(" | ")) == 3:
        dt, region, title = text_value.split(" | ", 2)
        region_map = {"US": "美國", "EU": "歐元區", "JP": "日本", "CN": "中國", "TW": "台灣"}
        title_map = {
            "Annual Report": "年度報告",
            "ECB Cipollone Speech": "歐洲央行 Cipollone 講話",
            "ECB De Guindos Speech": "歐洲央行 De Guindos 講話",
            "ECB Survey of Monetary Analysts": "歐洲央行貨幣分析師調查",
            "ECB Survey of Professional Forecasters": "歐洲央行專業預測調查",
        }
        return f"{dt}｜{region_map.get(region, region)}｜{title_map.get(title, title)}"
    return ZH_DECISION_TEXT.get(text_value, text_value)


def describe_vix(vix_value: float | None) -> tuple[str, str]:
    if vix_value is None:
        return (t("unknown"), "VIX 無法取得，先以市場廣度與情緒分數輔助判讀。" if LANG == "zh-TW" else "VIX unavailable; rely on breadth and sentiment instead.")
    if vix_value < 15:
        return (
            "極低波動 / 偏樂觀" if LANG == "zh-TW" else "Very low vol / optimistic",
            "市場波動很低，資金風險偏好強，但也要留意過熱追價。" if LANG == "zh-TW" else "Volatility is very low and risk appetite is strong, but crowded longs can overheat quickly.",
        )
    if vix_value < 20:
        return (
            "低波動 / 偏正向" if LANG == "zh-TW" else "Low vol / constructive",
            "目前屬於相對健康的風險區，順勢交易通常比較舒服。" if LANG == "zh-TW" else "This is a relatively healthy risk regime where trend-following tends to work better.",
        )
    if vix_value < 25:
        return (
            "中等波動 / 謹慎" if LANG == "zh-TW" else "Moderate vol / cautious",
            "波動開始升高，進場可以更挑、部位可以更小。" if LANG == "zh-TW" else "Volatility is rising, so entries should be more selective and sizing should shrink.",
        )
    if vix_value < 32:
        return (
            "高波動 / 偏避險" if LANG == "zh-TW" else "High vol / defensive",
            "市場進入偏防守狀態，單日震盪大，勝率與持有體驗都會變差。" if LANG == "zh-TW" else "Markets are defensive here, with wider daily swings and weaker holding quality.",
        )
    return (
        "極高波動 / 恐慌" if LANG == "zh-TW" else "Extreme vol / panic",
        "這通常是明顯的恐慌帶，除非是高把握逆勢交易，否則先保守。" if LANG == "zh-TW" else "This is a panic regime; stay conservative unless the reversal setup is exceptionally strong.",
    )


def describe_fear_greed(score: int) -> tuple[str, str, str]:
    if score <= 24:
        return (
            "極度恐慌" if LANG == "zh-TW" else "Extreme Fear",
            "市場參與者明顯在避險，搶反彈要很挑位置。" if LANG == "zh-TW" else "Participants are clearly de-risking; only the best reversal setups deserve attention.",
            "#ff5a6b",
        )
    if score <= 44:
        return (
            "恐慌" if LANG == "zh-TW" else "Fear",
            "情緒偏保守，單日反彈有機會，但延續力通常還不穩。" if LANG == "zh-TW" else "Sentiment is defensive; bounces can happen, but follow-through is still less reliable.",
            "#ff8a4c",
        )
    if score <= 55:
        return (
            "中性" if LANG == "zh-TW" else "Neutral",
            "市場沒有明顯偏多或偏空，適合精選個股，不適合亂追。" if LANG == "zh-TW" else "The tape is balanced; stock selection matters more than aggressive chasing.",
            "#f6c84c",
        )
    if score <= 75:
        return (
            "貪婪" if LANG == "zh-TW" else "Greed",
            "風險偏好不差，順勢策略通常比較吃香，但也要防過熱。" if LANG == "zh-TW" else "Risk appetite is healthy and trend-following tends to work, though overheating risk rises.",
            "#8bd36c",
        )
    return (
        "極度貪婪" if LANG == "zh-TW" else "Extreme Greed",
        "資金願意追價，但這也常是短線過熱區，別把節奏搞丟。" if LANG == "zh-TW" else "Capital is chasing upside aggressively, which can also mean short-term overheating.",
        "#2fbf71",
    )


def build_fear_greed_gauge(score: int) -> go.Figure:
    _, _, accent = describe_fear_greed(score)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 30}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": "rgba(0,0,0,0)"},
                "bar": {"color": accent, "thickness": 0.3},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 24], "color": "#ff6678"},
                    {"range": [25, 44], "color": "#ff9a5a"},
                    {"range": [45, 55], "color": "#f6cf56"},
                    {"range": [56, 75], "color": "#9bd66f"},
                    {"range": [76, 100], "color": "#49c57d"},
                ],
            },
        )
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=10), height=240, paper_bgcolor="white")
    return fig


def build_vix_gauge(vix_value: float | None) -> go.Figure:
    value = 0 if vix_value is None else min(max(float(vix_value), 0), 60)
    accent = "#94a3b8"
    if vix_value is not None:
        if vix_value < 15:
            accent = "#2fbf71"
        elif vix_value < 20:
            accent = "#8bd36c"
        elif vix_value < 25:
            accent = "#f6c84c"
        elif vix_value < 32:
            accent = "#ff8a4c"
        else:
            accent = "#ff5a6b"
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"font": {"size": 30}},
            title={"text": "VIX"},
            gauge={
                "axis": {"range": [0, 60], "tickvals": [0, 15, 20, 25, 32, 60]},
                "bar": {"color": accent, "thickness": 0.3},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 15], "color": "#d9f7e8"},
                    {"range": [15, 20], "color": "#ebf7cf"},
                    {"range": [20, 25], "color": "#fff2c2"},
                    {"range": [25, 32], "color": "#ffe0c2"},
                    {"range": [32, 60], "color": "#ffd0d6"},
                ],
            },
        )
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=10), height=240, paper_bgcolor="white")
    return fig


@st.cache_data(ttl=21600, show_spinner=False)
def get_company_profile_cached(ticker: str) -> dict[str, str]:
    return market_data.get_company_profile(ticker)


def _display_name_for_row(row: pd.Series) -> tuple[str, str]:
    ticker = str(row.get("ticker", "")).upper()
    market_type = str(row.get("type", ""))
    profile = get_company_profile_cached(ticker)
    name_zh = str(profile.get("name_zh", "")).strip()
    name_en = str(profile.get("name_en", "")).strip()
    sector = str(profile.get("sector", "")).strip()

    if market_type == "tw":
        display_name = name_zh or name_en or ticker
        display_sector = sector or "未知"
    else:
        if LANG == "zh-TW" and name_zh:
            display_name = f"{name_en}（{name_zh}）" if name_en else name_zh
        else:
            display_name = name_en or ticker
        display_sector = sector or ("未知" if LANG == "zh-TW" else "Unknown")
    return display_name, display_sector


def enrich_with_company_metadata(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    enriched = frame.copy()
    names: list[str] = []
    sectors: list[str] = []
    for _, row in enriched.iterrows():
        company_name, sector = _display_name_for_row(row)
        names.append(company_name)
        sectors.append(sector)
    enriched["company"] = names
    enriched["sector"] = sectors
    return enriched


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container { max-width: 1450px; padding-top: 2.15rem; padding-bottom: 1.8rem; }
        section[data-testid="stSidebar"] { min-width: 340px !important; max-width: 340px !important; }
        .page-title { font-size: 1.9rem; font-weight: 800; line-height: 1.2; margin: 0 0 1rem 0; color: #243047; }
        .section-label { font-size: 0.78rem; font-weight: 700; color: #616c7c; margin: 0.85rem 0 0.45rem; text-transform: uppercase; }
        .terminal-card, .summary-band, .decision-card { border: 1px solid rgba(118,128,145,.22); border-radius: 8px; background: #ffffff; }
        .terminal-card { padding: 14px; min-height: 174px; }
        .summary-band { padding: 12px 14px; min-height: 112px; background: #f7f9fc; }
        .summary-title { font-size: 0.75rem; font-weight: 700; color: #697483; margin-bottom: 5px; text-transform: uppercase; }
        .summary-main { font-size: 1.08rem; font-weight: 800; margin-bottom: 8px; }
        .summary-sub { font-size: 0.82rem; color: #596474; line-height: 1.45; }
        .state-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin-bottom:12px; }
        .state-metric { border:1px solid rgba(118,128,145,.16); border-radius:8px; padding:10px 12px; background:#f7f9fc; min-height:72px; }
        .state-label { font-size:0.73rem; color:#6b7685; text-transform:uppercase; margin-bottom:4px; font-weight:700; }
        .state-value { font-size:0.98rem; font-weight:800; line-height:1.2; }
        .state-read { border:1px solid rgba(118,128,145,.16); border-radius:8px; padding:12px 14px; background:#f7f9fc; min-height:118px; }
        .state-read-title { font-size:0.73rem; color:#6b7685; text-transform:uppercase; margin-bottom:6px; font-weight:700; }
        .state-read-main { font-size:1rem; font-weight:800; margin-bottom:6px; color:#243047; }
        .state-read-copy { font-size:0.86rem; color:#596474; line-height:1.5; }
        .mini-list { margin: 0; padding-left: 18px; color: #1f2937; font-size: 0.88rem; }
        .decision-card { padding: 14px; margin-bottom: 10px; }
        .decision-head { display:flex; justify-content:space-between; gap:10px; align-items:flex-start; margin-bottom:10px; }
        .decision-ticker { font-size: 0.98rem; font-weight: 800; }
        .decision-meta { font-size: 0.8rem; color: #5f6977; }
        .decision-pill { display:inline-block; border: 1px solid rgba(95,105,119,.18); border-radius:999px; padding: 2px 8px; font-size:0.74rem; margin-right:6px; margin-bottom:6px; }
        .decision-label { font-size: 0.75rem; font-weight: 700; color: #647080; margin: 8px 0 4px; text-transform: uppercase; }
        .decision-list { margin: 0; padding-left: 18px; color: #1f2937; font-size: 0.88rem; }
        div[data-testid="stMetric"] { background:#f7f9fc; border:1px solid rgba(118,128,145,.18); border-radius:8px; padding:10px 12px; }
        div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
        @media (max-width: 1200px) {
            section[data-testid="stSidebar"] { min-width: 290px !important; max-width: 290px !important; }
            .page-title { font-size: 1.55rem; }
            .block-container { padding-top: 2.4rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def run_market_analysis(market_type: str) -> int:
    universe = UniverseBuilder(runtime_settings).build(market_type)
    signals = AnalysisEngine(
        event_risk_service=EventRiskService(high_risk_event_dates=runtime_settings.high_risk_event_dates)
    ).run(universe.to_analysis_universe())
    return len(signals)


def load_candidate_frame(limit: int = 220) -> pd.DataFrame:
    frame = pd.DataFrame(repo.fetch_recent_candidates(limit=limit))
    if frame.empty:
        return frame
    frame = pd.DataFrame(decision_support.enrich_rows(frame.to_dict("records")))
    defaults = {
        "recommendation_bucket": "Watchlist",
        "universe_bucket": "core",
        "market_regime": "Unknown",
        "event_risk_note": "clear",
        "institutional_buy_streak": 0,
        "composite_signal_score": 0.0,
        "relative_strength_score": 0.0,
        "entry_quality_score": 0.0,
    }
    for column, default in defaults.items():
        if column not in frame.columns:
            frame[column] = default
        else:
            frame[column] = frame[column].fillna(default)
    return frame


def render_run_controls() -> None:
    st.markdown(f'<div class="section-label">{t("run_analysis")}</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    if left.button(t("run_tw"), use_container_width=True):
        try:
            count = run_market_analysis("tw")
            st.success(f'{t("analysis_done")} | {t("records")}: {count}')
            st.rerun()
        except Exception as exc:
            st.error(f'{t("analysis_failed")}: {exc}')
    if right.button(t("run_us"), use_container_width=True):
        try:
            count = run_market_analysis("us")
            st.success(f'{t("analysis_done")} | {t("records")}: {count}')
            st.rerun()
        except Exception as exc:
            st.error(f'{t("analysis_failed")}: {exc}')


def render_runtime_settings_panel() -> None:
    with st.sidebar.expander(t("settings_panel")):
        with st.form("runtime_settings_form"):
            app_language = st.selectbox(
                t("language"),
                options=["zh-TW", "en"],
                index=0 if runtime_settings.app_language == "zh-TW" else 1,
            )
            tw_core_tickers = st.text_area("TW Core", value=str(runtime_settings.tw_core_tickers), height=90)
            us_core_tickers = st.text_area("US Core", value=str(runtime_settings.us_core_tickers), height=80)
            tw_explore_tickers = st.text_area("TW Explore", value=str(runtime_settings.tw_explore_tickers), height=70)
            us_explore_tickers = st.text_area("US Explore", value=str(runtime_settings.us_explore_tickers), height=70)
            tw_explore_limit = st.number_input(
                "TW Explore Limit", min_value=1, max_value=30, value=int(runtime_settings.tw_explore_limit), step=1
            )
            us_explore_limit = st.number_input(
                "US Explore Limit", min_value=1, max_value=30, value=int(runtime_settings.us_explore_limit), step=1
            )
            st.caption("FMP economic calendar is used first. This field is only for manual fallback or custom override dates.")
            high_risk_event_dates = st.text_input(t("high_risk_dates"), value=str(runtime_settings.high_risk_event_dates))
            submitted = st.form_submit_button(t("save_settings"), use_container_width=True)
        if submitted:
            user_settings_service.update_runtime_preferences(
                chat_id,
                {
                    "app_language": app_language,
                    "tw_core_tickers": tw_core_tickers,
                    "us_core_tickers": us_core_tickers,
                    "tw_explore_tickers": tw_explore_tickers,
                    "us_explore_tickers": us_explore_tickers,
                    "tw_explore_limit": int(tw_explore_limit),
                    "us_explore_limit": int(us_explore_limit),
                    "high_risk_event_dates": high_risk_event_dates,
                },
            )
            st.success(t("settings_saved"))
            st.rerun()


def render_market_state() -> None:
    overview = overview_service.build()
    vix_value = market_data.get_vix_value()
    vix_zone, vix_copy = describe_vix(vix_value)
    fear_greed_label, fear_greed_copy, _ = describe_fear_greed(overview.fear_greed_score)
    st.markdown(f'<div class="section-label">{t("market_state")}</div>', unsafe_allow_html=True)
    momentum_items = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in overview.momentum_zones) or f"<li>{t('no_data')}</li>"
    macro_items = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in overview.upcoming_macro_events) or f"<li>{t('no_data')}</li>"
    caution_items = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in overview.caution_items)
    gauge_left, gauge_right = st.columns(2)
    with gauge_left:
        st.markdown(f'<div class="section-label">{t("fear_greed_gauge")}</div>', unsafe_allow_html=True)
        st.plotly_chart(build_fear_greed_gauge(overview.fear_greed_score), use_container_width=True, config={"displayModeBar": False})
    with gauge_right:
        st.markdown(f'<div class="section-label">{t("vix_meaning")}</div>', unsafe_allow_html=True)
        st.plotly_chart(build_vix_gauge(vix_value), use_container_width=True, config={"displayModeBar": False})
    read_left, read_right = st.columns(2)
    with read_left:
        st.markdown(
            f"""
            <div class="state-read">
                <div class="state-read-title">{t("vix_zone")}</div>
                <div class="state-read-main">{vix_zone}</div>
                <div class="state-read-copy">{vix_copy}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with read_right:
        st.markdown(
            f"""
            <div class="state-read">
                <div class="state-read-title">{t("market_read")}</div>
                <div class="state-read-main">{fear_greed_label} / {localize_value(overview.sentiment_label)}</div>
                <div class="state-read-copy">{fear_greed_copy}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        f"""
        <div class="terminal-card">
            <div class="state-grid">
                <div class="state-metric">
                    <div class="state-label">{t("overall_trend")}</div>
                    <div class="state-value">{localize_value(overview.overall_trend)}</div>
                </div>
                <div class="state-metric">
                    <div class="state-label">{t("sentiment")}</div>
                    <div class="state-value">{localize_value(overview.sentiment_label)}</div>
                </div>
                <div class="state-metric">
                    <div class="state-label">{t("fear_greed")}</div>
                    <div class="state-value">{overview.fear_greed_score}/100</div>
                </div>
                <div class="state-metric">
                    <div class="state-label">{t("breadth")}</div>
                    <div class="state-value">{overview.breadth_snapshot:.2f}</div>
                </div>
            </div>
            <div class="decision-label">{t("momentum_zones")}</div>
            <ul class="mini-list">{momentum_items}</ul>
            <div class="decision-label">{t("macro_calendar")}</div>
            <ul class="mini-list">{macro_items}</ul>
            <div class="decision-label">{t("cautions")}</div>
            <ul class="mini-list">{caution_items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_band(label: str, summary: Any) -> None:
    if summary is None:
        st.info(t("no_data"))
        return
    st.markdown(
        f"""
        <div class="summary-band">
            <div class="summary-title">{label}</div>
            <div class="summary-main">{localize_value(summary.regime)}</div>
            <div class="summary-sub">
                {t("breadth")} {summary.average_breadth:.2f} |
                {t("candidates")} {summary.candidate_count} |
                {t("actionable")} {summary.actionable_count} |
                {t("safer")} {summary.safer_count}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_market_overview() -> None:
    st.markdown(f'<div class="section-label">{t("market_overview")}</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        render_summary_band(t("taiwan"), summary_service.build_market_summary("tw"))
    with right:
        render_summary_band(t("us"), summary_service.build_market_summary("us"))


def render_terminal_table(frame: pd.DataFrame, columns: list[str]) -> None:
    if frame.empty:
        st.info(t("no_data"))
        return
    display = enrich_with_company_metadata(frame)
    for column in ["universe_bucket", "recommendation_bucket", "event_risk_note"]:
        if column in display.columns:
            display[column] = display[column].map(localize_value)
    if "suggested_action" in display.columns:
        display["suggested_action"] = display["suggested_action"].astype(str).map(maybe_translate_text)
    selected = [column for column in columns if column in display.columns]
    table = display[selected].copy()
    rename_map = {
        "ticker": t("ticker"),
        "company": t("company"),
        "sector": t("sector"),
        "recommendation_bucket": t("bucket"),
        "composite_signal_score": t("score"),
        "institutional_buy_streak": "法人連買天數" if LANG == "zh-TW" else "Institutional Buy Streak",
        "risk_level": t("risk_label"),
        "event_risk_note": t("event_risk"),
        "next_event_date": t("next_event"),
        "suggested_action": t("suggested_action"),
    }
    table = table.rename(columns=rename_map)
    st.dataframe(table, use_container_width=True, hide_index=True)


def render_focus_lists(candidate_frame: pd.DataFrame) -> None:
    st.markdown(f'<div class="section-label">{t("focus_lists")}</div>', unsafe_allow_html=True)
    if candidate_frame.empty:
        st.info(t("no_data"))
        return
    latest_date = candidate_frame["date"].max()
    latest = candidate_frame[candidate_frame["date"] == latest_date].copy()
    core_tab, explore_tab, risk_tab = st.tabs([t("core_tab"), t("explore_tab"), t("risk_tab")])
    with core_tab:
        render_terminal_table(
            latest[latest["universe_bucket"] == "core"]
            .sort_values(by=["composite_signal_score", "institutional_buy_streak"], ascending=[False, False])
            .head(12),
            ["ticker", "company", "sector", "recommendation_bucket", "composite_signal_score", "institutional_buy_streak", "suggested_action"],
        )
    with explore_tab:
        render_terminal_table(
            latest[latest["universe_bucket"] == "explore"]
            .sort_values(by=["composite_signal_score"], ascending=[False])
            .head(12),
            ["ticker", "company", "sector", "recommendation_bucket", "composite_signal_score", "risk_level", "suggested_action"],
        )
    with risk_tab:
        render_terminal_table(
            latest[latest["event_risk_note"] != "clear"]
            .sort_values(by=["composite_signal_score"], ascending=[True])
            .head(12),
            ["ticker", "company", "sector", "recommendation_bucket", "event_risk_note", "next_event_date", "risk_level"],
        )


def render_decision_cards(candidate_frame: pd.DataFrame) -> None:
    st.markdown(f'<div class="section-label">{t("decision_cards")}</div>', unsafe_allow_html=True)
    if candidate_frame.empty:
        st.info(t("no_data"))
        return
    latest_date = candidate_frame["date"].max()
    latest = (
        candidate_frame[candidate_frame["date"] == latest_date]
        .sort_values(by=["composite_signal_score", "institutional_buy_streak"], ascending=[False, False])
        .head(8)
    )
    for _, row in latest.iterrows():
        company_name, sector_name = _display_name_for_row(row)
        rationale = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in row.get("rationale", []))
        risks = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in row.get("risks", []))
        suggestion = maybe_translate_text(str(row.get("suggested_action", "")))
        level = maybe_translate_text(str(row.get("recommendation_level", "")))
        win_label = maybe_translate_text(str(row.get("win_rate_label", "")))
        risk_label = maybe_translate_text(str(row.get("risk_level", "")))
        reward_risk = maybe_translate_text(str(row.get("reward_risk_label", "")))
        forward_score = float(row.get("forward_score", 0))
        forward_notes = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in row.get("forward_notes", []))
        st.markdown(
            f"""
            <div class="decision-card">
                <div class="decision-head">
                    <div>
                        <div class="decision-ticker">{row["ticker"]}</div>
                        <div class="decision-meta">
                            {company_name} | {t("sector")} {sector_name} <br/>
                            {t("signal_type")} {localize_value(row.get("signal_type", ""))} |
                            {localize_value(row.get("universe_bucket", "core"))} |
                            {localize_value(row.get("recommendation_bucket", "Watchlist"))}
                        </div>
                    </div>
                    <div class="decision-meta">{t("score")} {float(row.get("composite_signal_score", 0)):.2f}</div>
                </div>
                <span class="decision-pill">{level}</span>
                <span class="decision-pill">{t("win_label")}: {win_label}</span>
                <span class="decision-pill">{t("risk_label")}: {risk_label}</span>
                <span class="decision-pill">{t("reward_risk")}: {reward_risk}</span>
                <span class="decision-pill">{t("forward_score")}: {forward_score:.2f}</span>
                <span class="decision-pill">{t("event_risk")}: {localize_value(row.get("event_risk_note", "clear"))}</span>
                <div class="decision-label">{t("suggested_action")}</div>
                <div>{suggestion}</div>
                <div class="decision-label">{t("forward_notes")}</div>
                <ul class="decision-list">{forward_notes}</ul>
                <div class="decision-label">{t("rationale")}</div>
                <ul class="decision-list">{rationale}</ul>
                <div class="decision-label">{t("risks")}</div>
                <ul class="decision-list">{risks}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_dashboard(candidate_frame: pd.DataFrame) -> None:
    snapshot = dashboard_service.build_snapshot()
    overview = overview_service.build()
    st.title(t("app_title"))
    st.caption(t("app_caption"))
    m1, m2, m3, m4 = st.columns(4)
    vix_zone, _ = describe_vix(snapshot.vix)
    m1.metric(t("vix"), f"{snapshot.vix:.2f}" if snapshot.vix is not None else "N/A", delta=vix_zone if snapshot.vix is not None else None)
    m2.metric(t("sentiment"), localize_value(snapshot.market_sentiment), delta=describe_fear_greed(overview.fear_greed_score)[0])
    m3.metric(t("open_pnl"), f"{snapshot.total_open_pnl:.2f}%")
    m4.metric(t("win_rate"), f"{snapshot.win_rate:.2f}%")
    render_run_controls()
    render_market_state()
    render_market_overview()
    render_focus_lists(candidate_frame)
    render_decision_cards(candidate_frame)
    left, right = st.columns((1.55, 1))
    with left:
        st.markdown(f'<div class="section-label">{t("portfolio_curve")}</div>', unsafe_allow_html=True)
        if snapshot.equity_curve.empty:
            st.info(t("no_closed_trades"))
        else:
            st.plotly_chart(
                px.line(snapshot.equity_curve, x="sequence", y="equity_pnl", markers=True, title=t("portfolio_curve")),
                use_container_width=True,
            )
    with right:
        st.markdown(f'<div class="section-label">{t("open_positions")}</div>', unsafe_allow_html=True)
        if snapshot.open_positions.empty:
            st.info(t("no_positions"))
        else:
            st.dataframe(snapshot.open_positions, use_container_width=True, hide_index=True)


def render_portfolio() -> None:
    st.markdown(f'<div class="page-title">{t("portfolio")}</div>', unsafe_allow_html=True)
    positions, _ = portfolio_service.get_open_positions_summary()
    if not positions:
        st.info(t("no_positions"))
        return
    frame = pd.DataFrame(positions)
    st.dataframe(frame, use_container_width=True, hide_index=True)
    st.plotly_chart(px.bar(frame, x="ticker", y="stop_buffer_percent", title=t("stop_buffer")), use_container_width=True)


def render_screener(candidate_frame: pd.DataFrame) -> None:
    st.markdown(f'<div class="page-title">{t("screener")}</div>', unsafe_allow_html=True)
    if candidate_frame.empty:
        st.info(t("no_data"))
        return
    latest_date = candidate_frame["date"].max()
    latest = candidate_frame[candidate_frame["date"] == latest_date].copy()
    latest = enrich_with_company_metadata(latest)
    c1, c2, c3 = st.columns(3)
    selected_market = c1.selectbox(t("market"), [t("all"), "tw", "us"])
    selected_bucket = c2.selectbox(t("bucket"), [t("all"), "Safer Follow-Through", "Actionable", "Watchlist"])
    min_score = c3.slider(t("min_score"), min_value=0, max_value=100, value=60)
    filtered = latest.copy()
    if selected_market != t("all"):
        filtered = filtered[filtered["type"] == selected_market]
    if selected_bucket != t("all"):
        filtered = filtered[filtered["recommendation_bucket"] == selected_bucket]
    filtered = filtered[filtered["composite_signal_score"] >= min_score]

    left, right = st.columns((1.15, 1))
    with left:
        display = filtered.copy()
        for column in ["universe_bucket", "recommendation_bucket", "entry_timing", "market_regime", "event_risk_note"]:
            if column in display.columns:
                display[column] = display[column].map(localize_value)
        st.dataframe(
            display[
                [
                    column
                    for column in [
                        "ticker",
                        "company",
                        "sector",
                        "type",
                        "universe_bucket",
                        "signal_type",
                        "recommendation_bucket",
                        "composite_signal_score",
                        "recommendation_level",
                        "win_rate_label",
                        "risk_level",
                    ]
                    if column in display.columns
                ]
            ].rename(
                columns={
                    "ticker": t("ticker"),
                    "company": t("company"),
                    "sector": t("sector"),
                    "type": t("market"),
                    "universe_bucket": t("universe"),
                    "signal_type": t("signal_type"),
                    "recommendation_bucket": t("bucket"),
                    "composite_signal_score": t("score"),
                    "recommendation_level": "建議等級" if LANG == "zh-TW" else "Recommendation Level",
                    "win_rate_label": t("win_label"),
                    "risk_level": t("risk_label"),
                    "forward_score": t("forward_score"),
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    with right:
        ticker = st.text_input(t("ticker"), value="2330.TW")
        history = pd.DataFrame(repo.fetch_history(ticker))
        if history.empty:
            st.info(t("no_data"))
            return
        history = pd.DataFrame(decision_support.enrich_rows(history.to_dict("records")))
        latest_row = history.iloc[-1]
        top1, top2 = st.columns(2)
        top1.metric(t("score"), f"{float(latest_row.get('composite_signal_score', 0)):.2f}")
        top2.metric(t("bucket"), localize_value(latest_row.get("recommendation_bucket", "Watchlist")))
        detail_tab, why_tab = st.tabs([t("detail_tab"), t("why_tab")])
        with detail_tab:
            st.plotly_chart(px.line(history, x="date", y="close_price", markers=True, title=t("price_trend")), use_container_width=True)
            st.plotly_chart(
                px.line(
                    history,
                    x="date",
                    y=[
                        "market_regime_score",
                        "breadth_score",
                        "relative_strength_score",
                        "institutional_conviction_score",
                        "entry_quality_score",
                        "composite_signal_score",
                    ],
                    markers=True,
                    title=t("funnel_scores"),
                ),
                use_container_width=True,
            )
        with why_tab:
            st.markdown(f"**{t('suggested_action')}**  \n{maybe_translate_text(str(latest_row.get('suggested_action', '')))}")
            st.markdown(f"**{t('rationale')}**")
            for item in latest_row.get("rationale", []):
                st.write(f"- {maybe_translate_text(item)}")
            st.markdown(f"**{t('risks')}**")
            for item in latest_row.get("risks", []):
                st.write(f"- {maybe_translate_text(item)}")


def render_health_check() -> None:
    st.markdown(f'<div class="page-title">{t("health")}</div>', unsafe_allow_html=True)
    if st.button("Run Source Diagnostics", use_container_width=True):
        with st.spinner("Checking market-data sources..."):
            rows = market_data.diagnose_providers()
        frame = pd.DataFrame(rows)
        if LANG == "zh-TW":
            frame = frame.rename(columns={"source": "來源", "status": "狀態", "latency_ms": "延遲(ms)", "note": "說明"})
            frame["狀態"] = frame["狀態"].map(lambda s: "正常" if s == "ok" else "失敗")
        st.dataframe(frame, use_container_width=True, hide_index=True)


inject_styles()

language_options = {"繁體中文": "zh-TW", "English": "en"}
selected_label = st.sidebar.selectbox(
    f'Language / {COPY["zh-TW"]["language"]}',
    options=list(language_options.keys()),
    index=0 if LANG == "zh-TW" else 1,
)
TEXT = COPY["zh-TW"] | COPY[language_options[selected_label]]
render_runtime_settings_panel()

candidate_frame = load_candidate_frame()
nav = st.sidebar.radio(t("view"), [t("dashboard"), t("portfolio"), t("screener"), t("health")], index=0)

if nav == t("dashboard"):
    render_dashboard(candidate_frame)
elif nav == t("portfolio"):
    render_portfolio()
elif nav == t("health"):
    render_health_check()
else:
    render_screener(candidate_frame)
