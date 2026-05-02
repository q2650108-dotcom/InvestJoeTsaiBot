from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from investbot.config import get_settings
from investbot.scheduler.jobs import run_defense_monitor, run_tw_market_analysis, run_us_market_analysis


def build_scheduler(bot) -> BackgroundScheduler:
    settings = get_settings()
    scheduler = BackgroundScheduler(timezone=ZoneInfo(settings.app_timezone))
    scheduler.add_job(
        run_tw_market_analysis,
        "cron",
        hour=settings.tw_market_analysis_hour,
        minute=0,
        args=[bot],
        id="tw_market_analysis",
        replace_existing=True,
    )
    scheduler.add_job(
        run_us_market_analysis,
        "cron",
        hour=settings.us_market_analysis_hour,
        minute=0,
        args=[bot],
        id="us_market_analysis",
        replace_existing=True,
    )
    scheduler.add_job(
        run_defense_monitor,
        "interval",
        minutes=settings.defense_check_interval_minutes,
        args=[bot],
        id="defense_monitor",
        replace_existing=True,
    )
    return scheduler
