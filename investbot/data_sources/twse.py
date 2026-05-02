from __future__ import annotations

from collections.abc import Iterable


class TwseClient:
    """
    Placeholder TWSE OpenAPI client.
    Replace this with requests/httpx integration to return
    institutional buy flows and large-cap constituents.
    """

    def get_institutional_net_buy_map(self, tickers: Iterable[str]) -> dict[str, int]:
        return {ticker.upper(): 0 for ticker in tickers}

    def get_institutional_buy_history(self, tickers: Iterable[str], lookback_days: int = 3) -> dict[str, list[int]]:
        return {ticker.upper(): [0] * lookback_days for ticker in tickers}

    def get_large_cap_tickers(self) -> set[str]:
        return {"2330.TW", "2317.TW", "2454.TW", "0050.TW"}
