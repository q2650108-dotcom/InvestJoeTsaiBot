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

    def test_get_runtime_preferences_merges_universe_defaults(self) -> None:
        service = UserSettingsService(repository=FakeUserSettingsRepository())

        prefs = service.get_runtime_preferences("1")

        self.assertIn("tw_core_tickers", prefs)
        self.assertIn("us_core_tickers", prefs)
        self.assertIn("tw_explore_limit", prefs)
        self.assertIn("app_language", prefs)

    def test_update_runtime_preferences_persists_non_secret_settings(self) -> None:
        repository = FakeUserSettingsRepository(
            row={
                "telegram_chat_id": "1",
                "large_cap_only": True,
                "risk_tolerance_percent": 5.0,
                "min_institutional_buy_streak": 3,
                "app_language": "zh-TW",
                "high_risk_event_dates": "",
                "tw_core_tickers": "2330.TW",
                "us_core_tickers": "AAPL",
                "tw_explore_tickers": "",
                "us_explore_tickers": "",
                "tw_explore_limit": 12,
                "us_explore_limit": 8,
            }
        )
        service = UserSettingsService(repository=repository)

        updated = service.update_runtime_preferences(
            "1",
            {
                "app_language": "en",
                "tw_core_tickers": "2330.TW,2317.TW",
                "tw_explore_limit": 15,
            },
        )

        self.assertEqual(updated["app_language"], "en")
        self.assertEqual(updated["tw_core_tickers"], "2330.TW,2317.TW")
        self.assertEqual(updated["tw_explore_limit"], 15)
