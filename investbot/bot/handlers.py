from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from investbot.config import get_settings
from investbot.db.repositories import DailyAnalysisRepository
from investbot.services.notification_service import NotificationService
from investbot.services.portfolio_service import PortfolioService
from investbot.services.summary_service import SummaryService
from investbot.services.user_settings_service import UserSettingsService


settings = get_settings()
user_settings_service = UserSettingsService()
portfolio_service = PortfolioService()
summary_service = SummaryService()
notification_service = NotificationService()


def _assert_authorized(chat_id: int) -> None:
    if str(chat_id) != settings.telegram_allowed_chat_id:
        raise PermissionError("Unauthorized chat id")


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _assert_authorized(update.effective_chat.id)
    await update.message.reply_text(
        "Smart Swing Agent is online. Commands: /summary /signals /settings /streak /paper_buy /paper_sell /portfolio"
    )


async def summary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _assert_authorized(update.effective_chat.id)
    market = context.args[0].lower() if context.args else "tw"
    if market not in {"tw", "us"}:
        await update.message.reply_text("Usage: /summary [tw|us]")
        return
    summary = summary_service.build_market_summary(market)
    await update.message.reply_text(notification_service.format_market_summary(summary))


async def signals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _assert_authorized(update.effective_chat.id)
    market = context.args[0].lower() if context.args else "tw"
    if market not in {"tw", "us"}:
        await update.message.reply_text("Usage: /signals [tw|us]")
        return

    rows = DailyAnalysisRepository().fetch_latest_market_rows(market)
    if not rows:
        await update.message.reply_text("No signals are available yet.")
        return

    chat_id = str(update.effective_chat.id)
    settings_row = user_settings_service.get_or_create(chat_id)
    filtered_rows = user_settings_service.filter_signals_for_user(settings_row, rows)
    await update.message.reply_text(notification_service.format_signal_digest(filtered_rows))


async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _assert_authorized(update.effective_chat.id)
    chat_id = str(update.effective_chat.id)
    updated = user_settings_service.toggle_large_cap_only(chat_id)
    await update.message.reply_text(
        f"large_cap_only={updated['large_cap_only']} | min_streak={updated['min_institutional_buy_streak']}"
    )


async def streak_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _assert_authorized(update.effective_chat.id)
    chat_id = str(update.effective_chat.id)
    updated = user_settings_service.cycle_min_institutional_buy_streak(chat_id)
    await update.message.reply_text(
        f"min_institutional_buy_streak set to {updated['min_institutional_buy_streak']}"
    )


async def paper_buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _assert_authorized(update.effective_chat.id)
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /paper_buy [ticker] [stop_loss_price]")
        return

    ticker = context.args[0].upper()
    try:
        stop_loss_price = float(context.args[1])
    except ValueError:
        await update.message.reply_text("stop_loss_price must be a number.")
        return

    try:
        trade = portfolio_service.create_paper_trade(ticker, stop_loss_price)
    except ValueError as exc:
        await update.message.reply_text(str(exc))
        return

    await update.message.reply_text(
        f"Paper trade created: {trade['ticker']} buy_price={trade['buy_price']} stop_loss={trade['stop_loss_price']}"
    )


async def paper_sell_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _assert_authorized(update.effective_chat.id)
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /paper_sell [ticker]")
        return

    ticker = context.args[0].upper()
    try:
        trade = portfolio_service.close_trade(ticker)
    except ValueError as exc:
        await update.message.reply_text(str(exc))
        return

    await update.message.reply_text(
        f"Trade closed: {ticker} sell_price={trade['sell_price']} pnl={trade['pnl_percent']}%"
    )


async def portfolio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _assert_authorized(update.effective_chat.id)
    positions, total_pnl = portfolio_service.get_open_positions_summary()
    if not positions:
        await update.message.reply_text("No open positions.")
        return

    lines = [f"Open portfolio PnL: {total_pnl:.2f}%"]
    for position in positions:
        lines.append(
            f"- {position['ticker']} | price {position['latest_price']} | stop buffer {position['stop_buffer_percent']}%"
        )
    await update.message.reply_text("\n".join(lines))
