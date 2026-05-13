from __future__ import annotations

from unittest import TestCase

import pandas as pd

from investbot.services.confluence_engine import ConfluenceEngine


def build_history(days: int = 260, base: float = 100.0, slope: float = 0.8, volume: int = 1_000_000) -> pd.DataFrame:
    rows: list[dict[str, float | int | pd.Timestamp]] = []
    start = pd.Timestamp("2025-01-01")
    for i in range(days):
        close = base + (i * slope)
        rows.append(
            {
                "Date": start + pd.Timedelta(days=i),
                "Open": close - 1.0,
                "High": close + 2.0,
                "Low": close - 2.0,
                "Close": close,
                "Volume": volume,
            }
        )
    return pd.DataFrame(rows)


class ConfluenceEngineTests(TestCase):
    def test_evaluate_scores_high_quality_growth_leader(self) -> None:
        frame = build_history()
        frame.loc[255:, "Volume"] = 300_000
        frame.loc[259, "Volume"] = 2_500_000
        fund_data = {
            "eps_yoy": 35.0,
            "rev_yoy": 28.0,
            "pe_ratio": 18.0,
            "pb_ratio": 3.5,
            "inst_buy_days": 4,
        }

        result = ConfluenceEngine().evaluate(
            ticker="2330.TW",
            df_price=frame,
            fund_data=fund_data,
            market_ret_60=0.08,
        )

        self.assertGreaterEqual(result["scores"]["CAN_SLIM"], 20)
        self.assertGreaterEqual(result["scores"]["VCP"], 15)
        self.assertGreaterEqual(result["scores"]["Weinstein"], 15)
        self.assertEqual(result["scores"]["Graham"], 10)
        self.assertGreaterEqual(result["confluence_score"], 65)
        self.assertEqual(result["classification"], "Actionable")
        self.assertTrue(result["reasons"])
        self.assertIsNotNone(result["stop_loss_price"])

    def test_evaluate_penalizes_loss_making_laggard(self) -> None:
        frame = build_history(base=200.0, slope=-0.2, volume=500_000)
        fund_data = {
            "eps_yoy": -20.0,
            "rev_yoy": -12.0,
            "pe_ratio": -5.0,
            "pb_ratio": 4.0,
            "inst_buy_days": 0,
        }

        result = ConfluenceEngine().evaluate(
            ticker="XYZ",
            df_price=frame,
            fund_data=fund_data,
            market_ret_60=0.06,
        )

        self.assertEqual(result["scores"]["CAN_SLIM"], 0)
        self.assertEqual(result["scores"]["Graham"], 0)
        self.assertLess(result["confluence_score"], 40)
        self.assertEqual(result["classification"], "Watch")
        self.assertTrue(any("估值" in reason or "趨勢" in reason for reason in result["reasons"]))
