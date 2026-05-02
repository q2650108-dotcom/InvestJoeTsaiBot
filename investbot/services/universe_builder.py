from __future__ import annotations

from dataclasses import dataclass

from typing import Any

from investbot.data_sources.twse import TwseClient
from investbot.services.analysis_engine import AnalysisUniverse


@dataclass(slots=True)
class UniverseBuildResult:
    market_type: str
    core_tickers: list[str]
    explore_tickers: list[str]

    def to_analysis_universe(self) -> AnalysisUniverse:
        return AnalysisUniverse(
            market_type=self.market_type,
            core_tickers=self.core_tickers,
            explore_tickers=self.explore_tickers,
        )


class UniverseBuilder:
    def __init__(self, settings: Any, twse_client: TwseClient | None = None) -> None:
        self.settings = settings
        self.twse_client = twse_client or TwseClient()

    def build(self, market_type: str) -> UniverseBuildResult:
        if market_type == "tw":
            core_tickers = self._parse_tickers(
                self.settings.tw_core_tickers,
                ["2330.TW", "2317.TW", "2454.TW", "2308.TW", "0050.TW"],
            )
            manual_explore = self._parse_tickers(self.settings.tw_explore_tickers, [])
            dynamic_explore = self.twse_client.get_top_institutional_candidates(
                limit=self.settings.tw_explore_limit,
                exclude_tickers=core_tickers,
            )
            explore_tickers = self._merge_unique(manual_explore, dynamic_explore)
            return UniverseBuildResult(market_type="tw", core_tickers=core_tickers, explore_tickers=explore_tickers)

        core_tickers = self._parse_tickers(
            self.settings.us_core_tickers,
            ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "SPY", "QQQ"],
        )
        manual_explore = self._parse_tickers(
            self.settings.us_explore_tickers,
            ["AVGO", "AMD", "NFLX", "PLTR", "TSLA", "IWM", "DIA", "SMH"],
        )
        explore_tickers = manual_explore[: self.settings.us_explore_limit]
        return UniverseBuildResult(market_type="us", core_tickers=core_tickers, explore_tickers=explore_tickers)

    def _parse_tickers(self, raw_value: str, fallback: list[str]) -> list[str]:
        values = [item.strip().upper() for item in raw_value.split(",") if item.strip()]
        return values or fallback

    def _merge_unique(self, *groups: list[str]) -> list[str]:
        merged: list[str] = []
        for group in groups:
            for ticker in group:
                normalized = ticker.upper()
                if normalized not in merged:
                    merged.append(normalized)
        return merged
