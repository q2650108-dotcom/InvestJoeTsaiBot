from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from itertools import cycle
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd


class ProviderError(Exception):
    pass


@dataclass(slots=True)
class QuoteSnapshot:
    latest_price: float | None = None
    next_earnings_date: date | None = None


class ApiKeyPool:
    def __init__(self, raw_keys: str) -> None:
        keys = [item.strip() for item in raw_keys.split(",") if item.strip()]
        self.keys = keys
        self._iterator = cycle(keys) if keys else None

    def all_keys(self) -> list[str]:
        return self.keys

    def next_key(self) -> str | None:
        if self._iterator is None:
            return None
        return next(self._iterator)


class FinnhubFallbackClient:
    def __init__(self, key_pool: ApiKeyPool) -> None:
        self.key_pool = key_pool

    def get_quote_snapshot(self, ticker: str) -> QuoteSnapshot:
        for api_key in self.key_pool.all_keys():
            try:
                quote = self._get_json(
                    "https://finnhub.io/api/v1/quote",
                    {"symbol": ticker, "token": api_key},
                )
                earnings = self._get_json(
                    "https://finnhub.io/api/v1/calendar/earnings",
                    {"symbol": ticker, "from": date.today().isoformat(), "to": date.today().replace(year=date.today().year + 1).isoformat(), "token": api_key},
                )
                earnings_date = None
                earnings_rows = earnings.get("earningsCalendar", []) if isinstance(earnings, dict) else []
                if earnings_rows:
                    earnings_date = pd.to_datetime(earnings_rows[0].get("date")).date()
                current_price = quote.get("c")
                if current_price:
                    return QuoteSnapshot(latest_price=float(current_price), next_earnings_date=earnings_date)
            except ProviderError:
                continue
        raise ProviderError("Finnhub keys exhausted or unavailable.")

    def _get_json(self, base_url: str, params: dict[str, str]) -> dict:
        url = f"{base_url}?{urlencode(params)}"
        try:
            with urlopen(url, timeout=10) as response:
                payload = response.read().decode("utf-8")
        except (HTTPError, URLError) as exc:
            raise ProviderError(str(exc)) from exc
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ProviderError("Invalid JSON payload") from exc
        if isinstance(data, dict) and data.get("error"):
            raise ProviderError(str(data["error"]))
        return data


class FmpFallbackClient:
    def __init__(self, key_pool: ApiKeyPool) -> None:
        self.key_pool = key_pool

    def get_quote_snapshot(self, ticker: str) -> QuoteSnapshot:
        for api_key in self.key_pool.all_keys():
            try:
                quote = self._get_json(
                    f"https://financialmodelingprep.com/api/v3/quote/{ticker}",
                    {"apikey": api_key},
                )
                earnings = self._get_json(
                    "https://financialmodelingprep.com/stable/earnings-calendar",
                    {"symbol": ticker, "apikey": api_key},
                )
                latest_price = None
                next_earnings_date = None
                if isinstance(quote, list) and quote:
                    latest_price = float(quote[0].get("price")) if quote[0].get("price") is not None else None
                if isinstance(earnings, list) and earnings:
                    next_earnings_date = pd.to_datetime(earnings[0].get("date")).date()
                if latest_price is not None:
                    return QuoteSnapshot(latest_price=latest_price, next_earnings_date=next_earnings_date)
            except ProviderError:
                continue
        raise ProviderError("FMP keys exhausted or unavailable.")

    def _get_json(self, base_url: str, params: dict[str, str]) -> list | dict:
        url = f"{base_url}?{urlencode(params)}"
        try:
            with urlopen(url, timeout=10) as response:
                payload = response.read().decode("utf-8")
        except (HTTPError, URLError) as exc:
            raise ProviderError(str(exc)) from exc
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ProviderError("Invalid JSON payload") from exc


class QuoteProviderRouter:
    def __init__(self, finnhub_keys: str = "", fmp_keys: str = "") -> None:
        self.providers: list[object] = []
        if finnhub_keys.strip():
            self.providers.append(FinnhubFallbackClient(ApiKeyPool(finnhub_keys)))
        if fmp_keys.strip():
            self.providers.append(FmpFallbackClient(ApiKeyPool(fmp_keys)))

    def get_quote_snapshot(self, ticker: str) -> QuoteSnapshot:
        last_error: Exception | None = None
        for provider in self.providers:
            try:
                return provider.get_quote_snapshot(ticker)
            except ProviderError as exc:
                last_error = exc
                continue
        raise ProviderError(str(last_error) if last_error else "No quote providers configured.")
