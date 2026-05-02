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
    institutional_buy_streak: int | None = None
    entry_timing: str | None = None
    market_regime: str | None = None
    market_regime_score: float | None = None
    breadth_score: float | None = None
    relative_strength_score: float | None = None
    institutional_conviction_score: float | None = None
    event_risk_score: float | None = None
    entry_quality_score: float | None = None
    composite_signal_score: float | None = None
    recommendation_bucket: str | None = None

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
            "institutional_buy_streak": self.institutional_buy_streak,
            "entry_timing": self.entry_timing,
            "market_regime": self.market_regime,
            "market_regime_score": self.market_regime_score,
            "breadth_score": self.breadth_score,
            "relative_strength_score": self.relative_strength_score,
            "institutional_conviction_score": self.institutional_conviction_score,
            "event_risk_score": self.event_risk_score,
            "entry_quality_score": self.entry_quality_score,
            "composite_signal_score": self.composite_signal_score,
            "recommendation_bucket": self.recommendation_bucket,
        }
