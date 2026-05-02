from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from investbot.data_sources.economic_calendar import EconomicCalendarEvent, FmpEconomicCalendarClient
from investbot.data_sources.market_data import YahooMarketDataClient


@dataclass(slots=True)
class EventRiskAssessment:
    score: float
    next_event_date: date | None
    note: str


class EventRiskService:
    DEFAULT_COUNTRIES = {"US", "CN", "EU", "JP", "TW"}
    DEFAULT_IMPACTS = {"high", "3", "3-star", "three-star", "medium", "2", "2-star"}

    def __init__(
        self,
        market_data: YahooMarketDataClient | None = None,
        high_risk_event_dates: list[date] | str | None = None,
        calendar_client: FmpEconomicCalendarClient | None = None,
    ) -> None:
        self.market_data = market_data or YahooMarketDataClient()
        self.calendar_client = calendar_client or self._build_calendar_client()
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
        macro_events = self._load_upcoming_macro_events(trade_date)
        macro_dates = sorted({*self.high_risk_event_dates, *[event.event_date for event in macro_events]})
        macro_gap = self._nearest_future_gap(macro_dates, trade_date)
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
                notes.append(self._label_macro_note(macro_events, trade_date, imminent=True))
            elif macro_gap <= 3:
                score -= 10
                notes.append(self._label_macro_note(macro_events, trade_date, imminent=False))

        next_event_date = self._pick_next_event_date(next_earnings_date, macro_dates, trade_date)

        return EventRiskAssessment(
            score=max(0.0, min(score, 100.0)),
            next_event_date=next_event_date,
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

    def _build_calendar_client(self) -> FmpEconomicCalendarClient:
        try:
            from investbot.config import get_settings

            fmp_api_keys = get_settings().fmp_api_keys
        except ModuleNotFoundError:
            fmp_api_keys = ""
        return FmpEconomicCalendarClient(api_keys=fmp_api_keys)

    def _load_upcoming_macro_events(self, trade_date: date) -> list[EconomicCalendarEvent]:
        return self.calendar_client.get_upcoming_events(
            start_date=trade_date,
            days_ahead=7,
            countries=self.DEFAULT_COUNTRIES,
            impacts=self.DEFAULT_IMPACTS,
        )

    def _label_macro_note(
        self,
        macro_events: list[EconomicCalendarEvent],
        trade_date: date,
        imminent: bool,
    ) -> str:
        window = 1 if imminent else 3
        relevant = [event for event in macro_events if 0 <= (event.event_date - trade_date).days <= window]
        if not relevant:
            return "macro_event_imminent" if imminent else "macro_event_near"

        label = relevant[0].title.lower().replace(" ", "_")[:48]
        prefix = "macro_event_imminent" if imminent else "macro_event_near"
        return f"{prefix}:{label}"

    def _pick_next_event_date(
        self,
        next_earnings_date: date | None,
        macro_dates: list[date],
        trade_date: date,
    ) -> date | None:
        candidates: list[date] = []
        if next_earnings_date and next_earnings_date >= trade_date:
            candidates.append(next_earnings_date)
        candidates.extend([event_date for event_date in macro_dates if event_date >= trade_date])
        return min(candidates) if candidates else None

    def _parse_high_risk_event_dates(self, raw_value: str) -> list[date]:
        parsed_dates: list[date] = []
        for token in raw_value.split(","):
            token = token.strip()
            if not token:
                continue
            parsed_dates.append(date.fromisoformat(token))
        return parsed_dates
