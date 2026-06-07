from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover - lightweight test/runtime fallback
    requests = None  # type: ignore[assignment]


@dataclass(slots=True)
class ForwardSignalSnapshot:
    score: float
    notes: list[str]


class ForwardSignalService:
    def __init__(self, fmp_api_keys: str = "") -> None:
        self.keys = [item.strip() for item in fmp_api_keys.split(",") if item.strip()]
        self.cache: dict[str, tuple[datetime, ForwardSignalSnapshot]] = {}
        self.ttl = timedelta(hours=6)

    def get_snapshot(self, ticker: str) -> ForwardSignalSnapshot:
        now = datetime.now(UTC)
        cached = self.cache.get(ticker.upper())
        if cached and cached[0] > now:
            return cached[1]

        snapshot = self._fetch_snapshot(ticker.upper())
        self.cache[ticker.upper()] = (now + self.ttl, snapshot)
        return snapshot

    def _fetch_snapshot(self, ticker: str) -> ForwardSignalSnapshot:
        if not self.keys or requests is None:
            return ForwardSignalSnapshot(score=50.0, notes=[])

        # Start neutral and blend incremental live signals.
        score = 50.0
        notes: list[str] = []
        key = self.keys[0]

        # 1) Analyst consensus proxy
        # Endpoint often available on free tier for core tickers.
        target = self._safe_get_json(
            f"https://financialmodelingprep.com/api/v4/price-target?symbol={ticker}&apikey={key}"
        )
        if isinstance(target, list) and target:
            first = target[0]
            target_price = self._to_float(first.get("priceTarget"))
            current_price = self._to_float(first.get("priceWhenPosted"))
            if target_price and current_price and current_price > 0:
                upside = (target_price - current_price) / current_price
                if upside >= 0.12:
                    score += 10
                    notes.append("Analyst target implies double-digit upside.")
                elif upside >= 0.05:
                    score += 5
                    notes.append("Analyst target still supports moderate upside.")
                elif upside < -0.05:
                    score -= 8
                    notes.append("Consensus target has turned defensive.")

        # 2) News intensity and polarity proxy
        news = self._safe_get_json(
            f"https://financialmodelingprep.com/api/v3/stock_news?tickers={ticker}&limit=10&apikey={key}"
        )
        if isinstance(news, list) and news:
            bullish_terms = ("beat", "upgrade", "guidance raise", "ai", "asic", "order", "deal", "launch")
            bearish_terms = ("downgrade", "miss", "probe", "delay", "cut", "lawsuit", "recall")
            signal = 0
            for item in news:
                title = str(item.get("title", "")).lower()
                if any(term in title for term in bullish_terms):
                    signal += 1
                if any(term in title for term in bearish_terms):
                    signal -= 1
            if signal >= 3:
                score += 8
                notes.append("Recent headlines skew positive for demand narrative.")
            elif signal >= 1:
                score += 4
                notes.append("News flow is mildly supportive.")
            elif signal <= -3:
                score -= 8
                notes.append("Headline risk is pressuring forward expectations.")

        return ForwardSignalSnapshot(score=max(0.0, min(100.0, round(score, 2))), notes=notes)

    def _safe_get_json(self, url: str) -> Any:
        try:
            response = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def _to_float(self, value: Any) -> float | None:
        try:
            return float(value)
        except Exception:
            return None
