from __future__ import annotations

from unittest import TestCase

from investbot.services.monitor_service import MonitorService
from investbot.services.portfolio_service import PortfolioService


class FakePaperTradeRepository:
    def __init__(self, trades: list[dict[str, object]]) -> None:
        self.trades = trades
        self.created_payload: dict[str, object] | None = None
        self.closed_payload: dict[str, object] | None = None

    def list_open_trades(self) -> list[dict[str, object]]:
        return [trade for trade in self.trades if trade["status"] == "OPEN"]

    def create_trade(self, payload: dict[str, object]) -> dict[str, object]:
        self.created_payload = payload
        return payload

    def find_open_trade_by_ticker(self, ticker: str) -> dict[str, object] | None:
        for trade in self.trades:
            if trade["ticker"] == ticker.upper() and trade["status"] == "OPEN":
                return trade
        return None

    def close_trade(self, trade_id: str, payload: dict[str, object]) -> dict[str, object]:
        self.closed_payload = payload
        return payload


class FakeMarketDataClient:
    def __init__(self, price_map: dict[str, float]) -> None:
        self.price_map = price_map

    def get_latest_price(self, ticker: str) -> float:
        return self.price_map[ticker.upper()]


class PortfolioAndMonitorTests(TestCase):
    def test_create_paper_trade_rejects_duplicate_open_trade(self) -> None:
        repository = FakePaperTradeRepository(
            trades=[
                {
                    "id": "1",
                    "ticker": "2330.TW",
                    "buy_price": 100.0,
                    "stop_loss_price": 90.0,
                    "status": "OPEN",
                }
            ]
        )
        service = PortfolioService(
            repository=repository,
            market_data=FakeMarketDataClient({"2330.TW": 110.0}),
        )

        with self.assertRaisesRegex(ValueError, "OPEN trade already exists"):
            service.create_paper_trade("2330.TW", 90.0)

    def test_create_paper_trade_rejects_invalid_stop_loss(self) -> None:
        repository = FakePaperTradeRepository(trades=[])
        service = PortfolioService(
            repository=repository,
            market_data=FakeMarketDataClient({"2330.TW": 110.0}),
        )

        with self.assertRaisesRegex(ValueError, "below the latest price"):
            service.create_paper_trade("2330.TW", 120.0)

    def test_get_open_positions_summary_computes_live_pnl_and_stop_buffer(self) -> None:
        repository = FakePaperTradeRepository(
            trades=[
                {
                    "id": "1",
                    "ticker": "2330.TW",
                    "buy_price": 100.0,
                    "stop_loss_price": 90.0,
                    "status": "OPEN",
                }
            ]
        )
        service = PortfolioService(
            repository=repository,
            market_data=FakeMarketDataClient({"2330.TW": 110.0}),
        )

        positions, total_pnl = service.get_open_positions_summary()

        self.assertEqual(total_pnl, 10.0)
        self.assertEqual(positions[0]["latest_price"], 110.0)
        self.assertEqual(positions[0]["live_pnl_percent"], 10.0)
        self.assertEqual(positions[0]["stop_buffer_percent"], 18.18)

    def test_monitor_service_returns_alert_when_price_breaks_stop_loss(self) -> None:
        repository = FakePaperTradeRepository(
            trades=[
                {
                    "id": "1",
                    "ticker": "AAPL",
                    "buy_price": 200.0,
                    "stop_loss_price": 180.0,
                    "status": "OPEN",
                }
            ]
        )
        service = MonitorService(
            repository=repository,
            market_data=FakeMarketDataClient({"AAPL": 175.0}),
        )

        alerts = service.scan_stop_losses()

        self.assertEqual(
            alerts,
            [{"ticker": "AAPL", "latest_price": 175.0, "stop_loss_price": 180.0}],
        )
