from telegram.ext import Application, CommandHandler

from investbot.bot.handlers import (
    paper_buy_handler,
    paper_sell_handler,
    portfolio_handler,
    settings_handler,
    start_handler,
)
from investbot.config import get_settings


def build_telegram_app() -> Application:
    settings = get_settings()
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("settings", settings_handler))
    app.add_handler(CommandHandler("paper_buy", paper_buy_handler))
    app.add_handler(CommandHandler("paper_sell", paper_sell_handler))
    app.add_handler(CommandHandler("portfolio", portfolio_handler))
    return app
