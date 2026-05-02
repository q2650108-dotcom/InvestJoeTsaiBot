from __future__ import annotations


class NotificationService:
    def __init__(self) -> None:
        self.settings = None

    async def send_text(self, bot, text: str) -> None:
        if self.settings is None:
            from investbot.config import get_settings

            self.settings = get_settings()
        await bot.send_message(chat_id=self.settings.telegram_allowed_chat_id, text=text)

    def format_signal_digest(self, signals: list[dict[str, object]]) -> str:
        if not signals:
            return "No strategy signals were detected today."

        lines = ["Today's strategy candidates:"]
        for row in signals:
            lines.append(
                f"- {row['ticker']} | {row['signal_type']} | close {row['close_price']} | institutional {row['institutional_net_buy']}"
            )
        return "\n".join(lines)

    def format_stop_loss_alerts(self, alerts: list[dict[str, object]]) -> str:
        if not alerts:
            return "No stop-loss alerts."

        lines = ["Stop-loss alerts:"]
        for alert in alerts:
            lines.append(
                f"- {alert['ticker']} | price {alert['latest_price']} | stop {alert['stop_loss_price']}"
            )
        return "\n".join(lines)
