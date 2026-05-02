from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from investbot.data_sources.market_data import YahooMarketDataClient


@dataclass(slots=True)
class EventRiskAssessment:
    score: float
    next_event_date: date | None
    note: str


class EventRiskService:
    def __init__(
        self,
        market_data: YahooMarketDataClient | None = None,
        high_risk_event_dates: list[date] | str | None = None,
    ) -> None:
        self.market_data = market_data or YahooMarketDataClient()
        if isinstance(high_risk_event_dates, str):
            self.high_risk_event_dates = self._parse_high_risk_event_dates(high_risk_event_dates)
        elif high_risk_event_dates is not None:
            self.high_risk_event_dates = high_risk_event_dates
        else:
            self.high_risk_event_dates = self._load_high_risk_event_dates()

    def assess(self, ticker: str, trade_date: date) -> EventRiskAssessment:
        if hasattr(self.market_data, "get_next_earnings_date"):
            next_earnings_date = self.market_data.get_next_earnings_date(ticker)
        else:
            next_earnings_date = None
        macro_gap = self._nearest_future_gap(self.high_risk_event_dates, trade_date)
        earnings_gap = (next_earnings_date - trade_date).days if next_earnings_date else None

        score = 70.0
        notes: list[str] = []

        if earnings_gap is not None:
            if earnings_gap <= 3:
                score -= 35
                notes.append("earnings_imminent")
            elif earnings_gap <= 7:
                score -= 20
                notes.append("earnings_near")

        if macro_gap is not None:
            if macro_gap <= 1:
                score -= 20
                notes.append("macro_event_imminent")
            elif macro_gap <= 3:
                score -= 10
                notes.append("macro_event_near")

        return EventRiskAssessment(
            score=max(0.0, min(score, 100.0)),
            next_event_date=next_earnings_date,
            note=",".join(notes) if notes else "clear",
        )

    def _nearest_future_gap(self, event_dates: list[date], trade_date: date) -> int | None:
        future_dates = [event_date for event_date in event_dates if event_date >= trade_date]
        if not future_dates:
            return None
        return min((event_date - trade_date).days for event_date in future_dates)

    def _load_high_risk_event_dates(self) -> list[date]:
        try:
            from investbot.config import get_settings

            raw_value = get_settings().high_risk_event_dates
        except ModuleNotFoundError:
            raw_value = ""

        return self._parse_high_risk_event_dates(raw_value)

    def _parse_high_risk_event_dates(self, raw_value: str) -> list[date]:
        parsed_dates: list[date] = []
        for token in raw_value.split(","):
            token = token.strip()
            if not token:
                continue
            parsed_dates.append(date.fromisoformat(token))
        return parsed_dates
