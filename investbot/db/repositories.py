from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

from investbot.db.supabase_client import get_supabase

if TYPE_CHECKING:
    from supabase import Client
else:
    Client = Any


class DailyAnalysisRepository:
    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase()

    def upsert_many(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        self.client.table("daily_analysis").upsert(
            rows,
            on_conflict="date,ticker,signal_type",
        ).execute()

    def fetch_by_date(self, target_date: date) -> list[dict[str, Any]]:
        response = (
            self.client.table("daily_analysis")
            .select("*")
            .eq("date", target_date.isoformat())
            .order("ticker")
            .execute()
        )
        return response.data or []

    def fetch_history(self, ticker: str, limit: int = 30) -> list[dict[str, Any]]:
        response = (
            self.client.table("daily_analysis")
            .select("*")
            .eq("ticker", ticker.upper())
            .order("date", desc=True)
            .limit(limit)
            .execute()
        )
        return list(reversed(response.data or []))

    def fetch_recent_candidates(self, limit: int = 100) -> list[dict[str, Any]]:
        response = (
            self.client.table("daily_analysis")
            .select("*")
            .order("date", desc=True)
            .order("universe_bucket", desc=False)
            .order("composite_signal_score", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def fetch_latest_market_rows(self, market_type: str) -> list[dict[str, Any]]:
        latest_date_response = (
            self.client.table("daily_analysis")
            .select("date")
            .eq("type", market_type)
            .order("date", desc=True)
            .limit(1)
            .execute()
        )
        latest_date_rows = latest_date_response.data or []
        if not latest_date_rows:
            return []

        latest_date = latest_date_rows[0]["date"]
        response = (
            self.client.table("daily_analysis")
            .select("*")
            .eq("type", market_type)
            .eq("date", latest_date)
            .order("universe_bucket", desc=False)
            .order("composite_signal_score", desc=True)
            .execute()
        )
        return response.data or []

    def upsert_analysis_run(self, payload: dict[str, Any]) -> None:
        self.client.table("analysis_runs").upsert(
            payload,
            on_conflict="market_type,trade_date",
        ).execute()

    def fetch_latest_analysis_run(self, market_type: str) -> dict[str, Any] | None:
        response = (
            self.client.table("analysis_runs")
            .select("*")
            .eq("market_type", market_type)
            .order("trade_date", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None


class PaperTradeRepository:
    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase()

    def list_open_trades(self) -> list[dict[str, Any]]:
        response = (
            self.client.table("paper_trades")
            .select("*")
            .eq("status", "OPEN")
            .order("buy_date", desc=False)
            .execute()
        )
        return response.data or []

    def create_trade(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.client.table("paper_trades").insert(payload).execute()
        return response.data[0]

    def list_closed_trades(self, limit: int = 50) -> list[dict[str, Any]]:
        response = (
            self.client.table("paper_trades")
            .select("*")
            .eq("status", "CLOSED")
            .order("sell_date", desc=False)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def find_open_trade_by_ticker(self, ticker: str) -> dict[str, Any] | None:
        response = (
            self.client.table("paper_trades")
            .select("*")
            .eq("ticker", ticker.upper())
            .eq("status", "OPEN")
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def close_trade(self, trade_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = (
            self.client.table("paper_trades")
            .update(payload)
            .eq("id", trade_id)
            .execute()
        )
        return response.data[0]


class UserSettingsRepository:
    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase()

    def get_settings(self, chat_id: str) -> dict[str, Any] | None:
        response = (
            self.client.table("user_settings")
            .select("*")
            .eq("telegram_chat_id", chat_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def upsert_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.client.table("user_settings").upsert(
            payload,
            on_conflict="telegram_chat_id",
        ).execute()
        return response.data[0]


class UserWatchlistRepository:
    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase()

    def upsert_entry(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(payload)
        normalized["ticker"] = str(payload.get("ticker", "")).upper()
        response = self.client.table("user_watchlist").upsert(
            normalized,
            on_conflict="telegram_chat_id,ticker",
        ).execute()
        return response.data[0]

    def list_entries(self, chat_id: str) -> list[dict[str, Any]]:
        response = (
            self.client.table("user_watchlist")
            .select("*")
            .eq("telegram_chat_id", chat_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

    def list_tickers(self, chat_id: str, market_type: str | None = None) -> list[str]:
        entries = self.list_entries(chat_id)
        tickers = [str(row.get("ticker", "")).upper() for row in entries if row.get("ticker")]
        if market_type == "tw":
            return [ticker for ticker in tickers if ticker.endswith(".TW") or ticker.endswith(".TWO")]
        if market_type == "us":
            return [ticker for ticker in tickers if not ticker.endswith(".TW") and not ticker.endswith(".TWO")]
        return tickers


class GuruPortfolioRepository:
    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase()

    def upsert_portfolio(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.client.table("guru_portfolios").upsert(
            payload,
            on_conflict="guru_name,quarter",
        ).execute()
        return response.data[0]

    def fetch_latest_by_guru(self, guru_name: str) -> dict[str, Any] | None:
        response = (
            self.client.table("guru_portfolios")
            .select("*")
            .eq("guru_name", guru_name)
            .order("disclosed_at", desc=True)
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None


class AppCacheRepository:
    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase()

    def get_payload(self, cache_key: str) -> dict[str, Any] | None:
        response = (
            self.client.table("app_cache")
            .select("*")
            .eq("cache_key", cache_key)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def upsert_payload(self, cache_key: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.client.table("app_cache").upsert(
            {
                "cache_key": cache_key,
                "payload": payload,
            },
            on_conflict="cache_key",
        ).execute()
        return response.data[0]
