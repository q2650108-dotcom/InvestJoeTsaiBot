from __future__ import annotations

from investbot.data_sources.market_data import YahooMarketDataClient
from investbot.db.repositories import PaperTradeRepository


class MonitorService:
    def __init__(
        self,
        repository: PaperTradeRepository | None = None,
        market_data: YahooMarketDataClient | None = None,
    ) -> None:
        self.repository = repository or PaperTradeRepository()
        self.market_data = market_data or YahooMarketDataClient()

    def scan_stop_losses(self) -> list[dict[str, object]]:
        alerts: list[dict[str, object]] = []
        for trade in self.repository.list_open_trades():
            latest_price = self.market_data.get_latest_price(trade["ticker"])
            if latest_price < float(trade["stop_loss_price"]):
                alerts.append(
                    {
                        "ticker": trade["ticker"],
                        "latest_price": round(latest_price, 2),
                        "stop_loss_price": float(trade["stop_loss_price"]),
                    }
                )
        return alerts
