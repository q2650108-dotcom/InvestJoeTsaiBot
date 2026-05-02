from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from investbot.data_sources.market_data import YahooMarketDataClient
from investbot.db.repositories import PaperTradeRepository
from investbot.services.portfolio_service import PortfolioService


@dataclass(slots=True)
class DashboardSnapshot:
    vix: float | None
    market_sentiment: str
    total_open_pnl: float
    win_rate: float
    open_trade_count: int
    equity_curve: pd.DataFrame
    open_positions: pd.DataFrame
    recent_closed_trades: pd.DataFrame


class DashboardService:
    def __init__(
        self,
        portfolio_service: PortfolioService | None = None,
        repository: PaperTradeRepository | None = None,
        market_data: YahooMarketDataClient | None = None,
    ) -> None:
        self.portfolio_service = portfolio_service or PortfolioService()
        self.repository = repository or PaperTradeRepository()
        self.market_data = market_data or YahooMarketDataClient()

    def build_snapshot(self) -> DashboardSnapshot:
        open_positions, total_open_pnl = self.portfolio_service.get_open_positions_summary()
        closed_trades = self.repository.list_closed_trades()
        vix = self.market_data.get_vix_value()

        open_positions_df = pd.DataFrame(open_positions)
        closed_trades_df = pd.DataFrame(closed_trades)
        equity_curve = self._build_equity_curve(closed_trades_df)

        win_rate = self._compute_win_rate(closed_trades_df)
        market_sentiment = self._classify_vix(vix)

        return DashboardSnapshot(
            vix=vix,
            market_sentiment=market_sentiment,
            total_open_pnl=total_open_pnl,
            win_rate=win_rate,
            open_trade_count=len(open_positions),
            equity_curve=equity_curve,
            open_positions=open_positions_df,
            recent_closed_trades=closed_trades_df,
        )

    def _build_equity_curve(self, closed_trades_df: pd.DataFrame) -> pd.DataFrame:
        if closed_trades_df.empty:
            return pd.DataFrame(columns=["sequence", "equity_pnl"])

        frame = closed_trades_df.copy()
        frame["pnl_percent"] = frame["pnl_percent"].fillna(0.0).astype(float)
        frame["sequence"] = range(1, len(frame) + 1)
        frame["equity_pnl"] = frame["pnl_percent"].cumsum()
        return frame[["sequence", "equity_pnl"]]

    def _compute_win_rate(self, closed_trades_df: pd.DataFrame) -> float:
        if closed_trades_df.empty:
            return 0.0

        pnl_series = closed_trades_df["pnl_percent"].fillna(0.0).astype(float)
        wins = (pnl_series > 0).sum()
        return round((wins / len(closed_trades_df)) * 100, 2)

    def _classify_vix(self, vix: float | None) -> str:
        if vix is None:
            return "Unknown"
        if vix < 18:
            return "Calm"
        if vix < 25:
            return "Neutral"
        return "Risk-Off"
