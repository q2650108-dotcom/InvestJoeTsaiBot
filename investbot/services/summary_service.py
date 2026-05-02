from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from investbot.db.repositories import DailyAnalysisRepository
from investbot.services.decision_support import DecisionSupportService


@dataclass(slots=True)
class MarketSummary:
    market_type: str
    summary_date: str
    regime: str
    average_breadth: float
    candidate_count: int
    actionable_count: int
    safer_count: int
    top_rows: list[dict[str, object]]
    core_rows: list[dict[str, object]]
    explore_rows: list[dict[str, object]]
    risk_rows: list[dict[str, object]]


class SummaryService:
    def __init__(
        self,
        repository: DailyAnalysisRepository | None = None,
        decision_support: DecisionSupportService | None = None,
    ) -> None:
        self.repository = repository or DailyAnalysisRepository()
        self.decision_support = decision_support or DecisionSupportService()

    def build_market_summary(self, market_type: str, limit: int = 5) -> MarketSummary | None:
        rows = self.repository.fetch_latest_market_rows(market_type)
        if not rows:
            return None

        frame = pd.DataFrame(rows)
        summary_date = str(frame["date"].max())
        regime = str(frame["market_regime"].mode().iloc[0]) if "market_regime" in frame and not frame["market_regime"].dropna().empty else "Unknown"
        average_breadth = round(float(frame["breadth_score"].fillna(0).mean()), 2) if "breadth_score" in frame else 0.0
        if "event_risk_note" not in frame:
            frame["event_risk_note"] = "clear"
        if "recommendation_bucket" not in frame:
            frame["recommendation_bucket"] = "Watchlist"
        if "universe_bucket" not in frame:
            frame["universe_bucket"] = "core"
        if "institutional_buy_streak" not in frame:
            frame["institutional_buy_streak"] = 0
        if "composite_signal_score" not in frame:
            frame["composite_signal_score"] = 0.0
        top_rows = (
            frame.sort_values(by=["composite_signal_score", "institutional_buy_streak"], ascending=[False, False])
            .head(limit)
            .to_dict("records")
        )
        core_rows = (
            frame[frame["universe_bucket"] == "core"]
            .sort_values(by=["composite_signal_score", "institutional_buy_streak"], ascending=[False, False])
            .head(limit)
            .to_dict("records")
        )
        explore_rows = (
            frame[frame["universe_bucket"] == "explore"]
            .sort_values(by=["composite_signal_score", "institutional_buy_streak"], ascending=[False, False])
            .head(limit)
            .to_dict("records")
        )
        risk_rows = (
            frame[frame["event_risk_note"] != "clear"]
            .sort_values(by=["composite_signal_score"], ascending=[True])
            .head(limit)
            .to_dict("records")
        )
        top_rows = self.decision_support.enrich_rows(top_rows)
        core_rows = self.decision_support.enrich_rows(core_rows)
        explore_rows = self.decision_support.enrich_rows(explore_rows)
        risk_rows = self.decision_support.enrich_rows(risk_rows)
        actionable_count = int((frame["recommendation_bucket"] == "Actionable").sum())
        safer_count = int((frame["recommendation_bucket"] == "Safer Follow-Through").sum())

        return MarketSummary(
            market_type=market_type,
            summary_date=summary_date,
            regime=regime,
            average_breadth=average_breadth,
            candidate_count=len(frame),
            actionable_count=actionable_count,
            safer_count=safer_count,
            top_rows=top_rows,
            core_rows=core_rows,
            explore_rows=explore_rows,
            risk_rows=risk_rows,
        )
