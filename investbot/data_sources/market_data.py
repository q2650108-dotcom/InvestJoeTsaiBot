from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from investbot.data_sources.provider_router import ProviderError, QuoteProviderRouter


class YahooMarketDataClient:
    def __init__(self, quote_router: QuoteProviderRouter | None = None) -> None:
        self.quote_router = quote_router or self._build_router()

    def get_price_history(self, ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        import yfinance as yf

        frame = yf.download(ticker, period=period, interval=interval, auto_adjust=False, progress=False)
        if frame.empty:
            raise ValueError(f"No market data found for ticker={ticker}")
        frame = frame.reset_index()
        if "Date" not in frame.columns:
            frame.rename(columns={"Datetime": "Date"}, inplace=True)
        return frame

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
        except ValueError:
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
