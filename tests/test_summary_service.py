from __future__ import annotations

from unittest import TestCase

from investbot.services.summary_service import SummaryService


class FakeDailyAnalysisRepository:
    def fetch_latest_market_rows(self, market_type: str) -> list[dict[str, object]]:
        return [
            {
                "date": "2026-05-02",
                "ticker": "2330.TW",
                "market_regime": "Risk-On",
                "breadth_score": 72.0,
                "recommendation_bucket": "Safer Follow-Through",
                "institutional_buy_streak": 3,
                "composite_signal_score": 84.0,
                "event_risk_note": "clear",
            },
            {
                "date": "2026-05-02",
                "ticker": "2317.TW",
                "market_regime": "Risk-On",
                "breadth_score": 68.0,
                "recommendation_bucket": "Actionable",
                "institutional_buy_streak": 2,
                "composite_signal_score": 72.0,
                "event_risk_note": "earnings_near",
                "next_event_date": "2026-05-05",
            },
        ]


class SummaryServiceTests(TestCase):
    def test_build_market_summary_returns_top_and_risk_rows(self) -> None:
        service = SummaryService(repository=FakeDailyAnalysisRepository())

        summary = service.build_market_summary("tw")

        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary.regime, "Risk-On")
        self.assertEqual(summary.actionable_count, 1)
        self.assertEqual(summary.safer_count, 1)
        self.assertEqual(summary.top_rows[0]["ticker"], "2330.TW")
        self.assertEqual(summary.risk_rows[0]["ticker"], "2317.TW")
