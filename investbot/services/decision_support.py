from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DecisionExplanation:
    recommendation_level: str
    win_rate_label: str
    risk_level: str
    reward_risk_label: str
    suggested_action: str
    rationale: list[str]
    risks: list[str]

    def to_record(self) -> dict[str, object]:
        return {
            "recommendation_level": self.recommendation_level,
            "win_rate_label": self.win_rate_label,
            "risk_level": self.risk_level,
            "reward_risk_label": self.reward_risk_label,
            "suggested_action": self.suggested_action,
            "rationale": self.rationale,
            "risks": self.risks,
        }


class DecisionSupportService:
    def explain(self, row: dict[str, Any]) -> DecisionExplanation:
        bucket = str(row.get("recommendation_bucket", "Watchlist"))
        universe_bucket = str(row.get("universe_bucket", "core"))
        buy_streak = int(row.get("institutional_buy_streak") or 0)
        composite_score = float(row.get("composite_signal_score") or 0.0)
        relative_strength_score = float(row.get("relative_strength_score") or 0.0)
        event_risk_score = float(row.get("event_risk_score") or 50.0)
        entry_quality_score = float(row.get("entry_quality_score") or 0.0)
        market_regime = str(row.get("market_regime", "Unknown"))
        event_risk_note = str(row.get("event_risk_note", "clear"))

        rationale: list[str] = []
        risks: list[str] = []

        if buy_streak >= 3:
            rationale.append(f"Institutional buying has persisted for {buy_streak} sessions.")
        elif buy_streak == 2:
            rationale.append("Institutional buying is building into a second session.")
        elif buy_streak == 1:
            rationale.append("Institutional buying has just turned positive.")

        if relative_strength_score >= 70:
            rationale.append("Relative strength is decisively above the market benchmark.")
        elif relative_strength_score >= 60:
            rationale.append("Relative strength is supportive versus the benchmark.")

        if entry_quality_score >= 70:
            rationale.append("Price location is constructive and not excessively extended.")
        elif entry_quality_score >= 55:
            rationale.append("Entry quality is acceptable if execution stays disciplined.")

        if market_regime == "Risk-On":
            rationale.append("The market regime is supportive for trend-following entries.")
        elif market_regime == "Neutral":
            risks.append("The broader market is neutral, so follow-through may be slower.")
        else:
            risks.append("The broader market is risk-off, so hit rates can fall quickly.")

        if universe_bucket == "explore":
            risks.append("This idea is in the Explore pool, so it should not outrank core large-cap names.")
        elif universe_bucket == "core":
            rationale.append("This name belongs to the core monitoring pool.")

        if event_risk_score < 45 or event_risk_note != "clear":
            risks.append(f"Event risk is elevated: {self._format_event_risk_note(event_risk_note)}.")
        elif event_risk_score < 65:
            risks.append("Event risk is manageable but still worth monitoring.")

        if composite_score >= 82 and bucket == "Safer Follow-Through":
            recommendation_level = "High Conviction Core"
            win_rate_label = "High"
            risk_level = "Medium"
            reward_risk_label = "Favorable"
            suggested_action = "Normal position sizing or staged entries on minor pullbacks."
        elif composite_score >= 70 and bucket == "Actionable":
            recommendation_level = "Actionable Setup"
            win_rate_label = "Medium-High"
            risk_level = "Medium"
            reward_risk_label = "Balanced"
            suggested_action = "Pilot size first, then add if confirmation holds."
        else:
            recommendation_level = "Watch and Wait"
            win_rate_label = "Medium-Low"
            risk_level = "Medium-High"
            reward_risk_label = "Unclear"
            suggested_action = "Observe only until the odds improve."

        if universe_bucket == "explore" and recommendation_level == "Actionable Setup":
            suggested_action = "Small trial size only; keep core capital focused on large caps."

        if not rationale:
            rationale.append("The current signal does not yet have enough stacked evidence.")
        if not risks:
            risks.append("No major risk flags are active right now, but standard stop discipline still applies.")

        return DecisionExplanation(
            recommendation_level=recommendation_level,
            win_rate_label=win_rate_label,
            risk_level=risk_level,
            reward_risk_label=reward_risk_label,
            suggested_action=suggested_action,
            rationale=rationale,
            risks=risks,
        )

    def enrich_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for row in rows:
            explanation = self.explain(row)
            enriched_row = dict(row)
            enriched_row.update(explanation.to_record())
            enriched.append(enriched_row)
        return enriched

    def _format_event_risk_note(self, note: str) -> str:
        if ":" not in note:
            return note
        prefix, label = note.split(":", 1)
        return f"{prefix} ({label.replace('_', ' ')})"
