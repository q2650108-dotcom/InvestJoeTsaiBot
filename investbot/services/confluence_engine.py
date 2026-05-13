from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import math

import pandas as pd


@dataclass(slots=True)
class ConfluenceEvaluation:
    ticker: str
    scores: dict[str, int]
    confluence_score: int
    classification: str
    reasons: list[str]
    stop_loss_price: float | None

    def to_record(self) -> dict[str, object]:
        return {
            "strategy_scores": self.scores,
            "confluence_score": float(self.confluence_score),
            "confluence_classification": self.classification,
            "confluence_reasons": self.reasons,
            "stop_loss_price": self.stop_loss_price,
        }


class ConfluenceEngine:
    def evaluate(
        self,
        ticker: str,
        df_price: pd.DataFrame,
        fund_data: dict[str, Any],
        market_ret_60: float,
    ) -> dict[str, object]:
        frame = self._prepare_frame(df_price)
        if frame.empty:
            return {
                "ticker": ticker.upper(),
                "scores": {"CAN_SLIM": 0, "VCP": 0, "Weinstein": 0, "Graham": 0},
                "confluence_score": 0,
                "classification": "Watch",
                "reasons": ["歷史資料不足 250 個交易日，無法完整評估多策略共振。"],
                "stop_loss_price": None,
            }
        latest = frame.iloc[-1]
        close_price = float(latest["Close"])
        atr_14 = float(latest["atr_14"]) if not pd.isna(latest["atr_14"]) else 0.0

        can_slim_score, can_slim_reasons = self._score_can_slim(frame, fund_data)
        vcp_score, vcp_reasons = self._score_vcp(frame)
        weinstein_score, weinstein_reasons = self._score_weinstein(frame, market_ret_60)
        graham_score, graham_reasons = self._score_graham(fund_data)

        total_score = int(can_slim_score + vcp_score + weinstein_score + graham_score)
        if total_score >= 80:
            classification = "Actionable"
        elif total_score >= 65:
            classification = "Candidate"
        else:
            classification = "Watch"

        reasons = can_slim_reasons + vcp_reasons + weinstein_reasons + graham_reasons
        if not reasons:
            reasons = ["多策略沒有形成足夠共振，暫時只保留觀察。"]

        stop_loss_price = None
        if atr_14 > 0:
            stop_loss_price = round(close_price - (atr_14 * 1.5), 2)

        result = ConfluenceEvaluation(
            ticker=ticker.upper(),
            scores={
                "CAN_SLIM": can_slim_score,
                "VCP": vcp_score,
                "Weinstein": weinstein_score,
                "Graham": graham_score,
            },
            confluence_score=total_score,
            classification=classification,
            reasons=reasons,
            stop_loss_price=stop_loss_price,
        )
        return {
            "ticker": result.ticker,
            "scores": result.scores,
            "confluence_score": result.confluence_score,
            "classification": result.classification,
            "reasons": result.reasons,
            "stop_loss_price": result.stop_loss_price,
        }

    def _prepare_frame(self, df_price: pd.DataFrame) -> pd.DataFrame:
        frame = df_price.copy()
        if "Date" in frame.columns:
            frame = frame.sort_values("Date").reset_index(drop=True)
        frame["ma_20"] = frame["Close"].rolling(20).mean()
        frame["ma_50"] = frame["Close"].rolling(50).mean()
        frame["ma_200"] = frame["Close"].rolling(200).mean()
        frame["high_250"] = frame["High"].rolling(250).max()
        prev_close = frame["Close"].shift(1)
        true_range = pd.concat(
            [
                frame["High"] - frame["Low"],
                (frame["High"] - prev_close).abs(),
                (frame["Low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        frame["atr_14"] = true_range.rolling(14).mean()
        frame["vol_5"] = frame["Volume"].rolling(5).mean()
        frame["vol_50"] = frame["Volume"].rolling(50).mean()
        frame["stock_ret_60"] = (frame["Close"] / frame["Close"].shift(60)) - 1
        return frame.dropna().reset_index(drop=True)

    def _score_can_slim(self, frame: pd.DataFrame, fund_data: dict[str, Any]) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []
        rev_yoy = self._to_float(fund_data.get("rev_yoy"))
        eps_yoy = self._to_float(fund_data.get("eps_yoy"))
        inst_buy_days = int(fund_data.get("inst_buy_days") or 0)
        latest = frame.iloc[-1]
        high_250 = self._to_float(latest["high_250"])
        close = self._to_float(latest["Close"])
        pct_from_high = ((close / high_250) - 1) if high_250 and high_250 > 0 else None

        if rev_yoy is not None and eps_yoy is not None and rev_yoy > 20 and eps_yoy > 20:
            score += 10
            reasons.append("CAN SLIM：營收與 EPS 年增同步強勁。")
        elif rev_yoy is not None and eps_yoy is not None and rev_yoy > 0 and eps_yoy > 0:
            score += 5
            reasons.append("CAN SLIM：基本成長仍為正。")

        if pct_from_high is not None and pct_from_high >= -0.05:
            score += 10
            reasons.append("CAN SLIM：股價仍貼近 250 日新高。")
        elif pct_from_high is not None and pct_from_high >= -0.15:
            score += 5

        if inst_buy_days >= 3:
            score += 5
            reasons.append("CAN SLIM：法人連買天數已形成支持。")
        elif inst_buy_days >= 1:
            score += 3

        return score, reasons

    def _score_vcp(self, frame: pd.DataFrame) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []
        latest = frame.iloc[-1]
        close = self._to_float(latest["Close"]) or 0.0
        ma_20 = self._to_float(latest["ma_20"]) or 0.0
        ma_50 = self._to_float(latest["ma_50"]) or 0.0
        ma_200 = self._to_float(latest["ma_200"]) or 0.0
        atr_14 = self._to_float(latest["atr_14"]) or 0.0
        vol_5 = self._to_float(latest["vol_5"]) or 0.0
        vol_50 = self._to_float(latest["vol_50"]) or 0.0
        volume = self._to_float(latest["Volume"]) or 0.0

        is_uptrend = close > ma_20 > ma_50 > ma_200 if ma_200 > 0 else False
        if is_uptrend:
            score += 15
            reasons.append("VCP：均線呈現多頭趨勢模板。")

        atr_pct = (atr_14 / close) if close > 0 else math.inf
        if atr_pct < 0.03:
            score += 10
            reasons.append("VCP：波動率極小，籌碼沉澱明顯。")
        elif atr_pct < 0.05:
            score += 5

        if vol_5 > 0 and vol_50 > 0 and vol_5 < vol_50 * 0.5:
            score += 10
            reasons.append("VCP：近期成交量明顯萎縮。")
        elif vol_50 > 0 and volume > vol_50 * 2:
            score += 10
            reasons.append("VCP：出現帶量突破足跡。")

        return score, reasons

    def _score_weinstein(self, frame: pd.DataFrame, market_ret_60: float) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []
        latest = frame.iloc[-1]
        close = self._to_float(latest["Close"]) or 0.0
        ma_200 = self._to_float(latest["ma_200"])
        ma_200_20d_ago = self._to_float(frame.iloc[-20]["ma_200"]) if len(frame) >= 20 else None

        if ma_200 and ma_200_20d_ago and ma_200_20d_ago > 0:
            slope_ratio = ma_200 / ma_200_20d_ago
            if close > ma_200 and slope_ratio > 1.02:
                score += 10
                reasons.append("溫斯坦：站上年線且年線持續上揚。")

        stock_ret_60 = self._to_float(latest["stock_ret_60"])
        if stock_ret_60 is not None:
            if stock_ret_60 > market_ret_60 + 0.1:
                score += 15
                reasons.append("溫斯坦：60 日相對強度明顯打敗大盤。")
            elif stock_ret_60 > market_ret_60:
                score += 5

        return score, reasons

    def _score_graham(self, fund_data: dict[str, Any]) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []
        pe_ratio = self._to_float(fund_data.get("pe_ratio"))
        pb_ratio = self._to_float(fund_data.get("pb_ratio"))

        if pe_ratio is not None and pb_ratio is not None and 0 < pe_ratio < 15 and 0 < pb_ratio < 2:
            score += 15
            reasons.append("葛拉漢：估值提供明顯安全邊際。")
        elif pe_ratio is not None and 0 < pe_ratio < 25:
            score += 10
            reasons.append("葛拉漢：估值仍屬合理區間。")
        elif pe_ratio is not None and pe_ratio <= 0:
            reasons.append("葛拉漢：仍屬虧損狀態，沒有估值保護。")
        else:
            reasons.append("葛拉漢：估值資料不足，安全邊際無法確認。")

        return score, reasons

    def _to_float(self, value: Any) -> float | None:
        if value in (None, "", "nan"):
            return None
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(result):
            return None
        return result
