from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

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


def render_header(snapshot) -> None:
    st.title("Smart Swing Agent")
    st.caption("Low-touch market brief for large-cap trend following and institutional flow monitoring.")

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("VIX", f"{snapshot.vix:.2f}" if snapshot.vix is not None else "N/A")
    metric2.metric("Sentiment", snapshot.market_sentiment)
    metric3.metric("Open PnL", f"{snapshot.total_open_pnl:.2f}%")
    metric4.metric("Win Rate", f"{snapshot.win_rate:.2f}%")


def render_market_overview() -> None:
    tw_summary = summary_service.build_market_summary("tw")
    us_summary = summary_service.build_market_summary("us")

    st.markdown('<div class="section-label">Market Overview</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        render_summary_band("Taiwan", tw_summary)
    with right:
        render_summary_band("US", us_summary)


def render_summary_band(label: str, summary) -> None:
    if summary is None:
        st.markdown(
            f"""
            <div class="summary-band">
                <div class="summary-title">{label}</div>
                <div class="summary-main">No data yet</div>
                <div class="summary-sub">Run the scheduled analysis first.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="summary-band">
            <div class="summary-title">{label}</div>
            <div class="summary-main">{summary.regime}</div>
            <div class="summary-sub">
                Breadth {summary.average_breadth:.2f} | Candidates {summary.candidate_count} |
                Actionable {summary.actionable_count} | Safer {summary.safer_count}
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
        st.dataframe(frame[columns], use_container_width=True, hide_index=True)


def render_focus_lists(candidate_frame: pd.DataFrame) -> None:
    st.markdown('<div class="section-label">Focus Lists</div>', unsafe_allow_html=True)
    if candidate_frame.empty:
        st.info("No candidates are available yet.")
        return

    latest_date = candidate_frame["date"].max()
    latest_frame = candidate_frame[candidate_frame["date"] == latest_date].copy()

    safer = latest_frame[latest_frame["recommendation_bucket"] == "Safer Follow-Through"].head(8)
    actionable = latest_frame[latest_frame["recommendation_bucket"] == "Actionable"].head(8)
    watchlist = latest_frame[latest_frame["recommendation_bucket"] == "Watchlist"].head(8)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("Safer Follow-Through")
        render_watchlist_table(safer)
    with col2:
        st.caption("Actionable")
        render_watchlist_table(actionable)
    with col3:
        st.caption("Watchlist")
        render_watchlist_table(watchlist)


def render_watchlist_table(frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("No names in this bucket.")
        return
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
    st.dataframe(frame[columns], use_container_width=True, hide_index=True)


def render_dashboard(candidate_frame: pd.DataFrame) -> None:
    snapshot = dashboard_service.build_snapshot()
    render_header(snapshot)
    render_market_overview()
    render_focus_lists(candidate_frame)

    left, right = st.columns((1.6, 1))
    with left:
        st.markdown('<div class="section-label">Portfolio Curve</div>', unsafe_allow_html=True)
        if snapshot.equity_curve.empty:
            st.info("No closed trades yet. Equity curve will appear after exits.")
        else:
            fig = px.line(
                snapshot.equity_curve,
                x="sequence",
                y="equity_pnl",
                markers=True,
                title="Closed Trade Equity Curve",
            )
            st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown('<div class="section-label">Open Positions</div>', unsafe_allow_html=True)
        if snapshot.open_positions.empty:
            st.info("No open positions.")
        else:
            st.dataframe(
                snapshot.open_positions[["ticker", "latest_price", "live_pnl_percent", "stop_buffer_percent"]],
                use_container_width=True,
                hide_index=True,
            )


def render_portfolio() -> None:
    st.subheader("Portfolio")
    positions, _ = portfolio_service.get_open_positions_summary()
    if not positions:
        st.info("No open positions.")
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
    frame["risk_flag"] = frame["stop_buffer_percent"].apply(lambda value: "Tight" if value < 3 else "Healthy")
    fig = px.bar(
        frame,
        x="ticker",
        y="stop_buffer_percent",
        color="risk_flag",
        title="Stop Buffer by Ticker",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_screener(candidate_frame: pd.DataFrame) -> None:
    st.subheader("Screener")
    if candidate_frame.empty:
        st.warning("No analysis history found yet. Run the scheduler first.")
        return

    latest_date = candidate_frame["date"].max()
    latest_candidates = candidate_frame[candidate_frame["date"] == latest_date].copy()

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    selected_market = filter_col1.selectbox("Market", options=["All", "tw", "us"], index=0)
    selected_bucket = filter_col2.selectbox(
        "Recommendation bucket",
        options=["All", "Safer Follow-Through", "Actionable", "Watchlist"],
        index=0,
    )
    min_score = filter_col3.slider("Minimum composite score", min_value=0, max_value=100, value=60)

    filtered_candidates = latest_candidates.copy()
    if selected_market != "All" and "type" in filtered_candidates.columns:
        filtered_candidates = filtered_candidates[filtered_candidates["type"] == selected_market]
    if selected_bucket != "All":
        filtered_candidates = filtered_candidates[filtered_candidates["recommendation_bucket"] == selected_bucket]
    filtered_candidates = filtered_candidates[filtered_candidates["composite_signal_score"] >= min_score]

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

    ticker = st.text_input("Ticker", value="2330.TW")
    history = pd.DataFrame(daily_analysis_repo.fetch_history(ticker))
    if history.empty:
        st.warning("No analysis history found for this ticker.")
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
    top1.metric("Composite", f"{float(latest_row['composite_signal_score']):.2f}")
    top2.metric("Regime", str(latest_row["market_regime"]))
    top3.metric("Bucket", str(latest_row["recommendation_bucket"]))
    top4.metric("Entry Timing", str(latest_row["entry_timing"]))
    top5.metric("Breadth", f"{float(latest_row['breadth_score']):.2f}")
    st.caption(f"Event risk: {latest_row['event_risk_note']} | Next event: {latest_row['next_event_date']}")

    chart_left, chart_right = st.columns((1.35, 1))
    with chart_left:
        fig = px.line(history, x="date", y="close_price", markers=True, title=f"{ticker.upper()} price trend")
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
            title=f"{ticker.upper()} funnel scores",
        )
        st.plotly_chart(score_fig, use_container_width=True)

    lower_left, lower_right = st.columns((1, 1))
    with lower_left:
        flow_fig = px.bar(
            history,
            x="date",
            y="institutional_net_buy",
            color="signal_type",
            title=f"{ticker.upper()} institutional flow",
        )
        st.plotly_chart(flow_fig, use_container_width=True)
    with lower_right:
        if history["institutional_buy_streak"].notna().any():
            streak_fig = px.bar(
                history.dropna(subset=["institutional_buy_streak"]),
                x="date",
                y="institutional_buy_streak",
                color="entry_timing",
                title=f"{ticker.upper()} institutional buying streak",
            )
            st.plotly_chart(streak_fig, use_container_width=True)


inject_styles()
candidate_frame = load_candidate_frame()

nav = st.sidebar.radio("View", ["Dashboard", "Portfolio", "Screener"], index=0)

if nav == "Dashboard":
    render_dashboard(candidate_frame)
elif nav == "Portfolio":
    render_portfolio()
else:
    render_screener(candidate_frame)
