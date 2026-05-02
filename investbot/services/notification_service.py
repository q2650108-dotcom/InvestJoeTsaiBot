from __future__ import annotations

from investbot.config import get_settings


class NotificationService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def send_text(self, bot, text: str) -> None:
        await bot.send_message(chat_id=self.settings.telegram_allowed_chat_id, text=text)

    def format_signal_digest(self, signals: list[dict[str, object]]) -> str:
        if not signals:
            return "今日沒有符合策略的標的。"

        lines = ["今日策略清單："]
        for row in signals:
            lines.append(
                f"- {row['ticker']} | {row['signal_type']} | 收盤 {row['close_price']} | 法人 {row['institutional_net_buy']}"
            )
        return "\n".join(lines)
