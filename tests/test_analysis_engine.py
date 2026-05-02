from __future__ import annotations

from datetime import date, timedelta
from unittest import TestCase

import pandas as pd

from investbot.services.analysis_engine import AnalysisEngine, AnalysisUniverse
from investbot.services.event_risk_service import EventRiskAssessment


class FakeMarketDataClient:
    def __init__(self, frames: dict[str, pd.DataFrame], vix_value: float = 16.0) -> None:
        self.frames = frames
        self.vix_value = vix_value

    def get_price_history(self, ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        return self.frames[ticker].copy()

    def get_last_trading_date(self) -> date:
        return date(2026, 5, 1)

    def get_vix_value(self) -> float:
        return self.vix_value

    def get_next_earnings_date(self, ticker: str) -> date | None:
        return None


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


class FakeEventRiskService:
    def __init__(self, assessment: EventRiskAssessment | None = None) -> None:
        self.assessment = assessment or EventRiskAssessment(score=70.0, next_event_date=None, note="clear")

    def assess(self, ticker: str, trade_date: date) -> EventRiskAssessment:
        return self.assessment


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


def build_engine(
    stock_history: pd.DataFrame,
    benchmark_history: pd.DataFrame | None = None,
    buy_map: dict[str, int] | None = None,
    buy_history_map: dict[str, list[int]] | None = None,
    vix_value: float = 16.0,
    event_risk_assessment: EventRiskAssessment | None = None,
) -> AnalysisEngine:
    if benchmark_history is None:
        benchmark_history = build_price_history(
            close_values=[200 + i for i in range(65)],
            volume_values=[5000] * 65,
        )
    frames = {
        "2330.TW": stock_history,
        "^TWII": benchmark_history,
    }
    return AnalysisEngine(
        market_data=FakeMarketDataClient(frames, vix_value=vix_value),
        twse_client=FakeTwseClient(
            large_caps={"2330.TW"},
            buy_map=buy_map or {"2330.TW": 300},
            buy_history_map=buy_history_map or {"2330.TW": [100, 120, 80]},
        ),
        repository=FakeDailyAnalysisRepository(),
        event_risk_service=FakeEventRiskService(event_risk_assessment),
    )


class AnalysisEngineTests(TestCase):
    def test_run_emits_day_1_institutional_accumulation_signal(self) -> None:
        history = build_price_history(close_values=[100 + i for i in range(65)], volume_values=[1000] * 65)
        engine = build_engine(
            stock_history=history,
            buy_map={"2330.TW": 300},
            buy_history_map={"2330.TW": [-50, 80]},
        )

        signals = engine.run(AnalysisUniverse(market_type="tw", core_tickers=["2330.TW"]))

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].signal_type, AnalysisEngine.INSTITUTIONAL_ACCUMULATION_SIGNAL)
        self.assertEqual(signals[0].institutional_buy_streak, 1)
        self.assertEqual(signals[0].entry_timing, "DAY_1_EARLY")

    def test_run_emits_day_2_institutional_accumulation_signal(self) -> None:
        history = build_price_history(close_values=[100 + i for i in range(65)], volume_values=[1000] * 65)
        engine = build_engine(
            stock_history=history,
            buy_map={"2330.TW": 50},
            buy_history_map={"2330.TW": [-10, 100, 80]},
        )

        signals = engine.run(AnalysisUniverse(market_type="tw", core_tickers=["2330.TW"]))

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].institutional_buy_streak, 2)
        self.assertEqual(signals[0].entry_timing, "DAY_2_BUILDING")

    def test_run_emits_day_3_plus_institutional_accumulation_signal(self) -> None:
        history = build_price_history(close_values=[100 + i for i in range(65)], volume_values=[1000] * 65)
        engine = build_engine(
            stock_history=history,
            buy_map={"2330.TW": 50},
            buy_history_map={"2330.TW": [-10, 40, 50, 60]},
        )

        signals = engine.run(AnalysisUniverse(market_type="tw", core_tickers=["2330.TW"]))

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].institutional_buy_streak, 3)
        self.assertEqual(signals[0].entry_timing, "DAY_3_PLUS_SAFER")

    def test_run_skips_institutional_accumulation_when_latest_day_is_not_a_net_buy(self) -> None:
        history = build_price_history(close_values=[100 + i for i in range(65)], volume_values=[1000] * 65)
        engine = build_engine(
            stock_history=history,
            buy_map={"2330.TW": -50},
            buy_history_map={"2330.TW": [100, 80, -10]},
        )

        signals = engine.run(AnalysisUniverse(market_type="tw", core_tickers=["2330.TW"]))

        self.assertEqual(signals, [])

    def test_run_emits_panic_reversal_signal_when_volume_spike_and_long_lower_shadow(self) -> None:
        close_values = [100] * 64 + [80]
        volume_values = [1000] * 64 + [3000]
        history = build_price_history(close_values=close_values, volume_values=volume_values, low_offset=10.0)
        history.loc[64, "Open"] = 82
        history.loc[64, "Close"] = 80
        history.loc[64, "Low"] = 65
        engine = build_engine(
            stock_history=history,
            buy_map={"2330.TW": 0},
            buy_history_map={"2330.TW": [0, 0, 0]},
        )

        signals = engine.run(AnalysisUniverse(market_type="tw", core_tickers=["2330.TW"]))

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].signal_type, AnalysisEngine.PANIC_REVERSAL_SIGNAL)

    def test_run_adds_market_and_relative_strength_scores(self) -> None:
        stock_history = build_price_history(close_values=[100 + (i * 2) for i in range(65)], volume_values=[1000] * 65)
        benchmark_history = build_price_history(close_values=[200 + i for i in range(65)], volume_values=[5000] * 65)
        engine = build_engine(
            stock_history=stock_history,
            benchmark_history=benchmark_history,
            buy_map={"2330.TW": 1500},
            buy_history_map={"2330.TW": [50, 100, 200]},
            vix_value=14.0,
        )

        signals = engine.run(AnalysisUniverse(market_type="tw", core_tickers=["2330.TW"]))
        signal = signals[0]

        self.assertEqual(signal.market_regime, "Risk-On")
        self.assertGreater(signal.market_regime_score or 0, 70)
        self.assertGreater(signal.breadth_score or 0, 60)
        self.assertGreater(signal.relative_strength_score or 0, 50)
        self.assertGreater(signal.institutional_conviction_score or 0, 70)
        self.assertGreater(signal.composite_signal_score or 0, 65)
        self.assertIn(signal.recommendation_bucket, {"Actionable", "Safer Follow-Through"})

    def test_run_penalizes_composite_score_when_event_risk_is_high(self) -> None:
        history = build_price_history(close_values=[100 + (i * 2) for i in range(65)], volume_values=[1000] * 65)
        engine = build_engine(
            stock_history=history,
            buy_map={"2330.TW": 1500},
            buy_history_map={"2330.TW": [50, 100, 200]},
            vix_value=14.0,
            event_risk_assessment=EventRiskAssessment(
                score=35.0,
                next_event_date=date(2026, 5, 3),
                note="earnings_imminent",
            ),
        )

        signals = engine.run(AnalysisUniverse(market_type="tw", core_tickers=["2330.TW"]))
        signal = signals[0]

        self.assertEqual(signal.event_risk_note, "earnings_imminent")
        self.assertEqual(signal.next_event_date, "2026-05-03")
        self.assertLess(signal.composite_signal_score or 100, 85)

    def test_run_downgrades_bucket_when_breadth_is_weak(self) -> None:
        strong_stock = build_price_history(close_values=[100 + (i * 2) for i in range(65)], volume_values=[1000] * 65)
        weak_stock = build_price_history(close_values=[200 - i for i in range(65)], volume_values=[5000] * 65)
        frames = {
            "2330.TW": strong_stock,
            "2317.TW": weak_stock,
            "2454.TW": weak_stock,
            "^TWII": weak_stock,
        }
        engine = AnalysisEngine(
            market_data=FakeMarketDataClient(frames, vix_value=28.0),
            twse_client=FakeTwseClient(
                large_caps={"2330.TW", "2317.TW", "2454.TW"},
                buy_map={"2330.TW": 1500},
                buy_history_map={"2330.TW": [50, 100, 200], "2317.TW": [0], "2454.TW": [0]},
            ),
            repository=FakeDailyAnalysisRepository(),
        )

        signals = engine.run(AnalysisUniverse(market_type="tw", core_tickers=["2330.TW", "2317.TW", "2454.TW"]))
        signal = next(item for item in signals if item.ticker == "2330.TW")

        self.assertLess(signal.breadth_score or 100, 40)
        self.assertEqual(signal.recommendation_bucket, "Watchlist")

    def test_run_allows_high_quality_explore_small_cap_candidate(self) -> None:
        history = build_price_history(close_values=[40 + i for i in range(65)], volume_values=[5000] * 65)
        benchmark_history = build_price_history(close_values=[200 + i for i in range(65)], volume_values=[5000] * 65)
        frames = {
            "3037.TW": history,
            "^TWII": benchmark_history,
        }
        engine = AnalysisEngine(
            market_data=FakeMarketDataClient(frames, vix_value=15.0),
            twse_client=FakeTwseClient(
                large_caps={"2330.TW"},
                buy_map={"3037.TW": 1200},
                buy_history_map={"3037.TW": [100, 120, 180]},
            ),
            repository=FakeDailyAnalysisRepository(),
        )

        signals = engine.run(
            AnalysisUniverse(
                market_type="tw",
                core_tickers=[],
                explore_tickers=["3037.TW"],
            )
        )

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].ticker, "3037.TW")
        self.assertEqual(signals[0].universe_bucket, "explore")

    def test_run_skips_low_quality_explore_small_cap_candidate(self) -> None:
        history = build_price_history(close_values=[40 + (i * 0.1) for i in range(65)], volume_values=[1000] * 65)
        benchmark_history = build_price_history(close_values=[200 + i for i in range(65)], volume_values=[5000] * 65)
        frames = {
            "3037.TW": history,
            "^TWII": benchmark_history,
        }
        engine = AnalysisEngine(
            market_data=FakeMarketDataClient(frames, vix_value=20.0),
            twse_client=FakeTwseClient(
                large_caps={"2330.TW"},
                buy_map={"3037.TW": 50},
                buy_history_map={"3037.TW": [-10, 30, 40]},
            ),
            repository=FakeDailyAnalysisRepository(),
        )

        signals = engine.run(
            AnalysisUniverse(
                market_type="tw",
                core_tickers=[],
                explore_tickers=["3037.TW"],
            )
        )

        self.assertEqual(signals, [])
