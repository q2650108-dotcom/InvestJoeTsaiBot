from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from investbot.data_sources.market_data import YahooMarketDataClient
from investbot.data_sources.twse import TwseClient
from investbot.db.repositories import DailyAnalysisRepository
from investbot.models import MarketSignal


@dataclass(slots=True)
class AnalysisUniverse:
    market_type: str
    tickers: list[str]


class AnalysisEngine:
    INSTITUTIONAL_ACCUMULATION_SIGNAL = "外資連買"
    PANIC_REVERSAL_SIGNAL = "底部爆量"

    def __init__(
        self,
        market_data: YahooMarketDataClient | None = None,
        twse_client: TwseClient | None = None,
        repository: DailyAnalysisRepository | None = None,
    ) -> None:
        self.market_data = market_data or YahooMarketDataClient()
        self.twse_client = twse_client or TwseClient()
        self.repository = repository or DailyAnalysisRepository()

    def run(self, universe: AnalysisUniverse, target_date: date | None = None) -> list[MarketSignal]:
        trade_date = target_date or self.market_data.get_last_trading_date()
        large_caps = self.twse_client.get_large_cap_tickers()
        net_buy_map = self.twse_client.get_institutional_net_buy_map(universe.tickers)
        buy_history_map = self.twse_client.get_institutional_buy_history(universe.tickers, lookback_days=3)

        signals: list[MarketSignal] = []
        for ticker in universe.tickers:
            history = self.market_data.get_price_history(ticker)
            enriched = self._build_indicators(history)
            if enriched.empty:
                continue

            latest = enriched.iloc[-1]
            is_large_cap = ticker.upper() in large_caps or universe.market_type == "us"
            ticker_signals = self._evaluate_strategies(
                ticker=ticker,
                market_type=universe.market_type,
                frame=enriched,
                latest=latest,
                trade_date=trade_date,
                institutional_net_buy=net_buy_map.get(ticker.upper(), 0),
                institutional_buy_history=buy_history_map.get(ticker.upper(), []),
                is_large_cap=is_large_cap,
            )
            signals.extend(ticker_signals)

        self.repository.upsert_many([signal.to_record() for signal in signals])
        return signals

    def _build_indicators(self, frame: pd.DataFrame) -> pd.DataFrame:
        frame = frame.copy()
        frame["20MA"] = frame["Close"].rolling(window=20).mean()
        frame["60MA"] = frame["Close"].rolling(window=60).mean()
        frame["5D_VOL_AVG"] = frame["Volume"].rolling(window=5).mean()
        frame["lower_shadow"] = frame[["Open", "Close"]].min(axis=1) - frame["Low"]
        frame["body_size"] = (frame["Close"] - frame["Open"]).abs()
        return frame.dropna().reset_index(drop=True)

    def _evaluate_strategies(
        self,
        ticker: str,
        market_type: str,
        frame: pd.DataFrame,
        latest: pd.Series,
        trade_date: date,
        institutional_net_buy: int,
        institutional_buy_history: list[int],
        is_large_cap: bool,
    ) -> list[MarketSignal]:
        results: list[MarketSignal] = []
        if not is_large_cap and market_type == "tw":
            return results

        close_price = float(latest["Close"])
        volume = int(latest["Volume"])
        ma_20 = float(latest["20MA"])
        ma_60 = float(latest["60MA"])

        if self._is_institutional_accumulation(frame, institutional_buy_history):
            results.append(
                MarketSignal(
                    trade_date=trade_date,
                    ticker=ticker.upper(),
                    market_type=market_type,
                    close_price=close_price,
                    volume=volume,
                    ma_20=ma_20,
                    ma_60=ma_60,
                    institutional_net_buy=institutional_net_buy,
                    signal_type=self.INSTITUTIONAL_ACCUMULATION_SIGNAL,
                    is_large_cap=is_large_cap,
                )
            )

        if self._is_panic_reversal(latest):
            results.append(
                MarketSignal(
                    trade_date=trade_date,
                    ticker=ticker.upper(),
                    market_type=market_type,
                    close_price=close_price,
                    volume=volume,
                    ma_20=ma_20,
                    ma_60=ma_60,
                    institutional_net_buy=institutional_net_buy,
                    signal_type=self.PANIC_REVERSAL_SIGNAL,
                    is_large_cap=is_large_cap,
                )
            )
        return results

    def _is_institutional_accumulation(self, frame: pd.DataFrame, institutional_buy_history: list[int]) -> bool:
        latest = frame.iloc[-1]
        recent_history = institutional_buy_history[-3:]
        return (
            len(recent_history) == 3
            and all(net_buy > 0 for net_buy in recent_history)
            and latest["Close"] > latest["20MA"]
        )

    def _is_panic_reversal(self, latest: pd.Series) -> bool:
        return (
            latest["Close"] < latest["60MA"]
            and latest["Volume"] >= latest["5D_VOL_AVG"] * 2
            and latest["lower_shadow"] > latest["body_size"]
        )
