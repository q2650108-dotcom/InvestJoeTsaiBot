from investbot.bot.app import build_telegram_app
from investbot.scheduler.runner import build_scheduler


def main() -> None:
    telegram_app = build_telegram_app()
    scheduler = build_scheduler(telegram_app.bot)
    scheduler.start()
    telegram_app.run_polling()


if __name__ == "__main__":
    main()
