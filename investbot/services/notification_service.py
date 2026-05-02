from __future__ import annotations

from investbot.services.summary_service import MarketSummary


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

    def format_market_summary(self, summary: MarketSummary | None) -> str:
        if summary is None:
            return "No summary data is available yet."

        lines = [
            f"{summary.market_type.upper()} summary | {summary.summary_date}",
            f"Regime: {summary.regime} | Breadth: {summary.average_breadth:.2f}",
            f"Candidates: {summary.candidate_count} | Actionable: {summary.actionable_count} | Safer: {summary.safer_count}",
        ]
        if summary.top_rows:
            lines.append("Top candidates:")
            for row in summary.top_rows[:5]:
                lines.append(
                    f"- {row['ticker']} | {row.get('recommendation_bucket', 'Watchlist')} | score {row.get('composite_signal_score', 0)} | streak {row.get('institutional_buy_streak', 0)}"
                )
        if summary.risk_rows:
            lines.append("Risk flags:")
            for row in summary.risk_rows[:3]:
                lines.append(
                    f"- {row['ticker']} | {row.get('event_risk_note', 'clear')} | next event {row.get('next_event_date')}"
                )
        return "\n".join(lines)
