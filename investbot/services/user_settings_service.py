from __future__ import annotations

from investbot.db.repositories import UserSettingsRepository


class UserSettingsService:
    def __init__(self, repository: UserSettingsRepository | None = None) -> None:
        self.repository = repository or UserSettingsRepository()
        self.settings = self._load_settings()

    def get_or_create(self, chat_id: str) -> dict[str, object]:
        current = self.repository.get_settings(chat_id)
        if current:
            return self._merge_defaults(current)

        payload = {
            "telegram_chat_id": chat_id,
            "large_cap_only": self.settings.default_large_cap_only,
            "risk_tolerance_percent": self.settings.default_risk_tolerance_percent,
            "min_institutional_buy_streak": self.settings.default_min_institutional_buy_streak,
        }
        return self.repository.upsert_settings(payload)

    def toggle_large_cap_only(self, chat_id: str) -> dict[str, object]:
        current = self.get_or_create(chat_id)
        payload = {
            "telegram_chat_id": chat_id,
            "large_cap_only": not bool(current["large_cap_only"]),
            "risk_tolerance_percent": current["risk_tolerance_percent"],
            "min_institutional_buy_streak": current["min_institutional_buy_streak"],
        }
        return self.repository.upsert_settings(payload)

    def cycle_min_institutional_buy_streak(self, chat_id: str) -> dict[str, object]:
        current = self.get_or_create(chat_id)
        current_value = int(current["min_institutional_buy_streak"])
        next_value = 1 if current_value >= 3 else current_value + 1
        payload = {
            "telegram_chat_id": chat_id,
            "large_cap_only": current["large_cap_only"],
            "risk_tolerance_percent": current["risk_tolerance_percent"],
            "min_institutional_buy_streak": next_value,
        }
        return self.repository.upsert_settings(payload)

    def filter_signals_for_user(self, settings_row: dict[str, object], signals: list[dict[str, object]]) -> list[dict[str, object]]:
        min_streak = int(
            settings_row.get(
                "min_institutional_buy_streak",
                self.settings.default_min_institutional_buy_streak,
            )
        )
        large_cap_only = bool(settings_row.get("large_cap_only", self.settings.default_large_cap_only))

        filtered: list[dict[str, object]] = []
        for row in signals:
            if large_cap_only and not row.get("is_large_cap", False):
                continue

            if row.get("signal_type") == "Institutional Accumulation":
                streak = int(row.get("institutional_buy_streak") or 0)
                if streak < min_streak:
                    continue
            filtered.append(row)
        return filtered

    def _merge_defaults(self, current: dict[str, object]) -> dict[str, object]:
        return {
            "telegram_chat_id": current["telegram_chat_id"],
            "large_cap_only": current.get("large_cap_only", self.settings.default_large_cap_only),
            "risk_tolerance_percent": current.get(
                "risk_tolerance_percent",
                self.settings.default_risk_tolerance_percent,
            ),
            "min_institutional_buy_streak": current.get(
                "min_institutional_buy_streak",
                self.settings.default_min_institutional_buy_streak,
            ),
        }

    def _load_settings(self):
        try:
            from investbot.config import get_settings

            return get_settings()
        except ModuleNotFoundError:
            class FallbackSettings:
                default_large_cap_only = True
                default_risk_tolerance_percent = 5.0
                default_min_institutional_buy_streak = 3
                telegram_allowed_chat_id = "0"

            return FallbackSettings()
