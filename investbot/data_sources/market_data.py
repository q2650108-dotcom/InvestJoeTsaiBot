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

TW_FALLBACK_PROFILE = {
    "2330": {"name_zh": "台積電", "name_en": "TSMC", "sector": "半導體"},
    "2317": {"name_zh": "鴻海", "name_en": "Hon Hai", "sector": "電子代工"},
    "2454": {"name_zh": "聯發科", "name_en": "MediaTek", "sector": "IC設計"},
    "2308": {"name_zh": "台達電", "name_en": "Delta", "sector": "電源供應"},
    "2881": {"name_zh": "富邦金", "name_en": "Fubon Financial", "sector": "金融保險"},
    "2882": {"name_zh": "國泰金", "name_en": "Cathay Financial", "sector": "金融保險"},
    "1303": {"name_zh": "南亞", "name_en": "Nan Ya Plastics", "sector": "塑化"},
    "1301": {"name_zh": "台塑", "name_en": "Formosa Plastics", "sector": "塑化"},
    "2886": {"name_zh": "兆豐金", "name_en": "Mega Financial", "sector": "金融保險"},
    "2891": {"name_zh": "中信金", "name_en": "CTBC Financial", "sector": "金融保險"},
    "2382": {"name_zh": "廣達", "name_en": "Quanta", "sector": "電腦週邊"},
    "3711": {"name_zh": "日月光投控", "name_en": "ASEH", "sector": "半導體封測"},
    "2884": {"name_zh": "玉山金", "name_en": "E.SUN Financial", "sector": "金融保險"},
    "1216": {"name_zh": "統一", "name_en": "Uni-President", "sector": "食品"},
    "2002": {"name_zh": "中鋼", "name_en": "China Steel", "sector": "鋼鐵"},
    "2303": {"name_zh": "聯電", "name_en": "UMC", "sector": "半導體"},
    "5880": {"name_zh": "合庫金", "name_en": "Hua Nan Financial", "sector": "金融保險"},
    "2885": {"name_zh": "元大金", "name_en": "Yuanta Financial", "sector": "金融保險"},
    "2207": {"name_zh": "和泰車", "name_en": "Hotai Motor", "sector": "汽車"},
    "0050": {"name_zh": "元大台灣50", "name_en": "Yuanta Taiwan 50 ETF", "sector": "ETF"},
}

TW_INDUSTRY_CODE_MAP = {
    "01": "水泥",
    "02": "食品",
    "03": "塑膠",
    "04": "紡織纖維",
    "05": "電機機械",
    "06": "電器電纜",
    "08": "玻璃陶瓷",
    "09": "造紙",
    "10": "鋼鐵",
    "11": "橡膠",
    "12": "汽車",
    "14": "建材營造",
    "15": "航運",
    "16": "觀光餐旅",
    "17": "金融保險",
    "18": "貿易百貨",
    "20": "其他",
    "21": "化學",
    "22": "生技醫療",
    "23": "油電燃氣",
    "24": "半導體",
    "25": "電腦及週邊設備",
    "26": "光電",
    "27": "通信網路",
    "28": "電子零組件",
    "29": "電子通路",
    "30": "資訊服務",
    "31": "其他電子",
    "32": "文化創意",
    "33": "農業科技",
    "34": "電子商務",
    "35": "綠能環保",
    "36": "數位雲端",
    "37": "運動休閒",
    "38": "居家生活",
    "80": "管理股票",
}


class YahooMarketDataClient:
    def __init__(self, quote_router: QuoteProviderRouter | None = None) -> None:
        self.quote_router = quote_router or self._build_router()
        self._tw_profile_cache: dict[str, dict[str, str]] | None = None

    def get_price_history(self, ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        deadline = time.monotonic() + 20.0
        if ticker.startswith("^"):
            idx_frame = self._fetch_from_stooq_csv(ticker)
            if not idx_frame.empty:
                return idx_frame
        candidates = self._ticker_candidates(ticker)
        frame = pd.DataFrame()
        is_tw_ticker = ticker.upper().endswith(".TW")

        # Taiwan first: FinMind is the fastest reliable public history source;
        # TWSE monthly pages remain as official fallback.
        if is_tw_ticker:
            tw_deadline = time.monotonic() + 16.0
            frame = self._fetch_from_finmind_tw(ticker, period=period)
            if frame.empty and time.monotonic() <= tw_deadline:
                frame = self._fetch_from_twse_monthly(ticker, period=period, deadline=tw_deadline)
            if frame.empty and time.monotonic() <= tw_deadline:
                frame = self._fetch_from_fmp_history(ticker)
            if frame.empty and time.monotonic() <= tw_deadline:
                frame = self._fetch_from_yahoo_chart(ticker, period=period, interval=interval)
            if not frame.empty:
                frame = frame.reset_index()
                if "Date" not in frame.columns:
                    frame.rename(columns={"Datetime": "Date"}, inplace=True)
                required = {"Open", "High", "Low", "Close", "Volume", "Date"}
                missing = required - set(frame.columns)
                if not missing:
                    return frame

        for symbol in candidates:
            # Attempt 1: direct Yahoo chart endpoint. This is faster and quieter
            # than yfinance in hosted Streamlit environments.
            frame = self._fetch_from_yahoo_chart(symbol, period=period, interval=interval)

            # Attempt 2: FMP history, if configured.
            if frame.empty:
                frame = self._fetch_from_fmp_history(symbol)

            # Attempt 3: yfinance bulk downloader
            if frame.empty:
                import yfinance as yf

                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    frame = yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)

            # Attempt 4: single ticker history endpoint
            if frame.empty:
                import yfinance as yf

                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    history = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
                frame = history

            if not frame.empty:
                break
            if time.monotonic() > deadline:
                break

        # Attempt 4: TWSE official endpoint fallback for Taiwan listed stocks.
        if frame.empty and is_tw_ticker and time.monotonic() <= deadline:
            frame = self._fetch_from_twse_monthly(ticker, period=period, deadline=deadline)

        # Attempt 5: FinMind Taiwan stock price fallback.
        if frame.empty and is_tw_ticker and time.monotonic() <= deadline:
            frame = self._fetch_from_finmind_tw(ticker, period=period)

        # Attempt 6: FMP historical fallback (use configured key rotation).
        if frame.empty and time.monotonic() <= deadline:
            frame = self._fetch_from_fmp_history(ticker)

        # Attempt 7: Stooq CSV fallback. Stooq currently requires a per-user
        # CSV API key for many symbols, so this is intentionally last.
        if frame.empty and time.monotonic() <= deadline:
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
            response = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
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

    def _fetch_from_twse_monthly(self, ticker: str, period: str, deadline: float | None = None) -> pd.DataFrame:
        stock_no = ticker.upper().replace(".TW", "").strip()
        if not stock_no.isdigit():
            return pd.DataFrame()

        months = self._period_to_months(period)
        max_probe_months = max(months + 3, 36)
        today = self._get_twse_latest_trade_date() or date.today()
        rows: list[dict[str, object]] = []
        session = requests.Session()
        consecutive_empty = 0

        for offset in range(max_probe_months + 1):
            if deadline is not None and time.monotonic() > deadline:
                break
            month_date = self._month_back(today, offset)
            ym = month_date.strftime("%Y%m01")
            data = self._fetch_twse_stock_day_month(session=session, month_anchor=ym, stock_no=stock_no)
            if not data:
                consecutive_empty += 1
                # once we already collected enough rows for indicators, stop probing if repeated empty months appear
                if rows and consecutive_empty >= 3 and offset >= months:
                    break
                continue
            consecutive_empty = 0

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

            # enough records for MA60 + buffer
            if len(rows) >= 90 and offset >= months:
                break

        if not rows:
            return pd.DataFrame()

        frame = pd.DataFrame(rows).dropna(subset=["Date", "Open", "High", "Low", "Close", "Volume"])
        frame = frame.sort_values("Date").drop_duplicates(subset=["Date"], keep="last").reset_index(drop=True)
        return frame

    def _fetch_twse_stock_day_month(self, session: requests.Session, month_anchor: str, stock_no: str) -> list[list[object]]:
        endpoints = [
            "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY",
            "https://www.twse.com.tw/exchangeReport/STOCK_DAY",
        ]
        for endpoint in endpoints:
            url = f"{endpoint}?date={month_anchor}&stockNo={stock_no}&response=json"
            for attempt in range(2):
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
                        return data
                except Exception:
                    pass
                time.sleep(0.2 * (attempt + 1))
        return []

    def _get_twse_latest_trade_date(self) -> date | None:
        try:
            response = requests.get(
                "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
                timeout=8,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
            rows = response.json()
            if not isinstance(rows, list) or not rows:
                return None
            raw = str(rows[0].get("Date", "")).strip()
            if len(raw) != 7:
                return None
            return date(int(raw[:3]) + 1911, int(raw[3:5]), int(raw[5:7]))
        except Exception:
            return None

    def _fetch_from_stooq_csv(self, ticker: str) -> pd.DataFrame:
        symbol = ticker.lower()
        if "." not in symbol and symbol not in {"^vix", "^gspc", "^twii"}:
            symbol = f"{symbol}.us"
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

    def _fetch_from_finmind_tw(self, ticker: str, period: str) -> pd.DataFrame:
        stock_no = ticker.upper().replace(".TW", "").strip()
        if not stock_no.isdigit():
            return pd.DataFrame()

        end_date = self._get_twse_latest_trade_date() or date.today()
        start_date = end_date - timedelta(days=max(self._period_to_months(period) * 35, 240))
        params = {
            "dataset": "TaiwanStockPrice",
            "data_id": stock_no,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        token = self._get_finmind_token()
        if token:
            params["token"] = token

        try:
            response = requests.get(
                "https://api.finmindtrade.com/api/v4/data",
                params=params,
                timeout=12,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
            payload = response.json()
            rows = payload.get("data") or []
        except Exception:
            return pd.DataFrame()

        if not rows:
            return pd.DataFrame()

        frame = pd.DataFrame(rows)
        required = {"date", "open", "max", "min", "close", "Trading_Volume"}
        if not required.issubset(set(frame.columns)):
            return pd.DataFrame()
        frame = frame.rename(
            columns={
                "date": "Date",
                "open": "Open",
                "max": "High",
                "min": "Low",
                "close": "Close",
                "Trading_Volume": "Volume",
            }
        )
        frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
        frame = frame.dropna(subset=["Date", "Open", "High", "Low", "Close", "Volume"])
        return frame.sort_values("Date").reset_index(drop=True)

    def _fetch_from_fmp_history(self, ticker: str) -> pd.DataFrame:
        keys = self._split_api_keys(self._get_fmp_keys())
        if not keys:
            return pd.DataFrame()

        symbols = [ticker.upper().strip()]
        if ticker.upper().endswith(".TW"):
            symbols.append(ticker.upper().replace(".TW", ".TWO"))

        for symbol in symbols:
            for key in keys:
                url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{quote_plus(symbol)}?apikey={key}"
                try:
                    response = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
                    response.raise_for_status()
                    payload = response.json()
                    rows = payload.get("historical") or []
                except Exception:
                    continue

                if not rows:
                    continue

                frame = pd.DataFrame(rows)
                required = {"date", "open", "high", "low", "close", "volume"}
                if not required.issubset(set(frame.columns)):
                    continue
                frame = frame.rename(
                    columns={
                        "date": "Date",
                        "open": "Open",
                        "high": "High",
                        "low": "Low",
                        "close": "Close",
                        "volume": "Volume",
                    }
                )
                frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
                frame = frame.dropna(subset=["Date", "Open", "High", "Low", "Close", "Volume"])
                if frame.empty:
                    continue
                frame = frame.sort_values("Date").reset_index(drop=True)
                return frame
        return pd.DataFrame()

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

    def get_company_profile(self, ticker: str) -> dict[str, str]:
        normalized = ticker.upper().strip()
        market = "tw" if normalized.endswith(".TW") or normalized.endswith(".TWO") else "us"
        if market == "tw":
            return self._get_tw_company_profile(normalized)
        return self._get_us_company_profile(normalized)

    def diagnose_providers(self) -> list[dict[str, str]]:
        checks: list[tuple[str, str, str]] = [
            ("TWSE Company API", "https://openapi.twse.com.tw/v1/opendata/t187ap03_L", "twse_company"),
            ("TWSE Price API", "https://www.twse.com.tw/exchangeReport/STOCK_DAY?date=20240101&stockNo=2330&response=json", "twse_price"),
            ("FinMind TW Price API", "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id=2330&start_date=2026-01-01", "finmind_tw_price"),
            ("Stooq US CSV", "https://stooq.com/q/d/l/?s=aapl.us&i=d", "csv"),
            ("Stooq TW CSV", "https://stooq.com/q/d/l/?s=2330.tw&i=d", "csv"),
            ("Yahoo Chart", "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d&range=1mo", "yahoo_chart"),
        ]
        results: list[dict[str, str]] = []
        for name, url, expected_shape in checks:
            started = time.monotonic()
            status = "ok"
            note = ""
            try:
                response = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                code = response.status_code
                if code >= 400:
                    status = "fail"
                    note = f"HTTP {code}"
                elif not self._diagnostic_payload_has_data(response, expected_shape):
                    status = "fail"
                    note = "HTTP 200 but no parseable market data"
                else:
                    note = f"HTTP {code}, data ok"
            except Exception as exc:
                status = "fail"
                note = str(exc.__class__.__name__)
            elapsed = int((time.monotonic() - started) * 1000)
            results.append({"source": name, "status": status, "latency_ms": str(elapsed), "note": note})

        if self._get_fmp_keys().strip():
            started = time.monotonic()
            status = "ok"
            note = ""
            try:
                key = self._split_api_keys(self._get_fmp_keys())[0]
                url = f"https://financialmodelingprep.com/api/v3/quote/AAPL?apikey={key}"
                response = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()
                note = f"HTTP {response.status_code}"
            except Exception as exc:
                status = "fail"
                note = str(exc.__class__.__name__)
            elapsed = int((time.monotonic() - started) * 1000)
            results.append({"source": "FMP Quote API", "status": status, "latency_ms": str(elapsed), "note": note})

        return results

    def _diagnostic_payload_has_data(self, response: requests.Response, expected_shape: str) -> bool:
        try:
            if expected_shape == "csv":
                frame = pd.read_csv(io.StringIO(response.text.strip()))
                return {"Date", "Open", "High", "Low", "Close", "Volume"}.issubset(set(frame.columns)) and not frame.empty
            payload = response.json()
            if expected_shape == "twse_company":
                return isinstance(payload, list) and bool(payload) and "公司代號" in payload[0]
            if expected_shape == "twse_price":
                return isinstance(payload, dict) and bool(payload.get("data"))
            if expected_shape == "finmind_tw_price":
                return isinstance(payload, dict) and bool(payload.get("data"))
            if expected_shape == "yahoo_chart":
                result = (payload.get("chart") or {}).get("result") or []
                return bool(result and result[0].get("timestamp"))
        except Exception:
            return False
        return False

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

    def _get_tw_company_profile(self, ticker: str) -> dict[str, str]:
        symbol = ticker.replace(".TW", "").replace(".TWO", "")
        cache = self._load_tw_profile_cache()
        row = cache.get(symbol, {})
        if not row and symbol in TW_FALLBACK_PROFILE:
            row = TW_FALLBACK_PROFILE[symbol]
        return {
            "name_zh": row.get("name_zh", symbol),
            "name_en": row.get("name_en", symbol),
            "sector": row.get("sector", "未知"),
        }

    def _load_tw_profile_cache(self) -> dict[str, dict[str, str]]:
        if self._tw_profile_cache is not None:
            return self._tw_profile_cache

        endpoints = [
            "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
            "https://openapi.twse.com.tw/v1/opendata/t187ap03_O",
        ]
        cache: dict[str, dict[str, str]] = {}
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()
                rows = response.json()
            except Exception:
                continue
            if not isinstance(rows, list):
                continue
            for item in rows:
                symbol = str(item.get("公司代號") or item.get("SecuritiesCompanyCode") or "").strip()
                if not symbol:
                    continue
                name_zh = str(item.get("公司簡稱") or item.get("公司名稱") or item.get("CompanyName") or "").strip() or symbol
                name_en = str(item.get("英文簡稱") or item.get("CompanyAbbreviation") or "").strip() or name_zh
                industry_code = str(item.get("產業別") or item.get("Industry") or "").strip()
                sector = TW_INDUSTRY_CODE_MAP.get(industry_code, industry_code or "未知")
                cache[symbol] = {"name_zh": name_zh, "name_en": name_en, "sector": sector}

        self._tw_profile_cache = cache
        return self._tw_profile_cache

    def _get_us_company_profile(self, ticker: str) -> dict[str, str]:
        zh_hint = {
            "AAPL": "蘋果",
            "MSFT": "微軟",
            "NVDA": "輝達",
            "AMZN": "亞馬遜",
            "META": "Meta",
            "GOOGL": "Alphabet",
            "SPY": "標普500 ETF",
            "QQQ": "那斯達克100 ETF",
        }

        # Prefer FMP profile first.
        keys = self._split_api_keys(self._get_fmp_keys())
        for key in keys:
            url = f"https://financialmodelingprep.com/api/v3/profile/{quote_plus(ticker)}?apikey={key}"
            try:
                response = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()
                payload = response.json()
            except Exception:
                continue
            if isinstance(payload, list) and payload:
                item = payload[0]
                name_en = str(item.get("companyName") or ticker).strip() or ticker
                sector = str(item.get("sector") or "Unknown").strip() or "Unknown"
                return {"name_zh": zh_hint.get(ticker, ""), "name_en": name_en, "sector": sector}

        # Fallback to yfinance info.
        try:
            import yfinance as yf

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                info = yf.Ticker(ticker).info
            name_en = str(info.get("longName") or info.get("shortName") or ticker).strip() or ticker
            sector = str(info.get("sector") or "Unknown").strip() or "Unknown"
            return {"name_zh": zh_hint.get(ticker, ""), "name_en": name_en, "sector": sector}
        except Exception:
            return {"name_zh": zh_hint.get(ticker, ""), "name_en": ticker, "sector": "Unknown"}

    def _get_fmp_keys(self) -> str:
        try:
            from investbot.config import get_settings

            return get_settings().fmp_api_keys
        except Exception:
            return ""

    def _get_finmind_token(self) -> str:
        try:
            from investbot.config import get_settings

            return get_settings().finmind_api_token
        except Exception:
            return ""

    def _split_api_keys(self, raw: str) -> list[str]:
        return [item.strip() for item in str(raw).split(",") if item.strip()]
