from __future__ import annotations

import asyncio

from investbot.db.repositories import DailyAnalysisRepository
from investbot.services.analysis_engine import AnalysisEngine, AnalysisUniverse
from investbot.services.monitor_service import MonitorService
from investbot.services.notification_service import NotificationService


def run_tw_market_analysis(bot) -> None:
    engine = AnalysisEngine()
    signals = engine.run(
        AnalysisUniverse(
            market_type="tw",
            tickers=["2330.TW", "2317.TW", "2454.TW", "0050.TW"],
        )
    )
    notifier = NotificationService()
    digest = notifier.format_signal_digest([signal.to_record() for signal in signals])
    asyncio.run(notifier.send_text(bot, digest))


def run_us_market_analysis(bot) -> None:
    engine = AnalysisEngine()
    signals = engine.run(
        AnalysisUniverse(
            market_type="us",
            tickers=["AAPL", "MSFT", "NVDA", "SPY"],
        )
    )
    notifier = NotificationService()
    digest = notifier.format_signal_digest([signal.to_record() for signal in signals])
    asyncio.run(notifier.send_text(bot, digest))


def run_defense_monitor(bot) -> None:
    notifier = NotificationService()
    alerts = MonitorService().scan_stop_losses()
    if not alerts:
        return

    lines = ["停損警報："]
    for alert in alerts:
        lines.append(
            f"- {alert['ticker']} 現價 {alert['latest_price']} 已跌破防守線 {alert['stop_loss_price']}"
        )
    asyncio.run(notifier.send_text(bot, "\n".join(lines)))


def get_today_signals() -> list[dict[str, object]]:
    from datetime import date

    return DailyAnalysisRepository().fetch_by_date(date.today())
