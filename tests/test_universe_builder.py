from __future__ import annotations

import sys
import types
from types import SimpleNamespace
from unittest import TestCase

analysis_engine_stub = types.ModuleType("investbot.services.analysis_engine")


class AnalysisUniverse:
    def __init__(self, market_type: str, core_tickers: list[str], explore_tickers: list[str] | None = None) -> None:
        self.market_type = market_type
        self.core_tickers = core_tickers
        self.explore_tickers = explore_tickers or []


analysis_engine_stub.AnalysisUniverse = AnalysisUniverse
sys.modules.setdefault("investbot.services.analysis_engine", analysis_engine_stub)

from investbot.services.universe_builder import UniverseBuilder


class FakeTwseClient:
    def get_top_institutional_candidates(self, limit: int, exclude_tickers: list[str]) -> list[str]:
        assert "2330.TW" in exclude_tickers
        return ["2603.TW", "2454.TW", "1301.TW", "3037.TW"][:limit]


class UniverseBuilderTests(TestCase):
    def test_build_tw_merges_manual_lists_and_respects_excluded(self) -> None:
        settings = SimpleNamespace(
            tw_core_tickers="2330.TW,2317.TW",
            tw_explore_tickers="2383.TW",
            tw_explore_limit=12,
            tw_manual_watch_tickers="2603.TW,3037.TW",
            tw_manual_hot_tickers="2454.TW",
            tw_excluded_tickers="1301.TW,2317.TW",
            us_core_tickers="",
            us_explore_tickers="",
            us_explore_limit=8,
            us_manual_watch_tickers="",
            us_manual_hot_tickers="",
            us_excluded_tickers="",
        )
        builder = UniverseBuilder(settings=settings, twse_client=FakeTwseClient())

        result = builder.build("tw")

        self.assertEqual(result.core_tickers, ["2330.TW"])
        self.assertEqual(result.explore_tickers, ["2454.TW", "2603.TW", "3037.TW", "2383.TW"])

    def test_build_us_prioritizes_manual_lists_and_removes_excluded(self) -> None:
        settings = SimpleNamespace(
            tw_core_tickers="",
            tw_explore_tickers="",
            tw_explore_limit=12,
            tw_manual_watch_tickers="",
            tw_manual_hot_tickers="",
            tw_excluded_tickers="",
            us_core_tickers="AAPL,MSFT",
            us_explore_tickers="AMD,NFLX,AVGO",
            us_explore_limit=4,
            us_manual_watch_tickers="TSLA,AMD",
            us_manual_hot_tickers="PLTR",
            us_excluded_tickers="NFLX",
        )
        builder = UniverseBuilder(settings=settings, twse_client=FakeTwseClient())

        result = builder.build("us")

        self.assertEqual(result.core_tickers, ["AAPL", "MSFT"])
        self.assertEqual(result.explore_tickers, ["PLTR", "TSLA", "AMD", "AVGO"])
