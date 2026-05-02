from __future__ import annotations

from unittest import TestCase

from investbot.data_sources.twse import TwseClient


class TwseClientTests(TestCase):
    def test_build_net_buy_map_sums_foreign_trust_and_dealer_flows(self) -> None:
        client = TwseClient(large_cap_tickers={"2330.TW"})
        rows = [
            {
                "證券代號": "2330",
                "外陸資買賣超股數(不含外資自營商)": "1,000",
                "投信買賣超股數": "2,000",
                "自營商買賣超股數(自行買賣)": "300",
                "自營商買賣超股數(避險)": "-100",
            }
        ]

        result = client._build_net_buy_map(rows)

        self.assertEqual(result["2330"], 3200)

    def test_get_large_cap_tickers_uses_configured_universe(self) -> None:
        client = TwseClient(large_cap_tickers={"2330.TW", "2317.TW"})
        self.assertEqual(client.get_large_cap_tickers(), {"2330.TW", "2317.TW"})
