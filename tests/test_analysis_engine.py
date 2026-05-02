from __future__ import annotations

from datetime import date, timedelta
from unittest import TestCase

import pandas as pd

from investbot.services.analysis_engine import AnalysisEngine, AnalysisUniverse


class FakeMarketDataClient:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame

    def get_price_history(self, ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        return self.frame.copy()

    def get_last_trading_date(self) -> date:
        return date(2026, 5, 1)


class FakeTwseClient:
    def __init__(self, large_caps: set[str], buy_map: dict[str, int], buy_history_map: dict[str, list[int]]) -> None:
        self.large_caps = large_caps
        self.buy_map = buy_map
        self.buy_history_map = buy_history_map

    def get_large_cap_tickers(self) -> set[str]:
        return self.large_caps

    def get_institutional_net_buy_map(self, tickers: list[str]) -> dict[str, int]:
        return {ticker.upper(): self.buy_map.get(ticker.upper(), 0) for ticker in tickers}

    def get_institutional_buy_history(self, tickers: list[str], lookback_days: int = 3) -> dict[str, list[int]]:
        return {ticker.upper(): self.buy_history_map.get(ticker.upper(), [0] * lookback_days) for ticker in tickers}


class FakeDailyAnalysisRepository:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []

    def upsert_many(self, rows: list[dict[str, object]]) -> None:
        self.rows.extend(rows)


def build_price_history(close_values: list[float], volume_values: list[int], low_offset: float = 3.0) -> pd.DataFrame:
    base_date = date(2026, 1, 1)
    rows = []
    for index, (close_price, volume) in enumerate(zip(close_values, volume_values)):
        rows.append(
            {
                "Date": pd.Timestamp(base_date + timedelta(days=index)),
                "Open": close_price - 1,
                "High": close_price + 2,
                "Low": close_price - low_offset,
                "Close": close_price,
                "Volume": volume,
            }
        )
    return pd.DataFrame(rows)


class AnalysisEngineTests(TestCase):
    def test_run_emits_institutional_accumulation_signal_for_three_day_buying(self) -> None:
        history = build_price_history(
            close_values=[100 + i for i in range(65)],
            volume_values=[1000] * 65,
        )
        repository = FakeDailyAnalysisRepository()
        engine = AnalysisEngine(
            market_data=FakeMarketDataClient(history),
            twse_client=FakeTwseClient(
                large_caps={"2330.TW"},
                buy_map={"2330.TW": 300},
                buy_history_map={"2330.TW": [100, 120, 80]},
            ),
            repository=repository,
        )

        signals = engine.run(AnalysisUniverse(market_type="tw", tickers=["2330.TW"]))

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].signal_type, AnalysisEngine.INSTITUTIONAL_ACCUMULATION_SIGNAL)
        self.assertEqual(len(repository.rows), 1)

    def test_run_skips_institutional_accumulation_when_buying_is_not_consecutive(self) -> None:
        history = build_price_history(
            close_values=[100 + i for i in range(65)],
            volume_values=[1000] * 65,
        )
        engine = AnalysisEngine(
            market_data=FakeMarketDataClient(history),
            twse_client=FakeTwseClient(
                large_caps={"2330.TW"},
                buy_map={"2330.TW": 50},
                buy_history_map={"2330.TW": [100, -10, 80]},
            ),
            repository=FakeDailyAnalysisRepository(),
        )

        signals = engine.run(AnalysisUniverse(market_type="tw", tickers=["2330.TW"]))

        self.assertEqual(signals, [])

    def test_run_emits_panic_reversal_signal_when_volume_spike_and_long_lower_shadow(self) -> None:
        close_values = [100] * 64 + [80]
        volume_values = [1000] * 64 + [3000]
        history = build_price_history(close_values=close_values, volume_values=volume_values, low_offset=10.0)
        history.loc[64, "Open"] = 82
        history.loc[64, "Close"] = 80
        history.loc[64, "Low"] = 65

        engine = AnalysisEngine(
            market_data=FakeMarketDataClient(history),
            twse_client=FakeTwseClient(
                large_caps={"2330.TW"},
                buy_map={"2330.TW": 0},
                buy_history_map={"2330.TW": [0, 0, 0]},
            ),
            repository=FakeDailyAnalysisRepository(),
        )

        signals = engine.run(AnalysisUniverse(market_type="tw", tickers=["2330.TW"]))

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].signal_type, AnalysisEngine.PANIC_REVERSAL_SIGNAL)
