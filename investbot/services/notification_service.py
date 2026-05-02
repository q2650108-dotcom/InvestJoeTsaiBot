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
            streak_text = ""
            if row.get("institutional_buy_streak"):
                streak_text = f" | streak {row['institutional_buy_streak']} | {row.get('entry_timing', 'N/A')}"
            bucket_text = ""
            if row.get("recommendation_bucket"):
                bucket_text = f" | bucket {row['recommendation_bucket']}"
            score_text = ""
            if row.get("composite_signal_score") is not None:
                score_text = f" | score {row['composite_signal_score']}"
            lines.append(
                f"- {row['ticker']} | {row['signal_type']} | close {row['close_price']} | institutional {row['institutional_net_buy']}{streak_text}{bucket_text}{score_text}"
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
