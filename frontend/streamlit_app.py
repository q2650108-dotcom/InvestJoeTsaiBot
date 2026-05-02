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
    ticker = st.text_input("Ticker", value="2330.TW")
    history = daily_analysis_repo.fetch_history(ticker)
    if not history:
        st.warning("No analysis history found for this ticker. Run the scheduler first.")
        return

    frame = pd.DataFrame(history)
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
    st.dataframe(frame, use_container_width=True, hide_index=True)


st.title("Smart Swing Agent")
tab_dashboard, tab_portfolio, tab_screener = st.tabs(["Dashboard", "Portfolio", "Screener"])

with tab_dashboard:
    render_dashboard()

with tab_portfolio:
    render_portfolio()

with tab_screener:
    render_screener()
