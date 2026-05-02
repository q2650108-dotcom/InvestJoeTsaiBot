from __future__ import annotations

from datetime import date, timedelta

import pandas as pd


class YahooMarketDataClient:
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
        history = self.get_price_history(ticker, period="5d", interval="1d")
        return float(history["Close"].iloc[-1])

    def get_vix_value(self) -> float | None:
        try:
            return self.get_latest_price("^VIX")
        except ValueError:
            return None

    def get_last_trading_date(self) -> date:
        today = date.today()
        candidate = today - timedelta(days=1)
        while candidate.weekday() >= 5:
            candidate -= timedelta(days=1)
        return candidate
