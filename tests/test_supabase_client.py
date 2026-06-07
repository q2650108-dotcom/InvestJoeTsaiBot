from __future__ import annotations

import os
import sys
import types
from unittest import TestCase
from unittest.mock import patch

from investbot.db.supabase_client import get_supabase


class SupabaseClientTests(TestCase):
    def tearDown(self) -> None:
        get_supabase.cache_clear()
        sys.modules.pop("supabase", None)
        sys.modules.pop("investbot.config", None)

    def test_frontend_role_uses_anon_key_when_available(self) -> None:
        captured: dict[str, str] = {}

        def fake_create_client(url: str, key: str) -> object:
            captured["url"] = url
            captured["key"] = key
            return object()

        sys.modules["supabase"] = types.SimpleNamespace(create_client=fake_create_client)
        sys.modules["investbot.config"] = types.SimpleNamespace(
            get_settings=lambda: types.SimpleNamespace(
                supabase_url="https://example.supabase.co",
                supabase_key="",
                supabase_service_key="service-key",
                supabase_anon_key="anon-key",
            )
        )
        with patch.dict(
            os.environ,
            {
                "INVESTBOT_SUPABASE_ROLE": "frontend",
            },
            clear=True,
        ):
            get_supabase.cache_clear()
            get_supabase()

        self.assertEqual(captured["key"], "anon-key")

    def test_service_role_prefers_service_key(self) -> None:
        captured: dict[str, str] = {}

        def fake_create_client(url: str, key: str) -> object:
            captured["url"] = url
            captured["key"] = key
            return object()

        sys.modules["supabase"] = types.SimpleNamespace(create_client=fake_create_client)
        sys.modules["investbot.config"] = types.SimpleNamespace(
            get_settings=lambda: types.SimpleNamespace(
                supabase_url="https://example.supabase.co",
                supabase_key="",
                supabase_service_key="service-key",
                supabase_anon_key="anon-key",
            )
        )
        with patch.dict(
            os.environ,
            {
                "INVESTBOT_SUPABASE_ROLE": "service",
            },
            clear=True,
        ):
            get_supabase.cache_clear()
            get_supabase()

        self.assertEqual(captured["key"], "service-key")
