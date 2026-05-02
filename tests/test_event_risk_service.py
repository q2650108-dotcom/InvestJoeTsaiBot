from __future__ import annotations

from datetime import date
from unittest import TestCase

from investbot.services.event_risk_service import EventRiskService


class FakeMarketDataClient:
    def __init__(self, next_earnings_date: date | None) -> None:
        self.next_earnings_date = next_earnings_date

    def get_next_earnings_date(self, ticker: str) -> date | None:
        return self.next_earnings_date


class EventRiskServiceTests(TestCase):
    def test_assess_penalizes_imminent_earnings(self) -> None:
        service = EventRiskService(
            market_data=FakeMarketDataClient(date(2026, 5, 3)),
            high_risk_event_dates=[],
        )

        assessment = service.assess("AAPL", date(2026, 5, 1))

        self.assertLess(assessment.score, 70.0)
        self.assertEqual(assessment.note, "earnings_imminent")

    def test_assess_penalizes_macro_event_window(self) -> None:
        service = EventRiskService(
            market_data=FakeMarketDataClient(None),
            high_risk_event_dates=[date(2026, 5, 2)],
        )

        assessment = service.assess("AAPL", date(2026, 5, 1))

        self.assertLess(assessment.score, 70.0)
        self.assertEqual(assessment.note, "macro_event_imminent")
