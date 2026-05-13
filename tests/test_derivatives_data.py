from __future__ import annotations

from datetime import date
from unittest import TestCase

from investbot.data_sources.derivatives_data import TaifexDerivativesClient


TAIFEX_HTML = """
<table>
  <thead>
    <tr>
      <th>序號</th>
      <th>商品名稱</th>
      <th>身份別</th>
      <th>未平倉餘額 多空淨額 口數</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td>臺股期貨</td>
      <td>自營商</td>
      <td>-1034</td>
    </tr>
    <tr>
      <td></td>
      <td></td>
      <td>投信</td>
      <td>46177</td>
    </tr>
    <tr>
      <td></td>
      <td></td>
      <td>外資</td>
      <td>-51132</td>
    </tr>
  </tbody>
</table>
"""


class TaifexDerivativesTests(TestCase):
    def test_parse_day_snapshot_extracts_tx_net_oi(self) -> None:
        client = TaifexDerivativesClient()

        row = client._parse_day_snapshot(TAIFEX_HTML, date(2026, 5, 7))

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.trade_date.isoformat(), "2026-05-07")
        self.assertEqual(row.foreign_net_oi, -51132)
        self.assertEqual(row.trust_net_oi, 46177)
        self.assertEqual(row.dealer_net_oi, -1034)

    def test_parse_day_snapshot_returns_none_when_tx_missing(self) -> None:
        client = TaifexDerivativesClient()

        row = client._parse_day_snapshot("<table><tr><td>小臺指</td></tr></table>", date(2026, 5, 7))

        self.assertIsNone(row)
