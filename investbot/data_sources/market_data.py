from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, timedelta
from urllib.parse import quote_plus

import pandas as pd
import requests

from investbot.data_sources.provider_router import ProviderError, QuoteProviderRouter


class YahooMarketDataClient:
    def __init__(self, quote_router: QuoteProviderRouter | None = None) -> None:
        self.quote_router = quote_router or self._build_router()

    def get_price_history(self, ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        import yfinance as yf

        candidates = self._ticker_candidates(ticker)
        frame = pd.DataFrame()

        for symbol in candidates:
            # Attempt 1: yfinance bulk downloader
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                frame = yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)

            # Attempt 2: single ticker history endpoint
            if frame.empty:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    history = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
                frame = history

            # Attempt 3: direct Yahoo chart endpoint
            if frame.empty:
                frame = self._fetch_from_yahoo_chart(symbol, period=period, interval=interval)

            if not frame.empty:
                break

        if frame.empty:
            raise ValueError(f"No market data found for ticker={ticker}")

        frame = frame.reset_index()
        if "Date" not in frame.columns:
            frame.rename(columns={"Datetime": "Date"}, inplace=True)

        required = {"Open", "High", "Low", "Close", "Volume", "Date"}
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"Incomplete market data for ticker={ticker}, missing={sorted(missing)}")
        return frame

    def _ticker_candidates(self, ticker: str) -> list[str]:
        normalized = ticker.upper().strip()
        candidates = [normalized]
        if normalized.endswith(".TW"):
            candidates.append(normalized.replace(".TW", ".TWO"))
        elif normalized.endswith(".TWO"):
            candidates.append(normalized.replace(".TWO", ".TW"))
        return list(dict.fromkeys(candidates))

    def _fetch_from_yahoo_chart(self, ticker: str, period: str, interval: str) -> pd.DataFrame:
        range_map = {"1d": "5d", "5d": "1mo", "1mo": "6mo", "3mo": "1y", "6mo": "2y", "1y": "5y"}
        query_range = range_map.get(period, period)
        url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            f"{quote_plus(ticker)}?interval={interval}&range={query_range}&events=history&includePrePost=false"
        )
        try:
            response = requests.get(url, timeout=12)
            response.raise_for_status()
            payload = response.json()
            result = (payload.get("chart") or {}).get("result") or []
            if not result:
                return pd.DataFrame()
            block = result[0]
            timestamps = block.get("timestamp") or []
            quote = ((block.get("indicators") or {}).get("quote") or [{}])[0]
            frame = pd.DataFrame(
                {
                    "Date": pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(None),
                    "Open": quote.get("open", []),
                    "High": quote.get("high", []),
                    "Low": quote.get("low", []),
                    "Close": quote.get("close", []),
                    "Volume": quote.get("volume", []),
                }
            )
        except Exception:
            return pd.DataFrame()

        if frame.empty:
            return frame
        frame = frame.dropna(subset=["Date", "Open", "High", "Low", "Close", "Volume"])
        return frame.reset_index(drop=True)

    def get_latest_price(self, ticker: str) -> float:
        try:
            snapshot = self.quote_router.get_quote_snapshot(ticker)
            if snapshot.latest_price is not None:
                return snapshot.latest_price
        except ProviderError:
            pass

        history = self.get_price_history(ticker, period="5d", interval="1d")
        return float(history["Close"].iloc[-1])

    def get_vix_value(self) -> float | None:
        try:
            return self.get_latest_price("^VIX")
        except Exception:
            return None

    def get_next_earnings_date(self, ticker: str) -> date | None:
        try:
            snapshot = self.quote_router.get_quote_snapshot(ticker)
            if snapshot.next_earnings_date is not None:
                return snapshot.next_earnings_date
        except ProviderError:
            pass

        import yfinance as yf

        try:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                ticker_obj = yf.Ticker(ticker)
                calendar = ticker_obj.calendar
        except Exception:
            return None

        if calendar is None:
            return None

        if isinstance(calendar, pd.DataFrame) and not calendar.empty:
            values = calendar.to_numpy().flatten().tolist()
        elif isinstance(calendar, dict):
            values = list(calendar.values())
        else:
            values = [calendar]

        parsed_dates: list[date] = []
        for value in values:
            if value is None:
                continue
            try:
                timestamp = pd.to_datetime(value)
            except Exception:
                continue
            if pd.isna(timestamp):
                continue
            parsed_dates.append(timestamp.date())

        today = date.today()
        future_dates = sorted(event_date for event_date in parsed_dates if event_date >= today)
        return future_dates[0] if future_dates else None

    def get_last_trading_date(self) -> date:
        today = date.today()
        candidate = today - timedelta(days=1)
        while candidate.weekday() >= 5:
            candidate -= timedelta(days=1)
        return candidate

    def _build_router(self) -> QuoteProviderRouter:
        try:
            from investbot.config import get_settings

            settings = get_settings()
            finnhub_keys = settings.finnhub_api_keys or settings.finnhub_api_key
            fmp_keys = settings.fmp_api_keys
        except ModuleNotFoundError:
            finnhub_keys = ""
            fmp_keys = ""
        return QuoteProviderRouter(finnhub_keys=finnhub_keys, fmp_keys=fmp_keys)
