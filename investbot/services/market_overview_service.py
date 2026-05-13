from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from investbot.data_sources.derivatives_data import TaifexDerivativesClient, TaifexInstitutionSnapshot
from investbot.data_sources.economic_calendar import FmpEconomicCalendarClient
from investbot.data_sources.market_data import YahooMarketDataClient
from investbot.db.repositories import DailyAnalysisRepository
from investbot.services.summary_service import SummaryService


TW_SECTOR_MAP = {
    "2330.TW": "Semiconductors",
    "2317.TW": "Electronics Manufacturing",
    "2454.TW": "IC Design",
    "2308.TW": "Semiconductors",
    "2881.TW": "Financials",
    "2882.TW": "Financials",
    "2886.TW": "Financials",
    "2891.TW": "Financials",
    "2603.TW": "Shipping",
    "3037.TW": "AI Hardware",
    "2383.TW": "Electronics Components",
}

US_SECTOR_MAP = {
    "AAPL": "Mega-cap Tech",
    "MSFT": "Cloud Software",
    "NVDA": "AI Semiconductors",
    "AMZN": "Consumer Tech",
    "META": "Internet Platforms",
    "GOOGL": "Internet Platforms",
    "AVGO": "AI Semiconductors",
    "AMD": "Semiconductors",
    "NFLX": "Streaming",
    "PLTR": "AI Software",
    "TSLA": "EV / Autonomy",
    "SMH": "Semiconductors",
    "IWM": "Small-cap Beta",
    "DIA": "Dow Cyclicals",
}


@dataclass(slots=True)
class MarketOverview:
    overall_trend: str
    sentiment_label: str
    fear_greed_score: int
    fear_greed_rating: str
    fear_greed_source: str
    fear_greed_updated_at: str
    breadth_snapshot: float
    momentum_zones: list[str]
    caution_items: list[str]
    upcoming_macro_events: list[str]
    tw_futures_snapshot: TaifexInstitutionSnapshot | None
    us_derivatives_note: str


class MarketOverviewService:
    def __init__(
        self,
        repository: DailyAnalysisRepository | None = None,
        summary_service: SummaryService | None = None,
        market_data: YahooMarketDataClient | None = None,
        calendar_client: FmpEconomicCalendarClient | None = None,
        derivatives_client: TaifexDerivativesClient | None = None,
    ) -> None:
        self.repository = repository or DailyAnalysisRepository()
        self.summary_service = summary_service or SummaryService(repository=self.repository)
        self.market_data = market_data or YahooMarketDataClient()
        self.calendar_client = calendar_client or self._build_calendar_client()
        self.derivatives_client = derivatives_client or TaifexDerivativesClient()

    def build(self) -> MarketOverview:
        tw_summary = self.summary_service.build_market_summary("tw")
        us_summary = self.summary_service.build_market_summary("us")
        all_rows = self.repository.fetch_recent_candidates(limit=200)
        frame = pd.DataFrame(all_rows)
        vix = self.market_data.get_vix_value()
        fear_greed_snapshot = self.market_data.get_fear_greed_snapshot()

        breadth_values = []
        if tw_summary is not None:
            breadth_values.append(tw_summary.average_breadth)
        if us_summary is not None:
            breadth_values.append(us_summary.average_breadth)
        breadth_snapshot = round(sum(breadth_values) / len(breadth_values), 2) if breadth_values else 50.0

        if fear_greed_snapshot is not None:
            fear_greed_score = int(max(0, min(round(fear_greed_snapshot.score), 100)))
            fear_greed_rating = fear_greed_snapshot.rating
            fear_greed_source = fear_greed_snapshot.source
            fear_greed_updated_at = fear_greed_snapshot.updated_at.isoformat() if fear_greed_snapshot.updated_at else ""
        else:
            fear_greed_score = self._score_fear_greed(vix=vix, breadth_snapshot=breadth_snapshot, frame=frame)
            fear_greed_rating = self._label_sentiment(fear_greed_score)
            fear_greed_source = "Internal fallback"
            fear_greed_updated_at = ""
        overall_trend = self._label_overall_trend(fear_greed_score)
        sentiment_label = fear_greed_rating
        momentum_zones = self._top_momentum_zones(frame)
        caution_items = self._build_cautions(vix=vix, breadth_snapshot=breadth_snapshot, frame=frame)
        upcoming_macro_events = self._build_upcoming_macro_events()
        tw_futures_snapshot = self.derivatives_client.get_tw_tx_institution_snapshot()
        us_derivatives_note = "No truly equivalent daily official institutional index-futures positioning feed for U.S. equities."

        return MarketOverview(
            overall_trend=overall_trend,
            sentiment_label=sentiment_label,
            fear_greed_score=fear_greed_score,
            fear_greed_rating=fear_greed_rating,
            fear_greed_source=fear_greed_source,
            fear_greed_updated_at=fear_greed_updated_at,
            breadth_snapshot=breadth_snapshot,
            momentum_zones=momentum_zones,
            caution_items=caution_items,
            upcoming_macro_events=upcoming_macro_events,
            tw_futures_snapshot=tw_futures_snapshot,
            us_derivatives_note=us_derivatives_note,
        )

    def _score_fear_greed(self, vix: float | None, breadth_snapshot: float, frame: pd.DataFrame) -> int:
        score = 50.0
        if vix is None:
            score += 5
        elif vix < 17:
            score += 18
        elif vix < 23:
            score += 8
        else:
            score -= 15

        score += (breadth_snapshot - 50.0) * 0.45

        if not frame.empty and "composite_signal_score" in frame.columns:
            score += min(max(float(frame["composite_signal_score"].fillna(0).mean()) - 60.0, -10.0), 10.0)

        return int(max(0, min(round(score), 100)))

    def _label_overall_trend(self, fear_greed_score: int) -> str:
        if fear_greed_score >= 68:
            return "Risk-On Uptrend"
        if fear_greed_score >= 48:
            return "Balanced / Selective"
        return "Defensive / Risk-Off"

    def _label_sentiment(self, fear_greed_score: int) -> str:
        if fear_greed_score >= 75:
            return "Greed"
        if fear_greed_score >= 60:
            return "Constructive"
        if fear_greed_score >= 40:
            return "Neutral"
        if fear_greed_score >= 25:
            return "Cautious"
        return "Fear"

    def _top_momentum_zones(self, frame: pd.DataFrame) -> list[str]:
        if frame.empty:
            return []

        latest_date = frame["date"].max() if "date" in frame.columns else None
        if latest_date is not None:
            frame = frame[frame["date"] == latest_date].copy()

        frame["sector"] = frame.apply(self._map_sector, axis=1)
        grouped = (
            frame.groupby("sector", dropna=True)["composite_signal_score"]
            .mean()
            .sort_values(ascending=False)
            .head(4)
        )
        return [f"{sector} ({score:.0f})" for sector, score in grouped.items() if sector != "Other"]

    def _map_sector(self, row: pd.Series) -> str:
        ticker = str(row.get("ticker", "")).upper()
        market_type = str(row.get("type", "")).lower()
        if market_type == "tw":
            return TW_SECTOR_MAP.get(ticker, "Other")
        return US_SECTOR_MAP.get(ticker, "Other")

    def _build_cautions(self, vix: float | None, breadth_snapshot: float, frame: pd.DataFrame) -> list[str]:
        cautions: list[str] = []
        if vix is not None and vix >= 23:
            cautions.append("Volatility is elevated; position sizing should stay conservative.")
        if breadth_snapshot < 45:
            cautions.append("Breadth is weak, so single-name breakouts may fail more often.")
        if not frame.empty and "event_risk_note" in frame.columns:
            risk_count = int((frame["event_risk_note"].fillna("clear") != "clear").sum())
            if risk_count > 0:
                cautions.append(f"{risk_count} names are carrying event-risk flags.")
        if not cautions:
            cautions.append("No major market-wide warnings are flashing right now.")
        return cautions

    def _build_upcoming_macro_events(self) -> list[str]:
        events = self.calendar_client.get_upcoming_events(
            days_ahead=7,
            countries={"US", "CN", "EU", "JP", "TW"},
            impacts={"high", "3", "3-star", "three-star", "medium", "2", "2-star"},
        )
        labels: list[str] = []
        for event in events[:5]:
            labels.append(f"{event.event_date.isoformat()} | {event.country} | {event.title}")
        return labels

    def _build_calendar_client(self) -> FmpEconomicCalendarClient:
        try:
            from investbot.config import get_settings

            fmp_api_keys = get_settings().fmp_api_keys
        except ModuleNotFoundError:
            fmp_api_keys = ""
        return FmpEconomicCalendarClient(api_keys=fmp_api_keys)
