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
        }
