from __future__ import annotations

from datetime import date
from unittest import TestCase

from investbot.data_sources.provider_router import ProviderError, QuoteProviderRouter, QuoteSnapshot


class StubProvider:
    def __init__(self, snapshot: QuoteSnapshot | None = None, should_fail: bool = False) -> None:
        self.snapshot = snapshot
        self.should_fail = should_fail

    def get_quote_snapshot(self, ticker: str) -> QuoteSnapshot:
        if self.should_fail:
            raise ProviderError("rate limited")
        if self.snapshot is None:
            raise ProviderError("no data")
        return self.snapshot


class ProviderRouterTests(TestCase):
    def test_router_falls_back_to_second_provider(self) -> None:
        router = QuoteProviderRouter()
        router.providers = [
            StubProvider(should_fail=True),
            StubProvider(snapshot=QuoteSnapshot(latest_price=101.5, next_earnings_date=date(2026, 5, 20))),
        ]

        snapshot = router.get_quote_snapshot("AAPL")

        self.assertEqual(snapshot.latest_price, 101.5)
        self.assertEqual(snapshot.next_earnings_date, date(2026, 5, 20))

    def test_router_raises_when_all_providers_fail(self) -> None:
        router = QuoteProviderRouter()
        router.providers = [StubProvider(should_fail=True), StubProvider(should_fail=True)]

        with self.assertRaises(ProviderError):
            router.get_quote_snapshot("AAPL")
