from __future__ import annotations

from unittest import TestCase

from investbot.services.dashboard_service import DashboardService
from investbot.services.notification_service import NotificationService


class FakePaperTradeRepository:
    def list_closed_trades(self, limit: int = 50) -> list[dict[str, object]]:
        return [
            {"ticker": "AAPL", "status": "CLOSED", "pnl_percent": 10.0, "sell_date": "2026-05-01"},
            {"ticker": "MSFT", "status": "CLOSED", "pnl_percent": -5.0, "sell_date": "2026-05-02"},
        ]


class FakePortfolioService:
    def get_open_positions_summary(self) -> tuple[list[dict[str, object]], float]:
        return (
            [
                {
                    "ticker": "2330.TW",
                    "latest_price": 110.0,
                    "live_pnl_percent": 10.0,
                    "stop_buffer_percent": 6.0,
                }
            ],
            10.0,
        )


class FakeMarketDataClient:
    def get_vix_value(self) -> float:
        return 17.5


class NotificationAndDashboardTests(TestCase):
    def test_notification_service_formats_signal_digest(self) -> None:
        message = NotificationService().format_signal_digest(
            [
                {
                    "ticker": "2330.TW",
                    "signal_type": "外資連買",
                    "close_price": 100.5,
                    "institutional_net_buy": 300,
                }
            ]
        )

        self.assertIn("Today's strategy candidates:", message)
        self.assertIn("2330.TW", message)

    def test_dashboard_service_computes_snapshot_metrics(self) -> None:
        service = DashboardService(
            portfolio_service=FakePortfolioService(),
            repository=FakePaperTradeRepository(),
            market_data=FakeMarketDataClient(),
        )

        snapshot = service.build_snapshot()

        self.assertEqual(snapshot.market_sentiment, "Calm")
        self.assertEqual(snapshot.total_open_pnl, 10.0)
        self.assertEqual(snapshot.win_rate, 50.0)
        self.assertEqual(snapshot.open_trade_count, 1)
        self.assertEqual(len(snapshot.equity_curve), 2)
