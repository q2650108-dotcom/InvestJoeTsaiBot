from __future__ import annotations

import asyncio
import logging
from datetime import date

from investbot.db.repositories import DailyAnalysisRepository
from investbot.services.analysis_engine import AnalysisEngine, AnalysisUniverse
from investbot.services.monitor_service import MonitorService
from investbot.services.notification_service import NotificationService
from investbot.services.summary_service import SummaryService
from investbot.services.user_settings_service import UserSettingsService
from investbot.config import get_settings


logger = logging.getLogger(__name__)


def run_tw_market_analysis(bot) -> list[dict[str, object]]:
    settings = get_settings()
    engine = AnalysisEngine()
    signals = engine.run(
        AnalysisUniverse(
            market_type="tw",
            tickers=_parse_tickers(settings.tw_core_tickers, ["2330.TW", "2317.TW", "2454.TW", "0050.TW"]),
        )
    )
    rows = [signal.to_record() for signal in signals]
    summary = SummaryService().build_market_summary("tw")
    _notify(bot, NotificationService().format_market_summary(summary))
    return rows


def run_us_market_analysis(bot) -> list[dict[str, object]]:
    settings = get_settings()
    engine = AnalysisEngine()
    signals = engine.run(
        AnalysisUniverse(
            market_type="us",
            tickers=_parse_tickers(settings.us_core_tickers, ["AAPL", "MSFT", "NVDA", "SPY"]),
        )
    )
    rows = [signal.to_record() for signal in signals]
    summary = SummaryService().build_market_summary("us")
    _notify(bot, NotificationService().format_market_summary(summary))
    return rows


def run_defense_monitor(bot) -> list[dict[str, object]]:
    settings = get_settings()
    if not settings.enable_defense_monitor:
        return []
    alerts = MonitorService().scan_stop_losses()
    if alerts:
        _notify(bot, NotificationService().format_stop_loss_alerts(alerts))
    return alerts


def get_today_signals() -> list[dict[str, object]]:
    return DailyAnalysisRepository().fetch_by_date(date.today())


def _notify(bot, message: str) -> None:
    try:
        asyncio.run(NotificationService().send_text(bot, message))
    except RuntimeError:
        logger.exception("Failed to send scheduler notification")


def _filter_rows_for_default_user(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    settings_service = UserSettingsService()
    settings_row = settings_service.get_or_create(settings_service.settings.telegram_allowed_chat_id)
    return settings_service.filter_signals_for_user(settings_row, rows)


def _parse_tickers(raw_value: str, fallback: list[str]) -> list[str]:
    values = [item.strip().upper() for item in raw_value.split(",") if item.strip()]
    return values or fallback
