from __future__ import annotations

from unittest import TestCase

from investbot.services.holdings_library_service import HoldingsLibraryService


class FakeAnalysisRepository:
    def __init__(self, rows_by_ticker: dict[str, list[dict[str, object]]] | None = None) -> None:
        self.rows_by_ticker = rows_by_ticker or {}

    def fetch_history(self, ticker: str, limit: int = 1) -> list[dict[str, object]]:
        return self.rows_by_ticker.get(ticker.upper(), [])[:limit]


class FakeWatchlistRepository:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []

    def upsert_entry(self, payload: dict[str, object]) -> dict[str, object]:
        self.rows.append(payload)
        return payload


class FakeGuruPortfolioRepository:
    def __init__(self, cached: dict[str, dict[str, object]] | None = None) -> None:
        self.cached = cached or {}
        self.last_upsert: dict[str, object] | None = None

    def fetch_latest_by_guru(self, guru_name: str) -> dict[str, object] | None:
        return self.cached.get(guru_name)

    def upsert_portfolio(self, payload: dict[str, object]) -> dict[str, object]:
        self.last_upsert = payload
        self.cached[str(payload["guru_name"])] = payload
        return payload


class StubHoldingsLibraryService(HoldingsLibraryService):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.etf_rows: dict[str, list[dict[str, object]]] = {}
        self.guru_rows: dict[str, tuple[str, str, list[dict[str, object]]]] = {}

    def _load_etf_holdings(self, definition):  # type: ignore[override]
        rows = self.etf_rows.get(definition.source_id, [])
        return {
            "as_of": "2026-05-15",
            "fetched_at": "2026-05-16T09:00:00+08:00",
            "rows": rows,
            "source_note": "test",
        }

    def _load_guru_holdings(self, definition):  # type: ignore[override]
        quarter, as_of, rows = self.guru_rows.get(definition.source_id, ("2026-Q1", "2026-03-31", []))
        return {
            "quarter": quarter,
            "as_of": as_of,
            "fetched_at": "2026-05-16T09:00:00+08:00",
            "rows": rows,
            "source_note": "test",
        }


class HoldingsLibraryServiceTests(TestCase):
    def test_list_sources_groups_and_orders_sources(self) -> None:
        service = HoldingsLibraryService(
            analysis_repository=FakeAnalysisRepository(),
            watchlist_repository=FakeWatchlistRepository(),
            guru_repository=FakeGuruPortfolioRepository(),
        )

        rows = service.list_sources()

        self.assertEqual(rows[0]["group_key"], "tw_etf")
        self.assertEqual(rows[0]["symbol"], "0050.TW")
        self.assertTrue(any(row["group_key"] == "us_etf" for row in rows))
        self.assertTrue(any(row["group_key"] == "guru_13f" for row in rows))

    def test_get_source_snapshot_enriches_holdings_with_latest_analysis(self) -> None:
        analysis_repo = FakeAnalysisRepository(
            rows_by_ticker={
                "2330.TW": [
                    {
                        "ticker": "2330.TW",
                        "close_price": 950.0,
                        "composite_signal_score": 83.5,
                        "confluence_score": 88.0,
                        "recommendation_bucket": "Actionable",
                        "institutional_buy_streak": 4,
                        "date": "2026-05-15",
                    }
                ]
            }
        )
        service = StubHoldingsLibraryService(
            analysis_repository=analysis_repo,
            watchlist_repository=FakeWatchlistRepository(),
            guru_repository=FakeGuruPortfolioRepository(),
        )
        service.etf_rows["tw-0050"] = [
            {"ticker": "2330.TW", "name": "TSMC", "weight": 58.2, "shares": 1000},
            {"ticker": "2317.TW", "name": "Hon Hai", "weight": 4.8, "shares": 2000},
        ]

        snapshot = service.get_source_snapshot("tw-0050")

        self.assertEqual(snapshot["source"]["symbol"], "0050.TW")
        self.assertEqual(snapshot["holdings"][0]["ticker"], "2330.TW")
        self.assertEqual(snapshot["holdings"][0]["close_price"], 950.0)
        self.assertEqual(snapshot["holdings"][0]["composite_signal_score"], 83.5)
        self.assertEqual(snapshot["holdings"][0]["recommendation_bucket"], "Actionable")

    def test_add_to_watchlist_persists_source_tag(self) -> None:
        watchlist_repo = FakeWatchlistRepository()
        service = HoldingsLibraryService(
            analysis_repository=FakeAnalysisRepository(),
            watchlist_repository=watchlist_repo,
            guru_repository=FakeGuruPortfolioRepository(),
        )

        service.add_to_watchlist("705748524", "2330.TW", "Berkshire Top Holdings")

        self.assertEqual(watchlist_repo.rows[0]["telegram_chat_id"], "705748524")
        self.assertEqual(watchlist_repo.rows[0]["ticker"], "2330.TW")
        self.assertEqual(watchlist_repo.rows[0]["added_from"], "Berkshire Top Holdings")
