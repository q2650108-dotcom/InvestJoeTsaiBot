from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import logging
from typing import Callable

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


@dataclass(slots=True)
class AnalysisRunSummary:
    market_type: str
    scanned_tickers: int
    data_ready_tickers: int
    skipped_data_tickers: int
    no_signal_tickers: int
    signal_count: int
    skipped_reason_counts: dict[str, int] = field(default_factory=dict)
    no_signal_reason_counts: dict[str, int] = field(default_factory=dict)
    core_ticker_count: int = 0
    explore_ticker_count: int = 0
    stage_counts: dict[str, int] = field(default_factory=dict)
    stage_rows: list[dict[str, object]] = field(default_factory=list)
    signals: list[MarketSignal] = field(default_factory=list)


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
        return self.run_with_summary(universe, target_date=target_date).signals

    def run_with_summary(
        self,
        universe: AnalysisUniverse,
        target_date: date | None = None,
        progress_callback: Callable[[str, int, int, str], None] | None = None,
    ) -> AnalysisRunSummary:
        trade_date = target_date or self.market_data.get_last_trading_date()
        large_caps = self.twse_client.get_large_cap_tickers()
        all_tickers = universe.all_tickers()
        net_buy_map = self.twse_client.get_institutional_net_buy_map(all_tickers)
        buy_history_map = self.twse_client.get_institutional_buy_history(all_tickers, lookback_days=5)
        enriched_frames: dict[str, pd.DataFrame] = {}
        skipped_data_tickers = 0
        skipped_reason_counts: dict[str, int] = {}
        no_signal_reason_counts: dict[str, int] = {}
        no_signal_tickers = 0
        stage_rows: list[dict[str, object]] = []

        if progress_callback:
            progress_callback("init", 0, len(all_tickers), "準備分析宇宙" if universe.market_type == "tw" else "Preparing analysis universe")

        for index, ticker in enumerate(all_tickers, start=1):
            if progress_callback:
                progress_callback("fetch", index, len(all_tickers), f"抓取 {ticker}" if universe.market_type == "tw" else f"Fetching {ticker}")
            try:
                history = self.market_data.get_price_history(ticker)
                enriched = self._build_indicators(history)
            except Exception as exc:
                self.logger.warning("Skip ticker with unavailable market data: %s", ticker, exc_info=True)
                skipped_data_tickers += 1
                skipped_reason = self._classify_skip_reason(exc)
                skipped_reason_counts[skipped_reason] = skipped_reason_counts.get(skipped_reason, 0) + 1
                continue
            if not enriched.empty:
                enriched_frames[ticker.upper()] = enriched

        if progress_callback:
            progress_callback("context", len(enriched_frames), len(all_tickers), "建立市場環境" if universe.market_type == "tw" else "Building market context")
        market_context = self._build_market_context(universe.market_type, enriched_frames)

        signals: list[MarketSignal] = []
        for index, ticker in enumerate(all_tickers, start=1):
            if progress_callback:
                progress_callback("score", index, len(all_tickers), f"評分 {ticker}" if universe.market_type == "tw" else f"Scoring {ticker}")
            enriched = enriched_frames.get(ticker.upper())
            if enriched is None or enriched.empty:
                continue

            is_large_cap = ticker.upper() in large_caps or universe.market_type == "us"
            universe_bucket = universe.bucket_for(ticker)
            ticker_signals, stage_row, no_signal_reason = self._evaluate_strategies(
                ticker=ticker,
                market_type=universe.market_type,
                enriched=enriched,
                trade_date=trade_date,
                institutional_net_buy=net_buy_map.get(ticker.upper(), 0),
                institutional_buy_history=buy_history_map.get(ticker.upper(), []),
                is_large_cap=is_large_cap,
                universe_bucket=universe_bucket,
                market_context=market_context,
            )
            stage_rows.append(stage_row)
            if not ticker_signals:
                no_signal_tickers += 1
                reason_key = no_signal_reason or "no_strategy_trigger"
                no_signal_reason_counts[reason_key] = no_signal_reason_counts.get(reason_key, 0) + 1
            signals.extend(ticker_signals)

        self.repository.upsert_many([signal.to_record() for signal in signals])
        if progress_callback:
            progress_callback(
                "done",
                len(signals),
                len(all_tickers),
                "分析完成" if universe.market_type == "tw" else "Analysis complete",
            )
        return AnalysisRunSummary(
            market_type=universe.market_type,
            scanned_tickers=len(all_tickers),
            data_ready_tickers=len(enriched_frames),
            skipped_data_tickers=skipped_data_tickers,
            no_signal_tickers=no_signal_tickers,
            signal_count=len(signals),
            skipped_reason_counts=skipped_reason_counts,
            no_signal_reason_counts=no_signal_reason_counts,
            core_ticker_count=sum(1 for ticker in all_tickers if universe.bucket_for(ticker) == "core"),
            explore_ticker_count=sum(1 for ticker in all_tickers if universe.bucket_for(ticker) == "explore"),
            stage_counts=self._build_stage_counts(stage_rows),
            stage_rows=stage_rows,
            signals=signals,
        )

    def _classify_skip_reason(self, exc: Exception) -> str:
        message = str(exc).lower()
        if "incomplete market data" in message:
            return "incomplete_history"
        if "no market data found" in message:
            return "no_market_data"
        if "timeout" in message:
            return "request_timeout"
        return "provider_error"

    def _build_indicators(self, frame: pd.DataFrame) -> pd.DataFrame:
        frame = frame.copy()
        prev_close = frame["Close"].shift(1)
        true_range = pd.concat(
            [
                frame["High"] - frame["Low"],
                (frame["High"] - prev_close).abs(),
                (frame["Low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        frame["20MA"] = frame["Close"].rolling(window=20).mean()
        frame["60MA"] = frame["Close"].rolling(window=60).mean()
        frame["5D_VOL_AVG"] = frame["Volume"].rolling(window=5).mean()
        frame["20D_VOL_AVG"] = frame["Volume"].rolling(window=20).mean()
        frame["20D_RETURN"] = frame["Close"].pct_change(periods=20)
        frame["ATR20"] = true_range.rolling(window=20).mean()
        frame["lower_shadow"] = frame[["Open", "Close"]].min(axis=1) - frame["Low"]
        frame["body_size"] = (frame["Close"] - frame["Open"]).abs()
        return frame.dropna().reset_index(drop=True)

    def _build_stage_counts(self, stage_rows: list[dict[str, object]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in stage_rows:
            stage = str(row.get("stage", "")).strip()
            if not stage:
                continue
            counts[stage] = counts.get(stage, 0) + 1
        return counts

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
        except Exception:
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
        enriched: pd.DataFrame,
        trade_date: date,
        institutional_net_buy: int,
        institutional_buy_history: list[int],
        is_large_cap: bool,
        universe_bucket: str,
        market_context: MarketContext,
    ) -> tuple[list[MarketSignal], dict[str, object], str | None]:
        results: list[MarketSignal] = []
        latest = enriched.iloc[-1]
        prev = enriched.iloc[-2] if len(enriched) > 1 else latest

        close_price = float(latest["Close"])
        volume = int(latest["Volume"])
        ma_20 = float(latest["20MA"])
        ma_60 = float(latest["60MA"])
        atr_20 = float(latest.get("ATR20", 0) or 0)
        ma_60_prev = float(prev["60MA"])
        ma60_up = ma_60 > ma_60_prev
        recent_3d_net_buy = int(sum(institutional_buy_history[-3:])) if institutional_buy_history else 0
        growth_snapshot = self.market_data.get_growth_snapshot(ticker) if universe_bucket == "explore" else {
            "revenue_yoy": None,
            "eps_ttm": None,
            "as_of": None,
            "source": "",
        }
        revenue_yoy = growth_snapshot.get("revenue_yoy")
        eps_ttm = growth_snapshot.get("eps_ttm")

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
        market_regime_score = market_context.regime_score
        event_risk_score = event_risk.score
        panic_reversal = self._is_panic_reversal(latest)
        composite_signal_score = self._score_composite_signal(
            market_regime_score=market_regime_score,
            relative_strength_score=relative_strength_score,
            institutional_conviction_score=institutional_conviction_score,
            atr_risk_score=self._score_atr_risk(close_price=close_price, ma_20=ma_20, atr_20=atr_20),
            volume_quality_score=self._score_volume_quality(enriched),
        )
        buy_ratio = (institutional_net_buy / volume * 100) if volume > 0 else 0.0
        overextended = self._is_overextended(close_price=close_price, ma_20=ma_20, atr_20=atr_20)

        baseline_ok, baseline_reason = self._passes_baseline(
            universe_bucket=universe_bucket,
            close_price=close_price,
            ma_60=ma_60,
            ma60_up=ma60_up,
            revenue_yoy=revenue_yoy,
            eps_ttm=eps_ttm,
            panic_reversal=panic_reversal,
        )
        if not baseline_ok:
            return (
                results,
                self._build_stage_row(
                    ticker=ticker,
                    market_type=market_type,
                    universe_bucket=universe_bucket,
                    stage="baseline_reject",
                    reason=baseline_reason,
                    composite_signal_score=composite_signal_score,
                    relative_strength_score=relative_strength_score,
                    institutional_buy_streak=buy_streak,
                    growth_snapshot=growth_snapshot,
                ),
                baseline_reason,
            )

        trigger_labels = self._detect_triggers(
            latest=latest,
            enriched=enriched,
            recent_3d_net_buy=recent_3d_net_buy,
            close_price=close_price,
            ma_20=ma_20,
            ma_60=ma_60,
            volume=volume,
            panic_reversal=panic_reversal,
        )
        if not trigger_labels:
            no_signal_reason = self._classify_trigger_gap_reason(
                recent_3d_net_buy=recent_3d_net_buy,
                close_price=close_price,
                ma_20=ma_20,
                volume=volume,
                vol_avg_5d=float(latest["5D_VOL_AVG"]),
                universe_bucket=universe_bucket,
            )
            return (
                results,
                self._build_stage_row(
                    ticker=ticker,
                    market_type=market_type,
                    universe_bucket=universe_bucket,
                    stage="watch",
                    reason=no_signal_reason,
                    composite_signal_score=composite_signal_score,
                    relative_strength_score=relative_strength_score,
                    institutional_buy_streak=buy_streak,
                    growth_snapshot=growth_snapshot,
                ),
                no_signal_reason,
            )

        recommendation_bucket, stage_name, stage_reason = self._classify_recommendation_bucket(
            composite_signal_score=composite_signal_score,
            market_regime=market_context.regime,
            overextended=overextended,
            trigger_labels=trigger_labels,
            institutional_buy_ratio=buy_ratio,
            is_large_cap=is_large_cap,
        )
        stage_row = self._build_stage_row(
            ticker=ticker,
            market_type=market_type,
            universe_bucket=universe_bucket,
            stage=stage_name,
            reason=stage_reason,
            composite_signal_score=composite_signal_score,
            relative_strength_score=relative_strength_score,
            institutional_buy_streak=buy_streak,
            growth_snapshot=growth_snapshot,
            trigger_labels=trigger_labels,
        )
        if recommendation_bucket == "Watchlist":
            return results, stage_row, stage_reason

        signal_type = self.INSTITUTIONAL_ACCUMULATION_SIGNAL if "SMART_MONEY_TREND" in trigger_labels or "VCP_BREAKOUT" in trigger_labels else self.PANIC_REVERSAL_SIGNAL
        if signal_type == self.INSTITUTIONAL_ACCUMULATION_SIGNAL:
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
                    signal_type=signal_type,
                    is_large_cap=is_large_cap,
                    universe_bucket=universe_bucket,
                    institutional_buy_streak=buy_streak,
                    entry_timing=self._classify_entry_timing(buy_streak),
                    market_regime=market_context.regime,
                    market_regime_score=market_regime_score,
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
        else:
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
                    signal_type=signal_type,
                    is_large_cap=is_large_cap,
                    universe_bucket=universe_bucket,
                    market_regime=market_context.regime,
                    market_regime_score=market_regime_score,
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
        return results, stage_row, None

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
        relative_strength_score: float,
        institutional_conviction_score: float,
        atr_risk_score: float,
        volume_quality_score: float,
    ) -> float:
        score = (
            (market_regime_score * 0.2)
            + (relative_strength_score * 0.2)
            + (institutional_conviction_score * 0.3)
            + (atr_risk_score * 0.15)
            + (volume_quality_score * 0.15)
        )
        return round(score, 2)

    def _classify_recommendation_bucket(
        self,
        composite_signal_score: float,
        market_regime: str,
        overextended: bool,
        trigger_labels: list[str],
        institutional_buy_ratio: float,
        is_large_cap: bool,
    ) -> tuple[str, str, str]:
        if market_regime == "Risk-Off":
            return "Watchlist", "watch", "market_risk_off"
        if composite_signal_score >= 75 and not overextended and (is_large_cap or institutional_buy_ratio > 3):
            return "Actionable", "actionable", "ready_now"
        if composite_signal_score >= 75 and overextended:
            return "Candidate", "candidate", "wait_pullback_to_20ma"
        if "VCP_BREAKOUT" in trigger_labels and institutional_buy_ratio <= 0:
            return "Candidate", "candidate", "wait_for_institutional_confirmation"
        if 65 <= composite_signal_score < 75:
            return "Candidate", "candidate", "score_borderline_65_74"
        return "Watchlist", "watch", "triggered_but_low_score"

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
            and latest["Volume"] >= latest["20D_VOL_AVG"] * 2.5
            and latest["lower_shadow"] > latest["body_size"]
        )

    def _passes_baseline(
        self,
        universe_bucket: str,
        close_price: float,
        ma_60: float,
        ma60_up: bool,
        revenue_yoy: object,
        eps_ttm: object,
        panic_reversal: bool,
    ) -> tuple[bool, str]:
        if panic_reversal:
            return True, "panic_exception_baseline_ok"
        if universe_bucket == "core":
            if close_price <= ma_60:
                return False, "core_below_60ma"
            if not ma60_up:
                return False, "core_60ma_not_rising"
            return True, "core_trend_template_ok"

        revenue_positive = revenue_yoy is not None and float(revenue_yoy) > 0
        eps_positive = eps_ttm is not None and float(eps_ttm) > 0
        if close_price <= ma_60:
            return False, "explore_below_60ma"
        if not (revenue_positive or eps_positive):
            return False, "explore_growth_missing"
        return True, "explore_baseline_ok"

    def _detect_triggers(
        self,
        latest: pd.Series,
        enriched: pd.DataFrame,
        recent_3d_net_buy: int,
        close_price: float,
        ma_20: float,
        ma_60: float,
        volume: int,
        panic_reversal: bool,
    ) -> list[str]:
        triggers: list[str] = []
        if recent_3d_net_buy > 0 and close_price > ma_20 and volume >= float(latest["5D_VOL_AVG"]):
            triggers.append("SMART_MONEY_TREND")

        recent_slice = enriched.tail(4).iloc[:-1]
        recent_volumes = recent_slice["Volume"] if not recent_slice.empty else pd.Series(dtype=float)
        volume_contracted = bool(not recent_volumes.empty and (recent_volumes < float(latest["20D_VOL_AVG"]) * 0.5).all())
        near_20ma = abs((close_price - ma_20) / ma_20) <= 0.03 if ma_20 else False
        if near_20ma and volume_contracted and volume > float(latest["20D_VOL_AVG"]):
            triggers.append("VCP_BREAKOUT")

        if panic_reversal:
            triggers.append("PANIC_REVERSAL")
        return triggers

    def _score_atr_risk(self, close_price: float, ma_20: float, atr_20: float) -> float:
        if atr_20 <= 0:
            return 50.0
        extension = abs(close_price - ma_20) / atr_20
        if extension <= 1.5:
            return 90.0
        if extension <= 3.0:
            return 65.0
        if extension <= 4.0:
            return 40.0
        return 20.0

    def _score_volume_quality(self, enriched: pd.DataFrame, lookback: int = 10) -> float:
        frame = enriched.tail(lookback).copy()
        if frame.empty:
            return 50.0
        up_days = frame[frame["Close"] >= frame["Open"]]
        down_days = frame[frame["Close"] < frame["Open"]]
        up_avg = float(up_days["Volume"].mean()) if not up_days.empty else 0.0
        down_avg = float(down_days["Volume"].mean()) if not down_days.empty else 0.0
        if up_avg <= 0 and down_avg <= 0:
            return 50.0
        if down_avg <= 0:
            return 90.0
        ratio = up_avg / down_avg
        if ratio >= 1.4:
            return 90.0
        if ratio >= 1.1:
            return 72.0
        if ratio >= 0.9:
            return 55.0
        if ratio >= 0.75:
            return 40.0
        return 25.0

    def _classify_trigger_gap_reason(
        self,
        recent_3d_net_buy: int,
        close_price: float,
        ma_20: float,
        volume: int,
        vol_avg_5d: float,
        universe_bucket: str,
    ) -> str:
        if recent_3d_net_buy <= 0:
            return "no_institutional_buy_streak"
        if close_price <= ma_20:
            return "below_20ma"
        if vol_avg_5d > 0 and volume < vol_avg_5d:
            return "volume_below_5d_avg"
        if universe_bucket == "explore":
            return "explore_waiting_for_trigger"
        return "no_strategy_trigger"

    def _is_overextended(self, close_price: float, ma_20: float, atr_20: float) -> bool:
        if atr_20 <= 0:
            return False
        return close_price > ma_20 and ((close_price - ma_20) / atr_20) > 3.0

    def _build_stage_row(
        self,
        ticker: str,
        market_type: str,
        universe_bucket: str,
        stage: str,
        reason: str,
        composite_signal_score: float,
        relative_strength_score: float,
        institutional_buy_streak: int,
        growth_snapshot: dict[str, object],
        trigger_labels: list[str] | None = None,
    ) -> dict[str, object]:
        return {
            "ticker": ticker.upper(),
            "market_type": market_type,
            "universe_bucket": universe_bucket,
            "stage": stage,
            "reason": reason,
            "composite_signal_score": round(composite_signal_score, 2),
            "relative_strength_score": round(relative_strength_score, 2),
            "institutional_buy_streak": institutional_buy_streak,
            "revenue_yoy": growth_snapshot.get("revenue_yoy"),
            "eps_ttm": growth_snapshot.get("eps_ttm"),
            "fundamental_as_of": growth_snapshot.get("as_of"),
            "growth_source": growth_snapshot.get("source"),
            "triggers": trigger_labels or [],
        }
