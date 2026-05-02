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
        response = self.client.table("user_settings").upsert(payload).execute()
        return response.data[0]
