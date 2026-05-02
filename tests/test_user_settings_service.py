from __future__ import annotations

from unittest import TestCase

from investbot.services.user_settings_service import UserSettingsService


class FakeUserSettingsRepository:
    def __init__(self, row: dict[str, object] | None = None) -> None:
        self.row = row
        self.last_payload: dict[str, object] | None = None

    def get_settings(self, chat_id: str) -> dict[str, object] | None:
        return self.row

    def upsert_settings(self, payload: dict[str, object]) -> dict[str, object]:
        self.last_payload = payload
        self.row = payload
        return payload


class UserSettingsServiceTests(TestCase):
    def test_filter_signals_for_user_respects_min_streak_and_large_cap(self) -> None:
        service = UserSettingsService(repository=FakeUserSettingsRepository())
        settings_row = {
            "telegram_chat_id": "1",
            "large_cap_only": True,
            "risk_tolerance_percent": 5.0,
            "min_institutional_buy_streak": 3,
        }
        rows = [
            {
                "ticker": "2330.TW",
                "signal_type": "Institutional Accumulation",
                "institutional_buy_streak": 2,
                "is_large_cap": True,
            },
            {
                "ticker": "2454.TW",
                "signal_type": "Institutional Accumulation",
                "institutional_buy_streak": 3,
                "is_large_cap": True,
            },
            {
                "ticker": "SMALL.TW",
                "signal_type": "Panic Reversal",
                "is_large_cap": False,
            },
        ]

        filtered = service.filter_signals_for_user(settings_row, rows)

        self.assertEqual(filtered, [rows[1]])

    def test_cycle_min_institutional_buy_streak_rotates_1_to_3(self) -> None:
        repository = FakeUserSettingsRepository(
            row={
                "telegram_chat_id": "1",
                "large_cap_only": True,
                "risk_tolerance_percent": 5.0,
                "min_institutional_buy_streak": 3,
            }
        )
        service = UserSettingsService(repository=repository)

        updated = service.cycle_min_institutional_buy_streak("1")

        self.assertEqual(updated["min_institutional_buy_streak"], 1)
