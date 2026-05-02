from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from investbot.config import get_settings
from investbot.db.repositories import UserSettingsRepository
from investbot.services.portfolio_service import PortfolioService


settings = get_settings()
user_settings_repo = UserSettingsRepository()
portfolio_service = PortfolioService()


def _assert_authorized(chat_id: int) -> None:
    if str(chat_id) != settings.telegram_allowed_chat_id:
        raise PermissionError("Unauthorized chat id")


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _assert_authorized(update.effective_chat.id)
    await update.message.reply_text(
        "Smart Swing Agent is online. Commands: /settings /paper_buy /paper_sell /portfolio"
    )


async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _assert_authorized(update.effective_chat.id)
    chat_id = str(update.effective_chat.id)
    current = user_settings_repo.get_settings(chat_id)
    large_cap_only = not (current or {}).get("large_cap_only", settings.default_large_cap_only)
    payload = {
        "telegram_chat_id": chat_id,
        "large_cap_only": large_cap_only,
        "risk_tolerance_percent": (current or {}).get(
            "risk_tolerance_percent",
            settings.default_risk_tolerance_percent,
        ),
    }
    user_settings_repo.upsert_settings(payload)
    await update.message.reply_text(f"large_cap_only toggled to {large_cap_only}")


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

    trade = portfolio_service.create_paper_trade(ticker, stop_loss_price)
    await update.message.reply_text(
        f"Paper trade created: {trade['ticker']} buy_price={trade['buy_price']} stop_loss={trade['stop_loss_price']}"
    )


async def paper_sell_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _assert_authorized(update.effective_chat.id)
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /paper_sell [ticker]")
        return

    ticker = context.args[0].upper()
    trade = portfolio_service.close_trade(ticker)
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
