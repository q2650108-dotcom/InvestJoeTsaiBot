from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, timedelta
import math
import time
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

        # Attempt 4: TWSE official endpoint fallback for Taiwan listed stocks.
        if frame.empty and ticker.upper().endswith(".TW"):
            frame = self._fetch_from_twse_monthly(ticker, period=period)

        # Attempt 5: Stooq CSV fallback
        if frame.empty:
            frame = self._fetch_from_stooq_csv(ticker)

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

    def _fetch_from_twse_monthly(self, ticker: str, period: str) -> pd.DataFrame:
        stock_no = ticker.upper().replace(".TW", "").strip()
        if not stock_no.isdigit():
            return pd.DataFrame()

        months = self._period_to_months(period)
        today = date.today()
        rows: list[dict[str, object]] = []
        session = requests.Session()

        for offset in range(months + 1):
            month_date = self._month_back(today, offset)
            ym = month_date.strftime("%Y%m01")
            url = (
                "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY"
                f"?date={ym}&stockNo={stock_no}&response=json"
            )
            data: list[list[object]] = []
            for attempt in range(3):
                try:
                    response = session.get(
                        url,
                        timeout=12,
                        headers={
                            "User-Agent": "Mozilla/5.0",
                            "Accept": "application/json,text/plain,*/*",
                            "Referer": "https://www.twse.com.tw/",
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                    data = payload.get("data") or []
                    if data:
                        break
                except Exception:
                    pass
                time.sleep(0.35 * (attempt + 1))

            for item in data:
                # [date, volume, amount, open, high, low, close, change, transactions]
                if len(item) < 9:
                    continue
                try:
                    row_date = self._parse_minguo_date(str(item[0]))
                    rows.append(
                        {
                            "Date": pd.to_datetime(row_date),
                            "Open": self._parse_tw_number(item[3]),
                            "High": self._parse_tw_number(item[4]),
                            "Low": self._parse_tw_number(item[5]),
                            "Close": self._parse_tw_number(item[6]),
                            "Volume": self._parse_tw_number(item[1]),
                        }
                    )
                except Exception:
                    continue

        if not rows:
            return pd.DataFrame()

        frame = pd.DataFrame(rows).dropna(subset=["Date", "Open", "High", "Low", "Close", "Volume"])
        frame = frame.sort_values("Date").drop_duplicates(subset=["Date"], keep="last").reset_index(drop=True)
        return frame

    def _fetch_from_stooq_csv(self, ticker: str) -> pd.DataFrame:
        symbol = ticker.lower()
        url = f"https://stooq.com/q/d/l/?s={quote_plus(symbol)}&i=d"
        try:
            response = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            text = response.text.strip()
        except Exception:
            return pd.DataFrame()

        if not text or text.lower().startswith("no data"):
            return pd.DataFrame()
        try:
            frame = pd.read_csv(io.StringIO(text))
        except Exception:
            return pd.DataFrame()

        required = {"Date", "Open", "High", "Low", "Close", "Volume"}
        if not required.issubset(set(frame.columns)):
            return pd.DataFrame()
        frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
        frame = frame.dropna(subset=["Date", "Open", "High", "Low", "Close", "Volume"])
        return frame.reset_index(drop=True)

    def _period_to_months(self, period: str) -> int:
        # Keep a long fallback window because hosted environments can have
        # date offsets and TWSE may return "no data" for future months.
        mapping = {"1d": 6, "5d": 6, "1mo": 12, "3mo": 18, "6mo": 24, "1y": 30, "2y": 36}
        return mapping.get(period, 24)

    def _month_back(self, source: date, offset: int) -> date:
        year = source.year
        month = source.month - offset
        while month <= 0:
            month += 12
            year -= 1
        return date(year, month, 1)

    def _parse_minguo_date(self, value: str) -> date:
        # 114/05/02 -> 2025-05-02
        parts = value.strip().split("/")
        if len(parts) != 3:
            raise ValueError("invalid minguo date")
        year = int(parts[0]) + 1911
        month = int(parts[1])
        day = int(parts[2])
        return date(year, month, day)

    def _parse_tw_number(self, value: object) -> float:
        text = str(value).replace(",", "").strip()
        if not text or text in {"--", "---", "X0.00"}:
            return math.nan
        return float(text)

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
