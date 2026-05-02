from __future__ import annotations

import os
import sys
from pathlib import Path

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
        # Local development and some test runs may not configure Streamlit secrets.
        return


hydrate_env_from_streamlit_secrets()

from investbot.data_sources.market_data import YahooMarketDataClient
from investbot.db.repositories import DailyAnalysisRepository
from investbot.services.dashboard_service import DashboardService
from investbot.services.portfolio_service import PortfolioService
from investbot.services.summary_service import SummaryService


st.set_page_config(page_title="Smart Swing Agent", layout="wide", initial_sidebar_state="collapsed")

daily_analysis_repo = DailyAnalysisRepository()
portfolio_service = PortfolioService()
market_data = YahooMarketDataClient()
dashboard_service = DashboardService(portfolio_service=portfolio_service, market_data=market_data)
summary_service = SummaryService()


TRANSLATIONS = {
    "zh-TW": {
        "app_title": "Smart Swing Agent",
        "app_caption": "低維護市場摘要，專注權值龍頭趨勢與法人資金流。",
        "vix": "VIX",
        "sentiment": "市場情緒",
        "open_pnl": "未實現報酬",
        "win_rate": "勝率",
        "market_overview": "市場總覽",
        "taiwan": "台股",
        "us": "美股",
        "no_data_yet": "尚無資料",
        "run_scheduler_first": "請先跑一次排程分析。",
        "breadth": "廣度",
        "candidates": "候選",
        "actionable": "可行動",
        "safer": "相對安全",
        "focus_lists": "重點名單",
        "safer_follow_through": "相對安全延續",
        "watchlist": "觀察名單",
        "no_names_bucket": "這個分組目前沒有標的。",
        "no_candidates": "目前還沒有候選標的。",
        "portfolio_curve": "資金曲線",
        "open_positions": "持有部位",
        "no_closed_trades": "目前還沒有已平倉交易，之後會顯示資金曲線。",
        "no_open_positions": "目前沒有持倉。",
        "portfolio": "投資組合",
        "stop_buffer_by_ticker": "各標的停損緩衝",
        "tight": "偏緊",
        "healthy": "健康",
        "screener": "選股",
        "no_analysis_history": "尚無分析歷史，請先跑排程。",
        "market": "市場",
        "all": "全部",
        "recommendation_bucket": "建議分組",
        "minimum_composite_score": "最低綜合分數",
        "ticker": "代碼",
        "no_history_ticker": "這檔股票目前沒有分析歷史。",
        "composite": "綜合分數",
        "regime": "盤勢",
        "bucket": "分組",
        "entry_timing": "進場時機",
        "event_risk": "事件風險",
        "next_event": "下一事件",
        "price_trend": "價格走勢",
        "funnel_scores": "漏斗分數",
        "institutional_flow": "法人流向",
        "institutional_streak": "法人連買天數",
        "view": "檢視",
        "dashboard": "總覽",
        "unknown": "未知",
        "calm": "平穩",
        "neutral": "中性",
        "risk_off": "風險偏高",
        "language": "語言",
        "clear": "正常",
    },
    "en": {
        "app_title": "Smart Swing Agent",
        "app_caption": "Low-touch market brief for large-cap trend following and institutional flow monitoring.",
    },
}


def detect_language() -> str:
    try:
        accept_language = str(st.context.headers.get("Accept-Language", "")).lower()
    except Exception:
        accept_language = ""
    if accept_language.startswith("zh") or "zh-tw" in accept_language:
        return "zh-TW"
    return os.environ.get("APP_LANGUAGE", "zh-TW")


def build_text(language: str) -> dict[str, str]:
    text = dict(TRANSLATIONS["zh-TW"])
    text.update(TRANSLATIONS.get(language, {}))
    return text


def localize_value(value: object, text: dict[str, str]) -> str:
    mapping = {
        "Unknown": text["unknown"],
        "Calm": text["calm"],
        "Neutral": text["neutral"],
        "Risk-Off": text["risk_off"],
        "Watchlist": text["watchlist"],
        "Actionable": text["actionable"],
        "Safer Follow-Through": text["safer_follow_through"],
        "clear": text["clear"],
        "DAY_1_EARLY": "第 1 天偏早" if text["language"] == "語言" else "Day 1 Early",
        "DAY_2_BUILDING": "第 2 天建立中" if text["language"] == "語言" else "Day 2 Building",
        "DAY_3_PLUS_SAFER": "第 3 天以上較穩" if text["language"] == "語言" else "Day 3+ Safer",
    }
    return mapping.get(str(value), str(value))


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.1rem;
            padding-bottom: 2rem;
            max-width: 1380px;
        }
        .summary-band {
            border: 1px solid rgba(120, 120, 140, 0.2);
            border-radius: 8px;
            padding: 14px 16px;
            background: rgba(18, 22, 28, 0.04);
            margin-bottom: 12px;
        }
        .summary-title {
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            color: rgba(90, 100, 110, 0.95);
            margin-bottom: 4px;
        }
        .summary-main {
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .summary-sub {
            font-size: 0.84rem;
            color: rgba(90, 100, 110, 0.95);
        }
        .section-label {
            font-size: 0.82rem;
            font-weight: 600;
            color: rgba(90, 100, 110, 0.95);
            text-transform: uppercase;
            margin-top: 0.35rem;
            margin-bottom: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_candidate_frame(limit: int = 150) -> pd.DataFrame:
    frame = pd.DataFrame(daily_analysis_repo.fetch_recent_candidates(limit=limit))
    if frame.empty:
        return frame

    defaults = {
        "recommendation_bucket": "Watchlist",
        "composite_signal_score": 0.0,
        "institutional_buy_streak": 0,
        "breadth_score": 0.0,
        "market_regime": "Unknown",
        "event_risk_note": "clear",
        "next_event_date": None,
        "entry_timing": None,
        "signal_type": "",
    }
    for column, default_value in defaults.items():
        if column not in frame.columns:
            frame[column] = default_value
        else:
            frame[column] = frame[column].fillna(default_value)

    frame["composite_signal_score"] = frame["composite_signal_score"].astype(float)
    frame["institutional_buy_streak"] = frame["institutional_buy_streak"].astype(float)
    return frame


def render_header(snapshot, text: dict[str, str]) -> None:
    st.title(text["app_title"])
    st.caption(text["app_caption"])

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("VIX", f"{snapshot.vix:.2f}" if snapshot.vix is not None else "N/A")
    metric2.metric(text["sentiment"], localize_value(snapshot.market_sentiment, text))
    metric3.metric(text["open_pnl"], f"{snapshot.total_open_pnl:.2f}%")
    metric4.metric(text["win_rate"], f"{snapshot.win_rate:.2f}%")


def render_market_overview(text: dict[str, str]) -> None:
    tw_summary = summary_service.build_market_summary("tw")
    us_summary = summary_service.build_market_summary("us")

    st.markdown(f'<div class="section-label">{text["market_overview"]}</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        render_summary_band(text["taiwan"], tw_summary, text)
    with right:
        render_summary_band(text["us"], us_summary, text)


def render_summary_band(label: str, summary, text: dict[str, str]) -> None:
    if summary is None:
        st.markdown(
            f"""
            <div class="summary-band">
                <div class="summary-title">{label}</div>
                <div class="summary-main">{text["no_data_yet"]}</div>
                <div class="summary-sub">{text["run_scheduler_first"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="summary-band">
            <div class="summary-title">{label}</div>
            <div class="summary-main">{localize_value(summary.regime, text)}</div>
            <div class="summary-sub">
                {text["breadth"]} {summary.average_breadth:.2f} | {text["candidates"]} {summary.candidate_count} |
                {text["actionable"]} {summary.actionable_count} | {text["safer"]} {summary.safer_count}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    frame = pd.DataFrame(summary.top_rows)
    if not frame.empty:
        columns = [
            column
            for column in ["ticker", "recommendation_bucket", "composite_signal_score", "institutional_buy_streak"]
            if column in frame.columns
        ]
        if "recommendation_bucket" in frame.columns:
            frame["recommendation_bucket"] = frame["recommendation_bucket"].map(lambda value: localize_value(value, text))
        st.dataframe(frame[columns], use_container_width=True, hide_index=True)


def render_focus_lists(candidate_frame: pd.DataFrame, text: dict[str, str]) -> None:
    st.markdown(f'<div class="section-label">{text["focus_lists"]}</div>', unsafe_allow_html=True)
    if candidate_frame.empty:
        st.info(text["no_candidates"])
        return

    latest_date = candidate_frame["date"].max()
    latest_frame = candidate_frame[candidate_frame["date"] == latest_date].copy()

    safer = latest_frame[latest_frame["recommendation_bucket"] == "Safer Follow-Through"].head(8)
    actionable = latest_frame[latest_frame["recommendation_bucket"] == "Actionable"].head(8)
    watchlist = latest_frame[latest_frame["recommendation_bucket"] == "Watchlist"].head(8)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(text["safer_follow_through"])
        render_watchlist_table(safer, text)
    with col2:
        st.caption(text["actionable"])
        render_watchlist_table(actionable, text)
    with col3:
        st.caption(text["watchlist"])
        render_watchlist_table(watchlist, text)


def render_watchlist_table(frame: pd.DataFrame, text: dict[str, str]) -> None:
    if frame.empty:
        st.info(text["no_names_bucket"])
        return
    localized_frame = frame.copy()
    for column in ["recommendation_bucket", "entry_timing", "event_risk_note"]:
        if column in localized_frame.columns:
            localized_frame[column] = localized_frame[column].map(lambda value: localize_value(value, text))
    columns = [
        column
        for column in [
            "ticker",
            "signal_type",
            "composite_signal_score",
            "institutional_buy_streak",
            "entry_timing",
            "event_risk_note",
        ]
        if column in frame.columns
    ]
    st.dataframe(localized_frame[columns], use_container_width=True, hide_index=True)


def render_dashboard(candidate_frame: pd.DataFrame, text: dict[str, str]) -> None:
    snapshot = dashboard_service.build_snapshot()
    render_header(snapshot, text)
    render_market_overview(text)
    render_focus_lists(candidate_frame, text)

    left, right = st.columns((1.6, 1))
    with left:
        st.markdown(f'<div class="section-label">{text["portfolio_curve"]}</div>', unsafe_allow_html=True)
        if snapshot.equity_curve.empty:
            st.info(text["no_closed_trades"])
        else:
            fig = px.line(
                snapshot.equity_curve,
                x="sequence",
                y="equity_pnl",
                markers=True,
                title=text["portfolio_curve"],
            )
            st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown(f'<div class="section-label">{text["open_positions"]}</div>', unsafe_allow_html=True)
        if snapshot.open_positions.empty:
            st.info(text["no_open_positions"])
        else:
            st.dataframe(
                snapshot.open_positions[["ticker", "latest_price", "live_pnl_percent", "stop_buffer_percent"]],
                use_container_width=True,
                hide_index=True,
            )


def render_portfolio(text: dict[str, str]) -> None:
    st.subheader(text["portfolio"])
    positions, _ = portfolio_service.get_open_positions_summary()
    if not positions:
        st.info(text["no_open_positions"])
        return

    frame = pd.DataFrame(positions)
    display_columns = [
        "ticker",
        "buy_date",
        "buy_price",
        "latest_price",
        "stop_loss_price",
        "live_pnl_percent",
        "stop_buffer_percent",
    ]
    st.dataframe(frame[display_columns], use_container_width=True, hide_index=True)
    frame["risk_flag"] = frame["stop_buffer_percent"].apply(
        lambda value: text["tight"] if value < 3 else text["healthy"]
    )
    fig = px.bar(
        frame,
        x="ticker",
        y="stop_buffer_percent",
        color="risk_flag",
        title=text["stop_buffer_by_ticker"],
    )
    st.plotly_chart(fig, use_container_width=True)


def render_screener(candidate_frame: pd.DataFrame, text: dict[str, str]) -> None:
    st.subheader(text["screener"])
    if candidate_frame.empty:
        st.warning(text["no_analysis_history"])
        return

    latest_date = candidate_frame["date"].max()
    latest_candidates = candidate_frame[candidate_frame["date"] == latest_date].copy()

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    selected_market = filter_col1.selectbox(text["market"], options=[text["all"], "tw", "us"], index=0)
    selected_bucket = filter_col2.selectbox(
        text["recommendation_bucket"],
        options=[text["all"], text["safer_follow_through"], text["actionable"], text["watchlist"]],
        index=0,
    )
    min_score = filter_col3.slider(text["minimum_composite_score"], min_value=0, max_value=100, value=60)

    filtered_candidates = latest_candidates.copy()
    if selected_market != text["all"] and "type" in filtered_candidates.columns:
        filtered_candidates = filtered_candidates[filtered_candidates["type"] == selected_market]
    bucket_reverse_map = {
        text["safer_follow_through"]: "Safer Follow-Through",
        text["actionable"]: "Actionable",
        text["watchlist"]: "Watchlist",
    }
    if selected_bucket != text["all"]:
        filtered_candidates = filtered_candidates[
            filtered_candidates["recommendation_bucket"] == bucket_reverse_map[selected_bucket]
        ]
    filtered_candidates = filtered_candidates[filtered_candidates["composite_signal_score"] >= min_score]
    if "recommendation_bucket" in filtered_candidates.columns:
        filtered_candidates["recommendation_bucket"] = filtered_candidates["recommendation_bucket"].map(
            lambda value: localize_value(value, text)
        )
    if "market_regime" in filtered_candidates.columns:
        filtered_candidates["market_regime"] = filtered_candidates["market_regime"].map(
            lambda value: localize_value(value, text)
        )
    if "event_risk_note" in filtered_candidates.columns:
        filtered_candidates["event_risk_note"] = filtered_candidates["event_risk_note"].map(
            lambda value: localize_value(value, text)
        )

    candidate_columns = [
        "ticker",
        "signal_type",
        "recommendation_bucket",
        "composite_signal_score",
        "institutional_buy_streak",
        "entry_timing",
        "market_regime",
        "breadth_score",
        "event_risk_note",
        "next_event_date",
    ]
    available_columns = [column for column in candidate_columns if column in filtered_candidates.columns]
    st.dataframe(filtered_candidates[available_columns], use_container_width=True, hide_index=True)

    ticker = st.text_input(text["ticker"], value="2330.TW")
    history = pd.DataFrame(daily_analysis_repo.fetch_history(ticker))
    if history.empty:
        st.warning(text["no_history_ticker"])
        return

    defaults = {
        "institutional_buy_streak": None,
        "entry_timing": None,
        "market_regime": "Unknown",
        "market_regime_score": 0.0,
        "breadth_score": 0.0,
        "relative_strength_score": 0.0,
        "institutional_conviction_score": 0.0,
        "event_risk_score": 50.0,
        "next_event_date": None,
        "event_risk_note": "clear",
        "entry_quality_score": 0.0,
        "composite_signal_score": 0.0,
        "recommendation_bucket": "Watchlist",
    }
    for column, default_value in defaults.items():
        if column not in history.columns:
            history[column] = default_value
        else:
            history[column] = history[column].fillna(default_value)

    latest_row = history.iloc[-1]
    top1, top2, top3, top4, top5 = st.columns(5)
    top1.metric(text["composite"], f"{float(latest_row['composite_signal_score']):.2f}")
    top2.metric(text["regime"], localize_value(latest_row["market_regime"], text))
    top3.metric(text["bucket"], localize_value(latest_row["recommendation_bucket"], text))
    top4.metric(text["entry_timing"], localize_value(latest_row["entry_timing"], text))
    top5.metric(text["breadth"], f"{float(latest_row['breadth_score']):.2f}")
    st.caption(
        f"{text['event_risk']}: {localize_value(latest_row['event_risk_note'], text)} | "
        f"{text['next_event']}: {latest_row['next_event_date']}"
    )

    chart_left, chart_right = st.columns((1.35, 1))
    with chart_left:
        fig = px.line(history, x="date", y="close_price", markers=True, title=f"{ticker.upper()} {text['price_trend']}")
        st.plotly_chart(fig, use_container_width=True)
    with chart_right:
        score_fig = px.line(
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
            title=f"{ticker.upper()} {text['funnel_scores']}",
        )
        st.plotly_chart(score_fig, use_container_width=True)

    lower_left, lower_right = st.columns((1, 1))
    with lower_left:
        flow_fig = px.bar(
            history,
            x="date",
            y="institutional_net_buy",
            color="signal_type",
            title=f"{ticker.upper()} {text['institutional_flow']}",
        )
        st.plotly_chart(flow_fig, use_container_width=True)
    with lower_right:
        if history["institutional_buy_streak"].notna().any():
            streak_fig = px.bar(
                history.dropna(subset=["institutional_buy_streak"]),
                x="date",
                y="institutional_buy_streak",
                color="entry_timing",
                title=f"{ticker.upper()} {text['institutional_streak']}",
            )
            st.plotly_chart(streak_fig, use_container_width=True)


inject_styles()
candidate_frame = load_candidate_frame()

language_options = {"繁體中文": "zh-TW", "English": "en"}
default_language = detect_language()
language_label = next((label for label, code in language_options.items() if code == default_language), "繁體中文")
selected_language_label = st.sidebar.selectbox("Language / 語言", options=list(language_options.keys()), index=list(language_options.keys()).index(language_label))
text = build_text(language_options[selected_language_label])

nav = st.sidebar.radio(text["view"], [text["dashboard"], text["portfolio"], text["screener"]], index=0)

if nav == text["dashboard"]:
    render_dashboard(candidate_frame, text)
elif nav == text["portfolio"]:
    render_portfolio(text)
else:
    render_screener(candidate_frame, text)
