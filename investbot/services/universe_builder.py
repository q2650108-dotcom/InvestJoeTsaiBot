from __future__ import annotations

from dataclasses import dataclass

from typing import Any

from investbot.data_sources.twse import TwseClient
from investbot.db.repositories import UserWatchlistRepository
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
    def __init__(
        self,
        settings: Any,
        twse_client: TwseClient | None = None,
        watchlist_repository: UserWatchlistRepository | None = None,
    ) -> None:
        self.settings = settings
        self.twse_client = twse_client or TwseClient()
        self.watchlist_repository = watchlist_repository

    def build(self, market_type: str) -> UniverseBuildResult:
        if market_type == "tw":
            excluded_tickers = set(self._parse_tickers(getattr(self.settings, "tw_excluded_tickers", ""), []))
            core_tickers = self._filter_excluded(
                self._parse_tickers(
                    self.settings.tw_core_tickers,
                    ["2330.TW", "2317.TW", "2454.TW", "2308.TW", "0050.TW"],
                ),
                excluded_tickers,
            )
            manual_watch = self._filter_excluded(
                self._parse_tickers(getattr(self.settings, "tw_manual_watch_tickers", ""), []),
                excluded_tickers,
            )
            manual_hot = self._filter_excluded(
                self._parse_tickers(getattr(self.settings, "tw_manual_hot_tickers", ""), []),
                excluded_tickers,
            )
            manual_explore = self._filter_excluded(
                self._parse_tickers(self.settings.tw_explore_tickers, []),
                excluded_tickers,
            )
            watchlist_explore = self._load_watchlist_tickers("tw", excluded_tickers)
            pinned_explore = self._merge_unique(manual_hot, manual_watch, watchlist_explore, manual_explore)
            dynamic_explore = self._filter_excluded(
                self.twse_client.get_top_institutional_candidates(
                    limit=self.settings.tw_explore_limit,
                    exclude_tickers=self._merge_unique(core_tickers, pinned_explore),
                ),
                excluded_tickers,
            )
            explore_tickers = [
                ticker for ticker in self._merge_unique(pinned_explore, dynamic_explore) if ticker not in core_tickers
            ]
            return UniverseBuildResult(market_type="tw", core_tickers=core_tickers, explore_tickers=explore_tickers)

        excluded_tickers = set(self._parse_tickers(getattr(self.settings, "us_excluded_tickers", ""), []))
        core_tickers = self._filter_excluded(
            self._parse_tickers(
                self.settings.us_core_tickers,
                ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "SPY", "QQQ"],
            ),
            excluded_tickers,
        )
        manual_watch = self._filter_excluded(
            self._parse_tickers(getattr(self.settings, "us_manual_watch_tickers", ""), []),
            excluded_tickers,
        )
        manual_hot = self._filter_excluded(
            self._parse_tickers(getattr(self.settings, "us_manual_hot_tickers", ""), []),
            excluded_tickers,
        )
        manual_explore = self._filter_excluded(
            self._parse_tickers(
                self.settings.us_explore_tickers,
                ["AVGO", "AMD", "NFLX", "PLTR", "TSLA", "IWM", "DIA", "SMH"],
            ),
            excluded_tickers,
        )
        watchlist_explore = self._load_watchlist_tickers("us", excluded_tickers)
        explore_tickers = [
            ticker
            for ticker in self._merge_unique(manual_hot, manual_watch, watchlist_explore, manual_explore)
            if ticker not in core_tickers
        ][: self.settings.us_explore_limit]
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

    def _filter_excluded(self, tickers: list[str], excluded_tickers: set[str]) -> list[str]:
        return [ticker for ticker in tickers if ticker.upper() not in excluded_tickers]

    def _load_watchlist_tickers(self, market_type: str, excluded_tickers: set[str]) -> list[str]:
        chat_id = str(getattr(self.settings, "telegram_allowed_chat_id", "") or "").strip()
        if not chat_id:
            return []
        repository = self.watchlist_repository
        if repository is None:
            try:
                repository = UserWatchlistRepository()
            except Exception:
                return []
        tickers = repository.list_tickers(chat_id, market_type=market_type)
        return self._filter_excluded([ticker.upper() for ticker in tickers], excluded_tickers)
