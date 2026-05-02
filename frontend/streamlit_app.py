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
from investbot.db.repositories import DailyAnalysisRepository
from investbot.services.analysis_engine import AnalysisEngine
from investbot.services.dashboard_service import DashboardService
from investbot.services.decision_support import DecisionSupportService
from investbot.services.market_overview_service import MarketOverviewService
from investbot.services.portfolio_service import PortfolioService
from investbot.services.summary_service import SummaryService
from investbot.services.universe_builder import UniverseBuilder
from investbot.data_sources.market_data import YahooMarketDataClient


st.set_page_config(page_title="Smart Swing Agent", layout="wide", initial_sidebar_state="expanded")

settings = get_settings()
repo = DailyAnalysisRepository()
portfolio_service = PortfolioService()
market_data = YahooMarketDataClient()
dashboard_service = DashboardService(portfolio_service=portfolio_service, market_data=market_data)
decision_support = DecisionSupportService()
summary_service = SummaryService(repository=repo, decision_support=decision_support)
overview_service = MarketOverviewService(repository=repo, summary_service=summary_service, market_data=market_data)


COPY = {
    "zh-TW": {
        "title": "Smart Swing Agent",
        "caption": "先看市場總體，再看資金與動能，最後才進個股。",
        "language": "語言",
        "dashboard": "總覽",
        "portfolio": "投資組合",
        "screener": "選股",
        "run_analysis": "執行分析",
        "run_tw": "執行台股分析",
        "run_us": "執行美股分析",
        "analysis_done": "分析完成",
        "analysis_failed": "分析失敗",
        "records": "寫入筆數",
        "market_state": "市場整體概況",
        "overall_trend": "整體趨勢",
        "sentiment": "市場情緒",
        "fear_greed": "恐慌貪婪",
        "breadth": "市場廣度",
        "momentum_zones": "重點動能區域",
        "cautions": "整體提醒",
        "market_overview": "市場總覽",
        "taiwan": "台股",
        "us": "美股",
        "candidates": "候選",
        "actionable": "可行動",
        "safer": "相對安全延續",
        "focus_lists": "重點名單",
        "decision_cards": "決策卡",
        "core_pool": "Core 固定池",
        "explore_pool": "Explore 觀察池",
        "watchlist": "觀察名單",
        "no_data": "尚無資料，請先跑一次分析。",
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
        "ticker": "代碼",
        "view": "檢視",
        "price_trend": "價格走勢",
        "funnel_scores": "漏斗分數",
        "suggested_action": "適合動作",
        "rationale": "推薦理由",
        "risks": "主要風險",
        "win_label": "勝率評估",
        "risk_label": "風險等級",
        "reward_risk": "風報比",
        "event_risk": "事件風險",
        "next_event": "下一事件",
        "universe": "池別",
        "unknown": "未知",
        "calm": "平穩",
        "neutral": "中性",
        "risk_off": "風險偏高",
        "clear": "正常",
        "day1": "第 1 天偏早",
        "day2": "第 2 天建立中",
        "day3": "第 3 天以上較穩",
    },
    "en": {
        "title": "Smart Swing Agent",
        "caption": "Start with the market, then capital flow and momentum, then single names.",
        "language": "Language",
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
        "view": "View",
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
        "unknown": "Unknown",
        "calm": "Calm",
        "neutral": "Neutral",
        "risk_off": "Risk-Off",
        "clear": "Clear",
        "day1": "Day 1 Early",
        "day2": "Day 2 Building",
        "day3": "Day 3+ Safer",
    },
}


def current_language() -> str:
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
    return mapping.get(str(value), str(value))


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container { max-width: 1380px; padding-top: 1.1rem; padding-bottom: 2rem; }
        .section-label { font-size: 0.82rem; font-weight: 700; color: #5d6776; margin: 0.9rem 0 0.45rem; text-transform: uppercase; }
        .state-card, .summary-band, .decision-card { border: 1px solid rgba(118,128,145,.22); border-radius: 8px; background: #ffffff; }
        .state-card { padding: 16px; min-height: 160px; }
        .summary-band { padding: 14px 16px; min-height: 116px; background: #f7f9fc; }
        .summary-title { font-size: 0.78rem; font-weight: 700; color: #677282; margin-bottom: 6px; text-transform: uppercase; }
        .summary-main { font-size: 1.15rem; font-weight: 800; margin-bottom: 8px; }
        .summary-sub { font-size: 0.84rem; color: #5c6776; line-height: 1.45; }
        .state-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; margin-bottom:12px; }
        .state-metric { border:1px solid rgba(118,128,145,.18); border-radius:8px; padding:12px; background:#f7f9fc; }
        .state-label { font-size:0.76rem; color:#677282; text-transform:uppercase; margin-bottom:4px; font-weight:700; }
        .state-value { font-size:1rem; font-weight:800; }
        .decision-card { padding: 16px; margin-bottom: 12px; }
        .decision-head { display:flex; justify-content:space-between; gap:10px; align-items:flex-start; margin-bottom:10px; }
        .decision-ticker { font-size: 1.02rem; font-weight: 800; }
        .decision-meta { font-size: 0.82rem; color: #5f6977; }
        .decision-pill { display:inline-block; border: 1px solid rgba(95,105,119,.22); border-radius:999px; padding: 3px 8px; font-size:0.76rem; margin-right:6px; margin-bottom:6px; }
        .decision-label { font-size: 0.78rem; font-weight: 700; color: #647080; margin: 8px 0 4px; text-transform: uppercase; }
        .decision-list { margin: 0; padding-left: 18px; color: #1f2937; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def run_market_analysis(market_type: str) -> int:
    universe = UniverseBuilder(settings).build(market_type)
    signals = AnalysisEngine().run(universe.to_analysis_universe())
    return len(signals)


def load_candidate_frame(limit: int = 180) -> pd.DataFrame:
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


def render_market_state() -> None:
    overview = overview_service.build()
    st.markdown(f'<div class="section-label">{t("market_state")}</div>', unsafe_allow_html=True)
    momentum_text = "<br>".join(overview.momentum_zones) if overview.momentum_zones else t("no_data")
    caution_text = "<br>".join(overview.caution_items)
    st.markdown(
        f"""
        <div class="state-card">
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
            <div class="summary-sub">{momentum_text}</div>
            <div class="decision-label">{t("cautions")}</div>
            <div class="summary-sub">{caution_text}</div>
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


def render_simple_table(frame: pd.DataFrame, columns: list[str]) -> None:
    if frame.empty:
        st.info(t("no_data"))
        return
    localized = frame.copy()
    for column in ["universe_bucket", "recommendation_bucket"]:
        if column in localized.columns:
            localized[column] = localized[column].map(localize_value)
    st.dataframe(localized[[column for column in columns if column in localized.columns]], use_container_width=True, hide_index=True)


def render_focus_lists(candidate_frame: pd.DataFrame) -> None:
    st.markdown(f'<div class="section-label">{t("focus_lists")}</div>', unsafe_allow_html=True)
    if candidate_frame.empty:
        st.info(t("no_data"))
        return
    latest_date = candidate_frame["date"].max()
    latest = candidate_frame[candidate_frame["date"] == latest_date].copy()
    columns = ["ticker", "universe_bucket", "recommendation_bucket", "composite_signal_score", "suggested_action"]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(t("safer"))
        render_simple_table(latest[latest["recommendation_bucket"] == "Safer Follow-Through"].head(6), columns)
    with col2:
        st.caption(t("actionable"))
        render_simple_table(latest[latest["recommendation_bucket"] == "Actionable"].head(6), columns)
    with col3:
        st.caption(t("explore_pool"))
        render_simple_table(latest[latest["universe_bucket"] == "explore"].head(6), columns)


def render_decision_cards(candidate_frame: pd.DataFrame) -> None:
    st.markdown(f'<div class="section-label">{t("decision_cards")}</div>', unsafe_allow_html=True)
    if candidate_frame.empty:
        st.info(t("no_data"))
        return
    latest_date = candidate_frame["date"].max()
    latest = candidate_frame[candidate_frame["date"] == latest_date].copy()
    latest = latest.sort_values(by=["composite_signal_score", "institutional_buy_streak"], ascending=[False, False]).head(8)
    for _, row in latest.iterrows():
        rationale = "".join(f"<li>{item}</li>" for item in row.get("rationale", []))
        risks = "".join(f"<li>{item}</li>" for item in row.get("risks", []))
        st.markdown(
            f"""
            <div class="decision-card">
                <div class="decision-head">
                    <div>
                        <div class="decision-ticker">{row["ticker"]}</div>
                        <div class="decision-meta">{row.get("signal_type", "")} | {localize_value(row.get("universe_bucket", "core"))} | {localize_value(row.get("recommendation_bucket", "Watchlist"))}</div>
                    </div>
                    <div class="decision-meta">Score {float(row.get("composite_signal_score", 0)):.2f}</div>
                </div>
                <span class="decision-pill">{t("win_label")}: {row.get("win_rate_label", "N/A")}</span>
                <span class="decision-pill">{t("risk_label")}: {row.get("risk_level", "N/A")}</span>
                <span class="decision-pill">{t("reward_risk")}: {row.get("reward_risk_label", "N/A")}</span>
                <span class="decision-pill">{t("event_risk")}: {localize_value(row.get("event_risk_note", "clear"))}</span>
                <div class="decision-label">{t("suggested_action")}</div>
                <div>{row.get("suggested_action", "")}</div>
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
    st.title(t("title"))
    st.caption(t("caption"))
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
    left, right = st.columns((1.6, 1))
    with left:
        st.markdown(f'<div class="section-label">{t("portfolio_curve")}</div>', unsafe_allow_html=True)
        if snapshot.equity_curve.empty:
            st.info(t("no_closed_trades"))
        else:
            fig = px.line(snapshot.equity_curve, x="sequence", y="equity_pnl", markers=True, title=t("portfolio_curve"))
            st.plotly_chart(fig, use_container_width=True)
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
    fig = px.bar(frame, x="ticker", y="stop_buffer_percent", title=t("stop_buffer"))
    st.plotly_chart(fig, use_container_width=True)


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
                    "suggested_action",
                ]
                if column in display.columns
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
    ticker = st.text_input(t("ticker"), value="2330.TW")
    history = pd.DataFrame(repo.fetch_history(ticker))
    if history.empty:
        st.info(t("no_data"))
        return
    history = pd.DataFrame(decision_support.enrich_rows(history.to_dict("records")))
    latest_row = history.iloc[-1]
    top1, top2, top3, top4 = st.columns(4)
    top1.metric("Score", f"{float(latest_row.get('composite_signal_score', 0)):.2f}")
    top2.metric(t("bucket"), localize_value(latest_row.get("recommendation_bucket", "Watchlist")))
    top3.metric(t("win_label"), str(latest_row.get("win_rate_label", "")))
    top4.metric(t("risk_label"), str(latest_row.get("risk_level", "")))
    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.plotly_chart(px.line(history, x="date", y="close_price", markers=True, title=t("price_trend")), use_container_width=True)
    with chart_right:
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


inject_styles()

language_options = {"繁體中文": "zh-TW", "English": "en"}
selected_label = st.sidebar.selectbox(
    f'Language / {COPY["zh-TW"]["language"]}',
    options=list(language_options.keys()),
    index=0 if LANG == "zh-TW" else 1,
)
TEXT = COPY["zh-TW"] | COPY[language_options[selected_label]]

candidate_frame = load_candidate_frame()
nav = st.sidebar.radio(t("view"), [t("dashboard"), t("portfolio"), t("screener")], index=0)

if nav == t("dashboard"):
    render_dashboard(candidate_frame)
elif nav == t("portfolio"):
    render_portfolio()
else:
    render_screener(candidate_frame)
