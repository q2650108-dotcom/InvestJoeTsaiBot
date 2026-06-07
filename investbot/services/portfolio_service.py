from __future__ import annotations

from datetime import date

from investbot.data_sources.market_data import YahooMarketDataClient
from investbot.db.repositories import PaperTradeRepository


class PortfolioService:
    def __init__(
        self,
        repository: PaperTradeRepository | None = None,
        market_data: YahooMarketDataClient | None = None,
    ) -> None:
        self.repository = repository or PaperTradeRepository()
        self.market_data = market_data or YahooMarketDataClient()

    def create_paper_trade(
        self,
        ticker: str,
        stop_loss_price: float,
        account_value: float | None = None,
        risk_tolerance_percent: float | None = None,
    ) -> dict[str, object]:
        latest_price = self.market_data.get_latest_price(ticker)
        existing_trade = self.repository.find_open_trade_by_ticker(ticker)
        if existing_trade is not None:
            raise ValueError(f"An OPEN trade already exists for {ticker.upper()}")
        if stop_loss_price >= latest_price:
            raise ValueError("stop_loss_price must be below the latest price for a defensive trade.")

        payload = {
            "ticker": ticker.upper(),
            "buy_date": date.today().isoformat(),
            "buy_price": latest_price,
            "stop_loss_price": stop_loss_price,
            "status": "OPEN",
        }
        sizing = self._calculate_position_sizing(
            latest_price=latest_price,
            stop_loss_price=stop_loss_price,
            account_value=account_value,
            risk_tolerance_percent=risk_tolerance_percent,
        )
        payload.update(sizing)
        return self.repository.create_trade(payload)

    def close_trade(self, ticker: str) -> dict[str, object]:
        trade = self.repository.find_open_trade_by_ticker(ticker)
        if trade is None:
            raise ValueError(f"No OPEN trade found for {ticker}")

        sell_price = self.market_data.get_latest_price(ticker)
        buy_price = float(trade["buy_price"])
        pnl_percent = ((sell_price - buy_price) / buy_price) * 100
        payload = {
            "status": "CLOSED",
            "sell_date": date.today().isoformat(),
            "sell_price": sell_price,
            "pnl_percent": round(pnl_percent, 2),
        }
        return self.repository.close_trade(trade["id"], payload)

    def get_open_positions_summary(self) -> tuple[list[dict[str, object]], float]:
        trades = self.repository.list_open_trades()
        total_pnl_percent_sum = 0.0
        total_position_value = 0.0
        total_live_pnl_value = 0.0
        enriched: list[dict[str, object]] = []
        for trade in trades:
            latest_price = self.market_data.get_latest_price(trade["ticker"])
            buy_price = float(trade["buy_price"])
            stop_loss_price = float(trade["stop_loss_price"])
            pnl_percent = ((latest_price - buy_price) / buy_price) * 100
            stop_buffer_percent = ((latest_price - stop_loss_price) / latest_price) * 100
            total_pnl_percent_sum += pnl_percent
            position_value = self._optional_float(trade.get("position_value"))
            if position_value is not None and position_value > 0:
                total_position_value += position_value
                total_live_pnl_value += position_value * (pnl_percent / 100)
            enriched.append(
                {
                    **trade,
                    "latest_price": round(latest_price, 2),
                    "live_pnl_percent": round(pnl_percent, 2),
                    "stop_buffer_percent": round(stop_buffer_percent, 2),
                }
            )
        if total_position_value > 0:
            return enriched, round((total_live_pnl_value / total_position_value) * 100, 2)
        return enriched, round(total_pnl_percent_sum, 2)

    def _calculate_position_sizing(
        self,
        latest_price: float,
        stop_loss_price: float,
        account_value: float | None,
        risk_tolerance_percent: float | None,
    ) -> dict[str, object]:
        if account_value is None or risk_tolerance_percent is None:
            return {}
        if account_value <= 0:
            raise ValueError("account_value must be positive.")
        if risk_tolerance_percent <= 0:
            raise ValueError("risk_tolerance_percent must be positive.")

        risk_per_share = latest_price - stop_loss_price
        risk_amount = account_value * (risk_tolerance_percent / 100)
        quantity = int(risk_amount // risk_per_share)
        if quantity <= 0:
            raise ValueError("risk budget is too small for one share at this stop distance.")
        return {
            "quantity": quantity,
            "account_value": round(account_value, 2),
            "risk_tolerance_percent": round(risk_tolerance_percent, 4),
            "risk_amount": round(quantity * risk_per_share, 2),
            "position_value": round(quantity * latest_price, 2),
        }

    def _optional_float(self, value: object) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
