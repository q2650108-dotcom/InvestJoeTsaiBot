from __future__ import annotations

from unittest import TestCase

from investbot.services.market_panorama_service import MarketPanoramaService


class MarketPanoramaServiceTests(TestCase):
    def test_tw_panorama_contains_widgets_and_theme_cards(self) -> None:
        service = MarketPanoramaService()

        config = service.get_config("tw")

        self.assertEqual(config["market_key"], "tw")
        self.assertTrue(config["ticker_tape"]["symbols"])
        self.assertTrue(config["market_overview"]["tabs"])
        self.assertTrue(config["theme_cards"])

    def test_us_panorama_contains_holdings_candidates_for_watch_actions(self) -> None:
        service = MarketPanoramaService()

        config = service.get_config("us")
        symbols = {item["ticker"] for card in config["theme_cards"] for item in card["symbols"]}

        self.assertIn("NVDA", symbols)
        self.assertIn("AVGO", symbols)
