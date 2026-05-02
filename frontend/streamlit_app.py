from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from investbot.data_sources.market_data import YahooMarketDataClient
from investbot.db.repositories import DailyAnalysisRepository
from investbot.services.dashboard_service import DashboardService
from investbot.services.portfolio_service import PortfolioService


st.set_page_config(page_title="Smart Swing Agent", layout="wide")

daily_analysis_repo = DailyAnalysisRepository()
portfolio_service = PortfolioService()
market_data = YahooMarketDataClient()
dashboard_service = DashboardService(portfolio_service=portfolio_service, market_data=market_data)

def render_dashboard() -> None:
    st.subheader("Dashboard")
    snapshot = dashboard_service.build_snapshot()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("VIX", f"{snapshot.vix:.2f}" if snapshot.vix is not None else "N/A")
    col2.metric("Sentiment", snapshot.market_sentiment)
    col3.metric("Open PnL", f"{snapshot.total_open_pnl:.2f}%")
    col4.metric("Win Rate", f"{snapshot.win_rate:.2f}%")

    left, right = st.columns((2, 1))
    with left:
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
        st.caption("Open Positions Overview")
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


def render_screener() -> None:
    st.subheader("Screener")
    latest_candidates = pd.DataFrame(daily_analysis_repo.fetch_recent_candidates(limit=100))
    if not latest_candidates.empty:
        st.caption("Latest candidates")
        filter_col1, filter_col2 = st.columns(2)
        selected_bucket = filter_col1.selectbox(
            "Recommendation bucket",
            options=["All", "Safer Follow-Through", "Actionable", "Watchlist"],
            index=0,
        )
        min_score = filter_col2.slider("Minimum composite score", min_value=0, max_value=100, value=60)
        filtered_candidates = latest_candidates.copy()
        if selected_bucket != "All":
            filtered_candidates = filtered_candidates[filtered_candidates["recommendation_bucket"] == selected_bucket]
        if "composite_signal_score" in filtered_candidates.columns:
            filtered_candidates = filtered_candidates[filtered_candidates["composite_signal_score"].fillna(0) >= min_score]
        candidate_columns = [
            "date",
            "ticker",
            "signal_type",
            "recommendation_bucket",
            "composite_signal_score",
            "institutional_buy_streak",
            "market_regime",
            "breadth_score",
            "event_risk_note",
            "next_event_date",
        ]
        available_columns = [column for column in candidate_columns if column in filtered_candidates.columns]
        st.dataframe(filtered_candidates[available_columns], use_container_width=True, hide_index=True)

    ticker = st.text_input("Ticker", value="2330.TW")
    history = daily_analysis_repo.fetch_history(ticker)
    if not history:
        st.warning("No analysis history found for this ticker. Run the scheduler first.")
        return

    frame = pd.DataFrame(history)
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
        if column not in frame.columns:
            frame[column] = default_value

    latest_row = frame.iloc[-1]

    top1, top2, top3, top4, top5 = st.columns(5)
    top1.metric("Composite", f"{float(latest_row['composite_signal_score']):.2f}")
    top2.metric("Regime", str(latest_row["market_regime"]))
    top3.metric("Bucket", str(latest_row["recommendation_bucket"]))
    top4.metric("Entry Timing", str(latest_row["entry_timing"]))
    top5.metric("Breadth", f"{float(latest_row['breadth_score']):.2f}")
    st.caption(f"Event risk: {latest_row['event_risk_note']} | Next event: {latest_row['next_event_date']}")

    fig = px.line(frame, x="date", y="close_price", markers=True, title=f"{ticker.upper()} price trend")
    st.plotly_chart(fig, use_container_width=True)
    flow_fig = px.bar(
        frame,
        x="date",
        y="institutional_net_buy",
        color="signal_type",
        title=f"{ticker.upper()} institutional flow",
    )
    st.plotly_chart(flow_fig, use_container_width=True)
    if frame["institutional_buy_streak"].notna().any():
        streak_fig = px.bar(
            frame.dropna(subset=["institutional_buy_streak"]),
            x="date",
            y="institutional_buy_streak",
            color="entry_timing",
            title=f"{ticker.upper()} institutional buying streak",
        )
        st.plotly_chart(streak_fig, use_container_width=True)

    score_columns = [
        "date",
        "market_regime",
        "market_regime_score",
        "breadth_score",
        "relative_strength_score",
        "institutional_conviction_score",
        "event_risk_note",
        "next_event_date",
        "entry_quality_score",
        "event_risk_score",
        "composite_signal_score",
        "recommendation_bucket",
    ]
    score_fig = px.line(
        frame,
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
    st.dataframe(frame[score_columns], use_container_width=True, hide_index=True)
    st.dataframe(frame, use_container_width=True, hide_index=True)


st.title("Smart Swing Agent")
tab_dashboard, tab_portfolio, tab_screener = st.tabs(["Dashboard", "Portfolio", "Screener"])

with tab_dashboard:
    render_dashboard()

with tab_portfolio:
    render_portfolio()

with tab_screener:
    render_screener()
