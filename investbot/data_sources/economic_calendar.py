from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover - local bundled runtime fallback
    requests = None  # type: ignore[assignment]


@dataclass(slots=True)
class EconomicCalendarEvent:
    event_date: date
    country: str
    title: str
    impact: str
    source: str = "fmp"


class FmpEconomicCalendarClient:
    BASE_URL = "https://financialmodelingprep.com/stable/economic-calendar"

    def __init__(self, api_keys: str = "", timeout_seconds: int = 12) -> None:
        self.api_keys = [key.strip() for key in api_keys.split(",") if key.strip()]
        self.timeout_seconds = timeout_seconds
        self._cache: dict[tuple[date, int], list[EconomicCalendarEvent]] = {}

    def get_upcoming_events(
        self,
        start_date: date | None = None,
        days_ahead: int = 7,
        countries: set[str] | None = None,
        impacts: set[str] | None = None,
    ) -> list[EconomicCalendarEvent]:
        start_date = start_date or date.today()
        cache_key = (start_date, days_ahead)
        if cache_key not in self._cache:
            self._cache[cache_key] = self._fetch_window(start_date, days_ahead)

        events = self._cache[cache_key]
        filtered = []
        for event in events:
            if countries and event.country.upper() not in countries:
                continue
            if impacts and event.impact.lower() not in impacts:
                continue
            filtered.append(event)
        return filtered

    def _fetch_window(self, start_date: date, days_ahead: int) -> list[EconomicCalendarEvent]:
        if not self.api_keys:
            return []
        if requests is None:
            return []

        end_date = start_date + timedelta(days=days_ahead)
        last_error: Exception | None = None

        for api_key in self.api_keys:
            try:
                response = requests.get(
                    self.BASE_URL,
                    params={
                        "from": start_date.isoformat(),
                        "to": end_date.isoformat(),
                        "apikey": api_key,
                    },
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                payload = response.json()
                return self._parse_events(payload)
            except Exception as exc:
                last_error = exc
                continue

        if last_error is not None:
            return []
        return []

    def _parse_events(self, payload: Any) -> list[EconomicCalendarEvent]:
        if not isinstance(payload, list):
            return []

        events: list[EconomicCalendarEvent] = []
        for item in payload:
            if not isinstance(item, dict):
                continue

            raw_date = item.get("date") or item.get("releaseDate") or item.get("datetime")
            parsed_date = self._parse_date(raw_date)
            if parsed_date is None:
                continue

            country = str(item.get("country") or item.get("countryCode") or "").strip().upper()
            title = str(item.get("event") or item.get("name") or item.get("title") or "").strip()
            impact = str(item.get("impact") or item.get("importance") or item.get("priority") or "").strip().lower()

            if not title:
                continue

            events.append(
                EconomicCalendarEvent(
                    event_date=parsed_date,
                    country=country,
                    title=title,
                    impact=impact or "unknown",
                )
            )
        return sorted(events, key=lambda event: (event.event_date, event.country, event.title))

    def _parse_date(self, raw_value: Any) -> date | None:
        if raw_value is None:
            return None
        text = str(raw_value).strip()
        if not text:
            return None
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None
