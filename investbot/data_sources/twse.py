from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


class TwseClient:
    T86_URL = "https://www.twse.com.tw/rwd/zh/fund/T86"

    def __init__(self, large_cap_tickers: set[str] | None = None) -> None:
        self.large_cap_tickers = large_cap_tickers or self._load_large_cap_tickers()

    def get_institutional_net_buy_map(self, tickers: Iterable[str]) -> dict[str, int]:
        rows = self._fetch_latest_t86_rows()
        parsed_map = self._build_net_buy_map(rows)
        return {ticker.upper(): parsed_map.get(self._normalize_symbol(ticker), 0) for ticker in tickers}

    def get_institutional_buy_history(self, tickers: Iterable[str], lookback_days: int = 3) -> dict[str, list[int]]:
        symbols = [self._normalize_symbol(ticker) for ticker in tickers]
        history_map: dict[str, list[int]] = {symbol: [] for symbol in symbols}
        cursor = date.today()
        attempts = 0

        while attempts < lookback_days + 10 and any(len(values) < lookback_days for values in history_map.values()):
            rows = self._fetch_t86_rows(cursor)
            if rows:
                parsed_map = self._build_net_buy_map(rows)
                for symbol in symbols:
                    if len(history_map[symbol]) < lookback_days:
                        history_map[symbol].append(parsed_map.get(symbol, 0))
            cursor -= timedelta(days=1)
            attempts += 1

        return {
            f"{symbol}.TW": list(reversed(values[-lookback_days:]))
            for symbol, values in history_map.items()
        }

    def get_large_cap_tickers(self) -> set[str]:
        return self.large_cap_tickers

    def _fetch_latest_t86_rows(self) -> list[dict[str, object]]:
        cursor = date.today()
        for _ in range(7):
            rows = self._fetch_t86_rows(cursor)
            if rows:
                return rows
            cursor -= timedelta(days=1)
        return []

    def _fetch_t86_rows(self, target_date: date) -> list[dict[str, object]]:
        url = f"{self.T86_URL}?date={target_date.strftime('%Y%m%d')}&selectType=ALLBUT0999&response=json"
        try:
            with urlopen(url, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return []

        fields = payload.get("fields", [])
        data = payload.get("data", [])
        if not fields or not data:
            return []

        return [dict(zip(fields, row)) for row in data]

    def _build_net_buy_map(self, rows: list[dict[str, object]]) -> dict[str, int]:
        result: dict[str, int] = {}
        for row in rows:
            symbol = str(row.get("證券代號", "")).strip()
            if not symbol:
                continue

            foreign_net = self._extract_first_int(
                row,
                [
                    "外陸資買賣超股數(不含外資自營商)",
                    "外資及陸資買賣超股數(不含外資自營商)",
                ],
            )
            trust_net = self._extract_first_int(row, ["投信買賣超股數"])
            dealer_net = self._extract_first_int(
                row,
                [
                    "自營商買賣超股數",
                    "自營商買賣超股數(自行買賣)",
                ],
            )
            dealer_hedge_net = self._extract_first_int(row, ["自營商買賣超股數(避險)"])
            result[symbol] = foreign_net + trust_net + dealer_net + dealer_hedge_net
        return result

    def _extract_first_int(self, row: dict[str, object], keys: list[str]) -> int:
        for key in keys:
            if key in row:
                return self._parse_int(row[key])
        return 0

    def _parse_int(self, value: object) -> int:
        text = str(value).strip().replace(",", "")
        if not text or text == "--":
            return 0
        return int(float(text))

    def _normalize_symbol(self, ticker: str) -> str:
        return ticker.upper().replace(".TW", "")

    def _load_large_cap_tickers(self) -> set[str]:
        try:
            from investbot.config import get_settings

            raw_value = get_settings().tw_core_tickers
        except ModuleNotFoundError:
            raw_value = ""

        if raw_value.strip():
            return {item.strip().upper() for item in raw_value.split(",") if item.strip()}

        return {
            "2330.TW",
            "2317.TW",
            "2454.TW",
            "2308.TW",
            "2881.TW",
            "2882.TW",
            "1303.TW",
            "1301.TW",
            "2886.TW",
            "2891.TW",
            "2382.TW",
            "3711.TW",
            "2884.TW",
            "1216.TW",
            "2002.TW",
            "2303.TW",
            "5880.TW",
            "2885.TW",
            "2207.TW",
            "0050.TW",
        }
