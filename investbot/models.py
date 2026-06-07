from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class MarketSignal:
    trade_date: date
    ticker: str
    market_type: str
    close_price: float
    volume: int
    ma_20: float
    ma_60: float
    institutional_net_buy: int
    signal_type: str
    is_large_cap: bool
    universe_bucket: str = "core"
    institutional_buy_streak: int | None = None
    entry_timing: str | None = None
    market_regime: str | None = None
    market_regime_score: float | None = None
    breadth_score: float | None = None
    relative_strength_score: float | None = None
    institutional_conviction_score: float | None = None
    event_risk_score: float | None = None
    next_event_date: str | None = None
    event_risk_note: str | None = None
    entry_quality_score: float | None = None
    composite_signal_score: float | None = None
    recommendation_bucket: str | None = None
    confluence_score: float | None = None
    confluence_classification: str | None = None
    strategy_scores: dict[str, int] | None = None
    confluence_reasons: list[str] | None = None
    stop_loss_price: float | None = None
    liquidity_score: float | None = None
    avg_dollar_volume_20d: float | None = None
    valuation_risk: str | None = None
    exposure_evidence: str | None = None
    research_priority: str | None = None

    def to_record(self) -> dict[str, object]:
        return {
            "date": self.trade_date.isoformat(),
            "ticker": self.ticker,
            "type": self.market_type,
            "close_price": self.close_price,
            "volume": self.volume,
            "ma_20": self.ma_20,
            "ma_60": self.ma_60,
            "institutional_net_buy": self.institutional_net_buy,
            "signal_type": self.signal_type,
            "is_large_cap": self.is_large_cap,
            "universe_bucket": self.universe_bucket,
            "institutional_buy_streak": self.institutional_buy_streak,
            "entry_timing": self.entry_timing,
            "market_regime": self.market_regime,
            "market_regime_score": self.market_regime_score,
            "breadth_score": self.breadth_score,
            "relative_strength_score": self.relative_strength_score,
            "institutional_conviction_score": self.institutional_conviction_score,
            "event_risk_score": self.event_risk_score,
            "next_event_date": self.next_event_date,
            "event_risk_note": self.event_risk_note,
            "entry_quality_score": self.entry_quality_score,
            "composite_signal_score": self.composite_signal_score,
            "recommendation_bucket": self.recommendation_bucket,
            "confluence_score": self.confluence_score,
            "confluence_classification": self.confluence_classification,
            "strategy_scores": self.strategy_scores,
            "confluence_reasons": self.confluence_reasons,
            "stop_loss_price": self.stop_loss_price,
            "liquidity_score": self.liquidity_score,
            "avg_dollar_volume_20d": self.avg_dollar_volume_20d,
            "valuation_risk": self.valuation_risk,
            "exposure_evidence": self.exposure_evidence,
            "research_priority": self.research_priority,
        }
