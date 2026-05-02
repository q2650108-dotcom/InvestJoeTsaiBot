from __future__ import annotations

import asyncio
import logging
from datetime import date

from investbot.db.repositories import DailyAnalysisRepository
from investbot.services.analysis_engine import AnalysisEngine, AnalysisUniverse
from investbot.services.monitor_service import MonitorService
from investbot.services.notification_service import NotificationService


logger = logging.getLogger(__name__)


def run_tw_market_analysis(bot) -> list[dict[str, object]]:
    engine = AnalysisEngine()
    signals = engine.run(
        AnalysisUniverse(
            market_type="tw",
            tickers=["2330.TW", "2317.TW", "2454.TW", "0050.TW"],
        )
    )
    rows = [signal.to_record() for signal in signals]
    _notify(bot, NotificationService().format_signal_digest(rows))
    return rows


def run_us_market_analysis(bot) -> list[dict[str, object]]:
    engine = AnalysisEngine()
    signals = engine.run(
        AnalysisUniverse(
            market_type="us",
            tickers=["AAPL", "MSFT", "NVDA", "SPY"],
        )
    )
    rows = [signal.to_record() for signal in signals]
    _notify(bot, NotificationService().format_signal_digest(rows))
    return rows


def run_defense_monitor(bot) -> list[dict[str, object]]:
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
