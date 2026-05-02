from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
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
from investbot.services.market_overview_service import MarketOverviewService
from investbot.services.portfolio_service import PortfolioService
from investbot.services.summary_service import SummaryService
from investbot.services.universe_builder import UniverseBuilder
from investbot.services.user_settings_service import UserSettingsService
from investbot.services.event_risk_service import EventRiskService


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
        "app_caption": "先看總體市場，再看資金流與動能，最後才下鑽到個股。",
        "language": "語言",
        "view": "檢視",
        "dashboard": "總覽",
        "portfolio": "持股",
        "screener": "篩選",
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
        "breadth": "市場廣度",
        "momentum_zones": "重點動能區域",
        "cautions": "整體提醒",
        "macro_calendar": "重大事件行事曆",
        "market_overview": "市場總覽",
        "taiwan": "台股",
        "us": "美股",
        "candidates": "候選數",
        "actionable": "可行動",
        "safer": "相對安全延續",
        "focus_lists": "重點名單",
        "decision_cards": "決策卡",
        "core_pool": "Core 主池",
        "explore_pool": "Explore 觀察池",
        "watchlist": "觀察",
        "no_data": "目前還沒有資料，先跑一次分析。",
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
        "price_trend": "價格趨勢",
        "funnel_scores": "漏斗分數",
        "suggested_action": "建議動作",
        "rationale": "推薦理由",
        "risks": "主要風險",
        "win_label": "勝率評估",
        "risk_label": "風險等級",
        "reward_risk": "風報比",
        "event_risk": "事件風險",
        "next_event": "下一個事件",
        "universe": "池別",
        "score": "分數",
        "signal_type": "訊號",
        "unknown": "未知",
        "calm": "平穩",
        "neutral": "中性",
        "risk_off": "避險",
        "clear": "正常",
        "day1": "第 1 天提前卡位",
        "day2": "第 2 天持續建倉",
        "day3": "第 3 天以上較穩",
        "core_tab": "Core",
        "explore_tab": "Explore",
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
        "app_caption": "Start with the market, then capital flow and momentum, then single names.",
        "language": "Language",
        "view": "View",
        "dashboard": "Dashboard",
        "portfolio": "Portfolio",
        "screener": "Screener",
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
        "price_trend": "Price Trend",
        "funnel_scores": "Funnel Scores",
        "suggested_action": "Suggested Action",
        "rationale": "Why It Ranks",
        "risks": "Main Risks",
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
    "Institutional buying has persisted for 5 sessions.": "法人買超已連續 5 天以上。",
    "Institutional buying is building into a second session.": "法人買超延續到第 2 天，正在建立倉位。",
    "Institutional buying has just turned positive.": "法人買超剛轉正，屬於早期訊號。",
    "Relative strength is decisively above the market benchmark.": "相對強弱明顯高於市場基準。",
    "Relative strength is supportive versus the benchmark.": "相對強弱優於基準，屬於正向加分。",
    "Price location is constructive and not excessively extended.": "價格位置健康，尚未明顯乖離。",
    "Entry quality is acceptable if execution stays disciplined.": "進場位置尚可，但需要守紀律執行。",
    "The market regime is supportive for trend-following entries.": "目前市場環境有利於順勢交易。",
    "The broader market is neutral, so follow-through may be slower.": "整體市場偏中性，後續續強速度可能較慢。",
    "The broader market is risk-off, so hit rates can fall quickly.": "整體市場偏避險，成功率可能快速下降。",
    "This idea is in the Explore pool, so it should not outrank core large-cap names.": "這檔屬於 Explore 觀察池，不應高於核心大型股的優先級。",
    "This name belongs to the core monitoring pool.": "這檔屬於 Core 主池。",
    "Event risk is manageable but still worth monitoring.": "事件風險可控，但仍值得留意。",
    "No major risk flags are active right now, but standard stop discipline still applies.": "目前沒有明顯風險警示，但停損紀律仍要維持。",
    "Normal position sizing or staged entries on minor pullbacks.": "可以正常部位，或等小幅拉回分批進場。",
    "Pilot size first, then add if confirmation holds.": "先小部位試單，確認延續後再加碼。",
    "Observe only until the odds improve.": "先觀察，等勝率條件更完整。",
    "Small trial size only; keep core capital focused on large caps.": "僅適合小倉位試單，主資金仍以大型股為主。",
    "High Conviction Core": "高信心核心標的",
    "Actionable Setup": "可執行型態",
    "Watch and Wait": "觀察等待",
    "High": "高",
    "Medium-High": "中高",
    "Medium-Low": "中低",
    "Medium": "中",
    "Favorable": "偏有利",
    "Balanced": "均衡",
    "Unclear": "不明朗",
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
        "Watchlist": t("watchlist"),
        "Actionable": t("actionable"),
        "Safer Follow-Through": t("safer"),
        "core": t("core_pool"),
        "explore": t("explore_pool"),
        "clear": t("clear"),
        "DAY_1_EARLY": t("day1"),
        "DAY_2_BUILDING": t("day2"),
        "DAY_3_PLUS_SAFER": t("day3"),
    }
    if text_value in mapping:
        return mapping[text_value]
    if text_value.startswith("macro_event_imminent:") or text_value.startswith("macro_event_near:"):
        prefix, label = text_value.split(":", 1)
        prefix_label = mapping.get(prefix.replace(":",""), prefix)
        if prefix == "macro_event_imminent":
            prefix_label = "Macro imminent"
        elif prefix == "macro_event_near":
            prefix_label = "Macro near"
        if LANG == "zh-TW":
            prefix_label = "總經事件臨近" if prefix == "macro_event_imminent" else "總經事件接近"
        return f"{prefix_label}: {label.replace('_', ' ')}"
    return text_value


def maybe_translate_text(text_value: str) -> str:
    if LANG != "zh-TW":
        return text_value
    return ZH_DECISION_TEXT.get(text_value, text_value)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container { max-width: 1450px; padding-top: 0.9rem; padding-bottom: 1.8rem; }
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
            app_language = st.selectbox(t("language"), options=["zh-TW", "en"], index=0 if runtime_settings.app_language == "zh-TW" else 1)
            tw_core_tickers = st.text_area("TW Core", value=str(runtime_settings.tw_core_tickers), height=90)
            us_core_tickers = st.text_area("US Core", value=str(runtime_settings.us_core_tickers), height=80)
            tw_explore_tickers = st.text_area("TW Explore", value=str(runtime_settings.tw_explore_tickers), height=70)
            us_explore_tickers = st.text_area("US Explore", value=str(runtime_settings.us_explore_tickers), height=70)
            tw_explore_limit = st.number_input("TW Explore Limit", min_value=1, max_value=30, value=int(runtime_settings.tw_explore_limit), step=1)
            us_explore_limit = st.number_input("US Explore Limit", min_value=1, max_value=30, value=int(runtime_settings.us_explore_limit), step=1)
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
    st.markdown(f'<div class="section-label">{t("market_state")}</div>', unsafe_allow_html=True)
    momentum_items = "".join(f"<li>{item}</li>" for item in overview.momentum_zones) or f"<li>{t('no_data')}</li>"
    caution_items = "".join(f"<li>{item}</li>" for item in overview.caution_items)
    st.markdown(
        f"""
        <div class="terminal-card">
            <div class="state-grid">
                <div class="state-metric">
                    <div class="state-label">{t("overall_trend")}</div>
                    <div class="state-value">{overview.overall_trend}</div>
                </div>
                <div class="state-metric">
                    <div class="state-label">{t("sentiment")}</div>
                    <div class="state-value">{overview.sentiment_label}</div>
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
            <ul class="mini-list">{"".join(f"<li>{item}</li>" for item in overview.upcoming_macro_events) or f"<li>{t('no_data')}</li>"}</ul>
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
    display = frame.copy()
    for column in ["universe_bucket", "recommendation_bucket", "event_risk_note"]:
        if column in display.columns:
            display[column] = display[column].map(localize_value)
    st.dataframe(display[[column for column in columns if column in display.columns]], use_container_width=True, hide_index=True)


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
            ["ticker", "recommendation_bucket", "composite_signal_score", "institutional_buy_streak", "suggested_action"],
        )
    with explore_tab:
        render_terminal_table(
            latest[latest["universe_bucket"] == "explore"]
            .sort_values(by=["composite_signal_score"], ascending=[False])
            .head(12),
            ["ticker", "recommendation_bucket", "composite_signal_score", "risk_level", "suggested_action"],
        )
    with risk_tab:
        render_terminal_table(
            latest[latest["event_risk_note"] != "clear"]
            .sort_values(by=["composite_signal_score"], ascending=[True])
            .head(12),
            ["ticker", "recommendation_bucket", "event_risk_note", "next_event_date", "risk_level"],
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
        rationale = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in row.get("rationale", []))
        risks = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in row.get("risks", []))
        suggestion = maybe_translate_text(str(row.get("suggested_action", "")))
        level = maybe_translate_text(str(row.get("recommendation_level", "")))
        win_label = maybe_translate_text(str(row.get("win_rate_label", "")))
        risk_label = maybe_translate_text(str(row.get("risk_level", "")))
        reward_risk = maybe_translate_text(str(row.get("reward_risk_label", "")))
        st.markdown(
            f"""
            <div class="decision-card">
                <div class="decision-head">
                    <div>
                        <div class="decision-ticker">{row["ticker"]}</div>
                        <div class="decision-meta">
                            {t("signal_type")} {row.get("signal_type", "")} |
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
                <span class="decision-pill">{t("event_risk")}: {localize_value(row.get("event_risk_note", "clear"))}</span>
                <div class="decision-label">{t("suggested_action")}</div>
                <div>{suggestion}</div>
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
    st.title(t("app_title"))
    st.caption(t("app_caption"))
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(t("vix"), f"{snapshot.vix:.2f}" if snapshot.vix is not None else "N/A")
    m2.metric(t("sentiment"), localize_value(snapshot.market_sentiment))
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
    st.subheader(t("portfolio"))
    positions, _ = portfolio_service.get_open_positions_summary()
    if not positions:
        st.info(t("no_positions"))
        return
    frame = pd.DataFrame(positions)
    st.dataframe(frame, use_container_width=True, hide_index=True)
    st.plotly_chart(px.bar(frame, x="ticker", y="stop_buffer_percent", title=t("stop_buffer")), use_container_width=True)


def render_screener(candidate_frame: pd.DataFrame) -> None:
    st.subheader(t("screener"))
    if candidate_frame.empty:
        st.info(t("no_data"))
        return
    latest_date = candidate_frame["date"].max()
    latest = candidate_frame[candidate_frame["date"] == latest_date].copy()
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
            ],
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
                    y=["market_regime_score", "breadth_score", "relative_strength_score", "institutional_conviction_score", "entry_quality_score", "composite_signal_score"],
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


inject_styles()

language_options = {"蝜?銝剜?": "zh-TW", "English": "en"}
selected_label = st.sidebar.selectbox(
    f'Language / {COPY["zh-TW"]["language"]}',
    options=list(language_options.keys()),
    index=0 if LANG == "zh-TW" else 1,
)
TEXT = COPY["zh-TW"] | COPY[language_options[selected_label]]
render_runtime_settings_panel()

candidate_frame = load_candidate_frame()
nav = st.sidebar.radio(t("view"), [t("dashboard"), t("portfolio"), t("screener")], index=0)

if nav == t("dashboard"):
    render_dashboard(candidate_frame)
elif nav == t("portfolio"):
    render_portfolio()
else:
    render_screener(candidate_frame)
