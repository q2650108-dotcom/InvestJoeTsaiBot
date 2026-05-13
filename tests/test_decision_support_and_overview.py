from __future__ import annotations

from datetime import date, datetime
from unittest import TestCase

from investbot.data_sources.derivatives_data import TaifexInstitutionRow, TaifexInstitutionSnapshot
from investbot.data_sources.market_data import FearGreedSnapshot
from investbot.data_sources.economic_calendar import EconomicCalendarEvent
from investbot.services.decision_support import DecisionSupportService
from investbot.services.market_overview_service import MarketOverviewService
from investbot.services.summary_service import SummaryService


class FakeOverviewRepository:
    def fetch_recent_candidates(self, limit: int = 200) -> list[dict[str, object]]:
        return [
            {
                "date": "2026-05-03",
                "ticker": "2330.TW",
                "type": "tw",
                "composite_signal_score": 84.0,
                "event_risk_note": "clear",
            },
            {
                "date": "2026-05-03",
                "ticker": "NVDA",
                "type": "us",
                "composite_signal_score": 80.0,
                "event_risk_note": "clear",
            },
            {
                "date": "2026-05-03",
                "ticker": "2603.TW",
                "type": "tw",
                "composite_signal_score": 74.0,
                "event_risk_note": "earnings_near",
            },
        ]

    def fetch_latest_market_rows(self, market_type: str) -> list[dict[str, object]]:
        if market_type == "tw":
            return [
                {
                    "date": "2026-05-03",
                    "ticker": "2330.TW",
                    "market_regime": "Risk-On",
                    "breadth_score": 70.0,
                    "recommendation_bucket": "Safer Follow-Through",
                    "universe_bucket": "core",
                    "institutional_buy_streak": 3,
                    "composite_signal_score": 84.0,
                    "event_risk_note": "clear",
                }
            ]
        return [
            {
                "date": "2026-05-03",
                "ticker": "NVDA",
                "market_regime": "Risk-On",
                "breadth_score": 64.0,
                "recommendation_bucket": "Actionable",
                "universe_bucket": "core",
                "institutional_buy_streak": 2,
                "composite_signal_score": 80.0,
                "event_risk_note": "clear",
            }
        ]


class FakeOverviewMarketData:
    def get_vix_value(self) -> float:
        return 16.5

    def get_fear_greed_snapshot(self) -> FearGreedSnapshot:
        return FearGreedSnapshot(
            score=70.0,
            rating="Greed",
            updated_at=datetime(2026, 5, 6, 13, 37, 15),
            previous_close=66.9,
        )


class FakeCalendarClient:
    def get_upcoming_events(self, **kwargs) -> list[EconomicCalendarEvent]:
        return [
            EconomicCalendarEvent(date(2026, 5, 5), "US", "FOMC Statement", "high"),
            EconomicCalendarEvent(date(2026, 5, 7), "US", "CPI", "high"),
        ]


class FakeDerivativesClient:
    def get_tw_tx_institution_snapshot(self, lookback_rows: int = 5, max_age_seconds: int = 1800) -> TaifexInstitutionSnapshot:
        return TaifexInstitutionSnapshot(
            latest_date=date(2026, 5, 6),
            source="TAIFEX",
            fetched_at=datetime(2026, 5, 6, 15, 0, 0),
            rows=[
                TaifexInstitutionRow(date(2026, 5, 6), foreign_net_oi=-51132, trust_net_oi=46177, dealer_net_oi=-1034),
                TaifexInstitutionRow(date(2026, 5, 5), foreign_net_oi=-48000, trust_net_oi=43000, dealer_net_oi=-900),
            ],
        )


class DecisionSupportAndOverviewTests(TestCase):
    def test_decision_support_generates_action_and_risk_text(self) -> None:
        service = DecisionSupportService()
        explanation = service.explain(
            {
                "recommendation_bucket": "Actionable",
                "universe_bucket": "explore",
                "institutional_buy_streak": 2,
                "composite_signal_score": 74.0,
                "relative_strength_score": 68.0,
                "event_risk_score": 60.0,
                "entry_quality_score": 62.0,
                "market_regime": "Risk-On",
                "event_risk_note": "clear",
            }
        )

        self.assertEqual(explanation.recommendation_level, "Actionable Setup")
        self.assertIn("Small trial size only", explanation.suggested_action)
        self.assertTrue(explanation.rationale)
        self.assertTrue(explanation.risks)

    def test_market_overview_builds_trend_and_momentum_zones(self) -> None:
        repository = FakeOverviewRepository()
        overview = MarketOverviewService(
            repository=repository,
            summary_service=SummaryService(repository=repository),
            market_data=FakeOverviewMarketData(),
            calendar_client=FakeCalendarClient(),
            derivatives_client=FakeDerivativesClient(),
        ).build()

        self.assertGreaterEqual(overview.fear_greed_score, 50)
        self.assertEqual(overview.overall_trend, "Risk-On Uptrend")
        self.assertEqual(overview.fear_greed_rating, "Greed")
        self.assertTrue(overview.momentum_zones)
        self.assertTrue(overview.caution_items)
        self.assertTrue(overview.upcoming_macro_events)
        self.assertIsNotNone(overview.tw_futures_snapshot)
