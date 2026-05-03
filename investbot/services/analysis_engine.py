from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import logging

import pandas as pd

from investbot.data_sources.market_data import YahooMarketDataClient
from investbot.data_sources.twse import TwseClient
from investbot.db.repositories import DailyAnalysisRepository
from investbot.models import MarketSignal
from investbot.services.event_risk_service import EventRiskAssessment, EventRiskService


@dataclass(slots=True)
class AnalysisUniverse:
    market_type: str
    core_tickers: list[str]
    explore_tickers: list[str] | None = None

    def all_tickers(self) -> list[str]:
        merged: list[str] = []
        for ticker in self.core_tickers + (self.explore_tickers or []):
            normalized = ticker.upper()
            if normalized not in merged:
                merged.append(normalized)
        return merged

    def bucket_for(self, ticker: str) -> str:
        normalized = ticker.upper()
        if normalized in {item.upper() for item in (self.explore_tickers or [])}:
            return "explore"
        return "core"


@dataclass(slots=True)
class MarketContext:
    regime: str
    regime_score: float
    breadth_score: float
    benchmark_return_20d: float
    vix_value: float | None


class AnalysisEngine:
    INSTITUTIONAL_ACCUMULATION_SIGNAL = "Institutional Accumulation"
    PANIC_REVERSAL_SIGNAL = "Panic Reversal"
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        market_data: YahooMarketDataClient | None = None,
        twse_client: TwseClient | None = None,
        repository: DailyAnalysisRepository | None = None,
        event_risk_service: EventRiskService | None = None,
    ) -> None:
        self.market_data = market_data or YahooMarketDataClient()
        self.twse_client = twse_client or TwseClient()
        self.repository = repository or DailyAnalysisRepository()
        self.event_risk_service = event_risk_service or EventRiskService(market_data=self.market_data)

    def run(self, universe: AnalysisUniverse, target_date: date | None = None) -> list[MarketSignal]:
        trade_date = target_date or self.market_data.get_last_trading_date()
        large_caps = self.twse_client.get_large_cap_tickers()
        all_tickers = universe.all_tickers()
        net_buy_map = self.twse_client.get_institutional_net_buy_map(all_tickers)
        buy_history_map = self.twse_client.get_institutional_buy_history(all_tickers, lookback_days=5)
        enriched_frames: dict[str, pd.DataFrame] = {}

        for ticker in all_tickers:
            try:
                history = self.market_data.get_price_history(ticker)
                enriched = self._build_indicators(history)
            except Exception:
                self.logger.warning("Skip ticker with unavailable market data: %s", ticker, exc_info=True)
                continue
            if not enriched.empty:
                enriched_frames[ticker.upper()] = enriched

        market_context = self._build_market_context(universe.market_type, enriched_frames)

        signals: list[MarketSignal] = []
        for ticker in all_tickers:
            enriched = enriched_frames.get(ticker.upper())
            if enriched is None or enriched.empty:
                continue

            latest = enriched.iloc[-1]
            is_large_cap = ticker.upper() in large_caps or universe.market_type == "us"
            universe_bucket = universe.bucket_for(ticker)
            ticker_signals = self._evaluate_strategies(
                ticker=ticker,
                market_type=universe.market_type,
                latest=latest,
                trade_date=trade_date,
                institutional_net_buy=net_buy_map.get(ticker.upper(), 0),
                institutional_buy_history=buy_history_map.get(ticker.upper(), []),
                is_large_cap=is_large_cap,
                universe_bucket=universe_bucket,
                market_context=market_context,
            )
            signals.extend(ticker_signals)

        self.repository.upsert_many([signal.to_record() for signal in signals])
        return signals

    def _build_indicators(self, frame: pd.DataFrame) -> pd.DataFrame:
        frame = frame.copy()
        frame["20MA"] = frame["Close"].rolling(window=20).mean()
        frame["60MA"] = frame["Close"].rolling(window=60).mean()
        frame["5D_VOL_AVG"] = frame["Volume"].rolling(window=5).mean()
        frame["20D_RETURN"] = frame["Close"].pct_change(periods=20)
        frame["lower_shadow"] = frame[["Open", "Close"]].min(axis=1) - frame["Low"]
        frame["body_size"] = (frame["Close"] - frame["Open"]).abs()
        return frame.dropna().reset_index(drop=True)

    def _build_market_context(self, market_type: str, enriched_frames: dict[str, pd.DataFrame]) -> MarketContext:
        benchmark_ticker = "^TWII" if market_type == "tw" else "^GSPC"
        vix_value = self.market_data.get_vix_value()
        breadth_score = self._score_universe_breadth(enriched_frames)

        try:
            benchmark_history = self.market_data.get_price_history(benchmark_ticker)
            benchmark_enriched = self._build_indicators(benchmark_history)
            latest = benchmark_enriched.iloc[-1]
            benchmark_return_20d = float(latest["20D_RETURN"])
            regime_score = self._score_market_regime(
                close_price=float(latest["Close"]),
                ma_20=float(latest["20MA"]),
                ma_60=float(latest["60MA"]),
                vix_value=vix_value,
            )
            regime = self._label_market_regime(regime_score)
            return MarketContext(
                regime=regime,
                regime_score=regime_score,
                breadth_score=breadth_score,
                benchmark_return_20d=benchmark_return_20d,
                vix_value=vix_value,
            )
        except ValueError:
            return MarketContext(
                regime="Neutral",
                regime_score=50.0,
                breadth_score=breadth_score,
                benchmark_return_20d=0.0,
                vix_value=vix_value,
            )

    def _evaluate_strategies(
        self,
        ticker: str,
        market_type: str,
        latest: pd.Series,
        trade_date: date,
        institutional_net_buy: int,
        institutional_buy_history: list[int],
        is_large_cap: bool,
        universe_bucket: str,
        market_context: MarketContext,
    ) -> list[MarketSignal]:
        results: list[MarketSignal] = []

        close_price = float(latest["Close"])
        volume = int(latest["Volume"])
        ma_20 = float(latest["20MA"])
        ma_60 = float(latest["60MA"])

        buy_streak = self._get_institutional_buy_streak(institutional_buy_history)
        event_risk = self.event_risk_service.assess(ticker.upper(), trade_date)
        relative_strength_score = self._score_relative_strength(float(latest["20D_RETURN"]), market_context.benchmark_return_20d)
        institutional_conviction_score = self._score_institutional_conviction(buy_streak, institutional_net_buy)
        entry_quality_score = self._score_entry_quality(
            close_price=close_price,
            ma_20=ma_20,
            ma_60=ma_60,
            volume=volume,
            volume_avg_5d=float(latest["5D_VOL_AVG"]),
            is_large_cap=is_large_cap,
        )
        event_risk_score = event_risk.score
        composite_signal_score = self._score_composite_signal(
            market_regime_score=market_context.regime_score,
            breadth_score=market_context.breadth_score,
            relative_strength_score=relative_strength_score,
            institutional_conviction_score=institutional_conviction_score,
            event_risk_score=event_risk_score,
            entry_quality_score=entry_quality_score,
        )
        recommendation_bucket = self._classify_recommendation_bucket(
            composite_signal_score=composite_signal_score,
            buy_streak=buy_streak,
            market_regime=market_context.regime,
            breadth_score=market_context.breadth_score,
            universe_bucket=universe_bucket,
        )

        if market_type == "tw" and not is_large_cap:
            if universe_bucket != "explore":
                return results
            if not self._is_high_quality_explore_candidate(
                buy_streak=buy_streak,
                institutional_net_buy=institutional_net_buy,
                relative_strength_score=relative_strength_score,
                entry_quality_score=entry_quality_score,
                composite_signal_score=composite_signal_score,
            ):
                return results

        if self._is_institutional_accumulation(close_price, ma_20, buy_streak):
            results.append(
                MarketSignal(
                    trade_date=trade_date,
                    ticker=ticker.upper(),
                    market_type=market_type,
                    close_price=close_price,
                    volume=volume,
                    ma_20=ma_20,
                    ma_60=ma_60,
                    institutional_net_buy=institutional_net_buy,
                    signal_type=self.INSTITUTIONAL_ACCUMULATION_SIGNAL,
                    is_large_cap=is_large_cap,
                    universe_bucket=universe_bucket,
                    institutional_buy_streak=buy_streak,
                    entry_timing=self._classify_entry_timing(buy_streak),
                    market_regime=market_context.regime,
                    market_regime_score=market_context.regime_score,
                    breadth_score=market_context.breadth_score,
                    relative_strength_score=relative_strength_score,
                    institutional_conviction_score=institutional_conviction_score,
                    event_risk_score=event_risk_score,
                    next_event_date=event_risk.next_event_date.isoformat() if event_risk.next_event_date else None,
                    event_risk_note=event_risk.note,
                    entry_quality_score=entry_quality_score,
                    composite_signal_score=composite_signal_score,
                    recommendation_bucket=recommendation_bucket,
                )
            )

        if self._is_panic_reversal(latest):
            results.append(
                MarketSignal(
                    trade_date=trade_date,
                    ticker=ticker.upper(),
                    market_type=market_type,
                    close_price=close_price,
                    volume=volume,
                    ma_20=ma_20,
                    ma_60=ma_60,
                    institutional_net_buy=institutional_net_buy,
                    signal_type=self.PANIC_REVERSAL_SIGNAL,
                    is_large_cap=is_large_cap,
                    universe_bucket=universe_bucket,
                    market_regime=market_context.regime,
                    market_regime_score=market_context.regime_score,
                    breadth_score=market_context.breadth_score,
                    relative_strength_score=relative_strength_score,
                    institutional_conviction_score=institutional_conviction_score,
                    event_risk_score=event_risk_score,
                    next_event_date=event_risk.next_event_date.isoformat() if event_risk.next_event_date else None,
                    event_risk_note=event_risk.note,
                    entry_quality_score=entry_quality_score,
                    composite_signal_score=composite_signal_score,
                    recommendation_bucket=recommendation_bucket,
                )
            )
        return results

    def _get_institutional_buy_streak(self, institutional_buy_history: list[int]) -> int:
        streak = 0
        for net_buy in reversed(institutional_buy_history):
            if net_buy > 0:
                streak += 1
            else:
                break
        return streak

    def _is_institutional_accumulation(self, close_price: float, ma_20: float, buy_streak: int) -> bool:
        return buy_streak >= 1 and close_price > ma_20

    def _classify_entry_timing(self, buy_streak: int) -> str:
        if buy_streak <= 1:
            return "DAY_1_EARLY"
        if buy_streak == 2:
            return "DAY_2_BUILDING"
        return "DAY_3_PLUS_SAFER"

    def _score_market_regime(self, close_price: float, ma_20: float, ma_60: float, vix_value: float | None) -> float:
        score = 0.0
        if close_price > ma_20:
            score += 35
        if close_price > ma_60:
            score += 35
        if ma_20 > ma_60:
            score += 15

        if vix_value is None:
            score += 10
        elif vix_value < 18:
            score += 15
        elif vix_value < 25:
            score += 8
        return min(score, 100.0)

    def _label_market_regime(self, regime_score: float) -> str:
        if regime_score >= 70:
            return "Risk-On"
        if regime_score >= 45:
            return "Neutral"
        return "Risk-Off"

    def _score_relative_strength(self, stock_return_20d: float, benchmark_return_20d: float) -> float:
        delta = stock_return_20d - benchmark_return_20d
        score = 50 + (delta * 200)
        return round(max(0.0, min(score, 100.0)), 2)

    def _score_universe_breadth(self, enriched_frames: dict[str, pd.DataFrame]) -> float:
        if not enriched_frames:
            return 50.0

        metrics: list[float] = []
        for enriched in enriched_frames.values():
            latest = enriched.iloc[-1]
            above_20 = 1.0 if float(latest["Close"]) > float(latest["20MA"]) else 0.0
            above_60 = 1.0 if float(latest["Close"]) > float(latest["60MA"]) else 0.0
            positive_return = 1.0 if float(latest["20D_RETURN"]) > 0 else 0.0
            metrics.append(((above_20 * 0.4) + (above_60 * 0.4) + (positive_return * 0.2)) * 100)
        return round(sum(metrics) / len(metrics), 2)

    def _score_institutional_conviction(self, buy_streak: int, institutional_net_buy: int) -> float:
        streak_score = min(buy_streak * 25, 75)
        flow_bonus = 0
        if institutional_net_buy > 0:
            flow_bonus = 10 if institutional_net_buy < 1000 else 20
        return round(min(streak_score + flow_bonus, 100.0), 2)

    def _score_entry_quality(
        self,
        close_price: float,
        ma_20: float,
        ma_60: float,
        volume: int,
        volume_avg_5d: float,
        is_large_cap: bool,
    ) -> float:
        score = 0.0
        if close_price > ma_20:
            score += 30
        if close_price > ma_60:
            score += 20

        distance_to_ma20 = abs((close_price - ma_20) / ma_20) if ma_20 else 0.0
        if distance_to_ma20 <= 0.03:
            score += 25
        elif distance_to_ma20 <= 0.08:
            score += 15

        if volume_avg_5d > 0 and volume >= volume_avg_5d:
            score += 15
        if is_large_cap:
            score += 10
        return round(min(score, 100.0), 2)

    def _score_composite_signal(
        self,
        market_regime_score: float,
        breadth_score: float,
        relative_strength_score: float,
        institutional_conviction_score: float,
        event_risk_score: float,
        entry_quality_score: float,
    ) -> float:
        score = (
            (market_regime_score * 0.2)
            + (breadth_score * 0.15)
            + (relative_strength_score * 0.15)
            + (institutional_conviction_score * 0.25)
            + (event_risk_score * 0.1)
            + (entry_quality_score * 0.15)
        )
        return round(score, 2)

    def _classify_recommendation_bucket(
        self,
        composite_signal_score: float,
        buy_streak: int,
        market_regime: str,
        breadth_score: float,
        universe_bucket: str,
    ) -> str:
        if market_regime == "Risk-Off" or breadth_score < 40:
            return "Watchlist"
        if (
            composite_signal_score >= 80
            and buy_streak >= 3
            and market_regime == "Risk-On"
            and breadth_score >= 60
            and universe_bucket == "core"
        ):
            return "Safer Follow-Through"
        threshold = 72 if universe_bucket == "explore" else 68
        if composite_signal_score >= threshold:
            return "Actionable"
        return "Watchlist"

    def _is_high_quality_explore_candidate(
        self,
        buy_streak: int,
        institutional_net_buy: int,
        relative_strength_score: float,
        entry_quality_score: float,
        composite_signal_score: float,
    ) -> bool:
        return (
            buy_streak >= 2
            and institutional_net_buy > 0
            and relative_strength_score >= 60
            and entry_quality_score >= 55
            and composite_signal_score >= 72
        )

    def _is_panic_reversal(self, latest: pd.Series) -> bool:
        return (
            latest["Close"] < latest["60MA"]
            and latest["Volume"] >= latest["5D_VOL_AVG"] * 2
            and latest["lower_shadow"] > latest["body_size"]
        )
