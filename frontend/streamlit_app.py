from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from investbot.data_sources.market_data import YahooMarketDataClient
from investbot.db.repositories import DailyAnalysisRepository
from investbot.services.portfolio_service import PortfolioService


st.set_page_config(page_title="Smart Swing Agent", layout="wide")

daily_analysis_repo = DailyAnalysisRepository()
portfolio_service = PortfolioService()
market_data = YahooMarketDataClient()


def load_dashboard_metrics() -> tuple[float | None, float, pd.DataFrame]:
    vix = market_data.get_vix_value()
    open_positions, total_pnl = portfolio_service.get_open_positions_summary()
    frame = pd.DataFrame(open_positions)
    return vix, total_pnl, frame


def render_dashboard() -> None:
    st.subheader("Dashboard")
    vix, total_pnl, positions = load_dashboard_metrics()

    col1, col2, col3 = st.columns(3)
    col1.metric("VIX", f"{vix:.2f}" if vix is not None else "N/A")
    col2.metric("Open PnL", f"{total_pnl:.2f}%")
    col3.metric("Open Trades", len(positions))

    if positions.empty:
        st.info("No open paper trades yet.")
        return

    equity_curve = positions[["ticker", "live_pnl_percent"]].copy()
    equity_curve["sequence"] = range(1, len(equity_curve) + 1)
    fig = px.line(
        equity_curve,
        x="sequence",
        y="live_pnl_percent",
        markers=True,
        title="Live PnL Curve",
    )
    st.plotly_chart(fig, use_container_width=True)


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


def render_screener() -> None:
    st.subheader("Screener")
    ticker = st.text_input("Ticker", value="2330.TW")
    history = daily_analysis_repo.fetch_history(ticker)
    if not history:
        st.warning("No analysis history found for this ticker. Run the scheduler first.")
        return

    frame = pd.DataFrame(history)
    fig = px.line(
        frame,
        x="date",
        y=["close_price", "institutional_net_buy"],
        markers=True,
        title=f"{ticker.upper()} institutional flow vs price",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(frame, use_container_width=True, hide_index=True)


st.title("Smart Swing Agent")
tab_dashboard, tab_portfolio, tab_screener = st.tabs(["Dashboard", "Portfolio", "Screener"])

with tab_dashboard:
    render_dashboard()

with tab_portfolio:
    render_portfolio()

with tab_screener:
    render_screener()
