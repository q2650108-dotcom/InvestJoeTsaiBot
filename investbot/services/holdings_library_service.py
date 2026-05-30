from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from investbot.data_sources.market_data import YahooMarketDataClient
from investbot.db.repositories import DailyAnalysisRepository, GuruPortfolioRepository, UserWatchlistRepository


@dataclass(frozen=True, slots=True)
class HoldingsSourceDefinition:
    source_id: str
    group_key: str
    group_label: str
    source_type: str
    symbol: str
    display_name: str
    added_from: str
    market_type: str
    disclosure_hint: str
    rank_order: int


TW_ETF_SOURCES: tuple[HoldingsSourceDefinition, ...] = (
    HoldingsSourceDefinition("tw-0050", "tw_etf", "台股 ETF", "etf", "0050.TW", "元大台灣 50", "TW ETF 0050", "tw", "ETF 成分股參考，揭露時間依基金公告為準。", 10),
    HoldingsSourceDefinition("tw-0056", "tw_etf", "台股 ETF", "etf", "0056.TW", "元大高股息", "TW ETF 0056", "tw", "ETF 成分股參考，揭露時間依基金公告為準。", 20),
    HoldingsSourceDefinition("tw-006208", "tw_etf", "台股 ETF", "etf", "006208.TW", "富邦台 50", "TW ETF 006208", "tw", "ETF 成分股參考，揭露時間依基金公告為準。", 30),
    HoldingsSourceDefinition("tw-00878", "tw_etf", "台股 ETF", "etf", "00878.TW", "國泰永續高股息", "TW ETF 00878", "tw", "ETF 成分股參考，揭露時間依基金公告為準。", 40),
)

US_ETF_SOURCES: tuple[HoldingsSourceDefinition, ...] = (
    HoldingsSourceDefinition("us-spy", "us_etf", "美股 ETF", "etf", "SPY", "SPDR S&P 500 ETF", "US ETF SPY", "us", "ETF 成分股參考，揭露時間依基金公告為準。", 10),
    HoldingsSourceDefinition("us-qqq", "us_etf", "美股 ETF", "etf", "QQQ", "Invesco QQQ Trust", "US ETF QQQ", "us", "ETF 成分股參考，揭露時間依基金公告為準。", 20),
    HoldingsSourceDefinition("us-voo", "us_etf", "美股 ETF", "etf", "VOO", "Vanguard S&P 500 ETF", "US ETF VOO", "us", "ETF 成分股參考，揭露時間依基金公告為準。", 30),
    HoldingsSourceDefinition("us-ivv", "us_etf", "美股 ETF", "etf", "IVV", "iShares Core S&P 500 ETF", "US ETF IVV", "us", "ETF 成分股參考，揭露時間依基金公告為準。", 40),
    HoldingsSourceDefinition("us-smh", "us_etf", "美股 ETF", "etf", "SMH", "VanEck Semiconductor ETF", "US ETF SMH", "us", "ETF 成分股參考，揭露時間依基金公告為準。", 50),
)

GURU_SOURCES: tuple[HoldingsSourceDefinition, ...] = (
    HoldingsSourceDefinition("guru-berkshire", "guru_13f", "機構 13F", "guru", "BRK", "Berkshire Hathaway", "Berkshire Top Holdings", "us", "13F 揭露資料，具季報延遲。", 10),
    HoldingsSourceDefinition("guru-ark", "guru_13f", "機構 13F", "guru", "ARK", "ARK Invest", "ARK Top Holdings", "us", "13F 揭露資料，具季報延遲。", 20),
    HoldingsSourceDefinition("guru-bridgewater", "guru_13f", "機構 13F", "guru", "BRIDGEWATER", "Bridgewater", "Bridgewater Top Holdings", "us", "13F 揭露資料，具季報延遲。", 30),
    HoldingsSourceDefinition("guru-soros", "guru_13f", "機構 13F", "guru", "SOROS", "Soros Fund", "Soros Top Holdings", "us", "13F 揭露資料，具季報延遲。", 40),
)


DEFAULT_ETF_HOLDINGS: dict[str, list[dict[str, object]]] = {
    "tw-0050": [
        {"ticker": "2330.TW", "weight": 58.2},
        {"ticker": "2317.TW", "weight": 4.8},
        {"ticker": "2454.TW", "weight": 4.3},
        {"ticker": "2308.TW", "weight": 2.4},
        {"ticker": "2881.TW", "weight": 2.2},
        {"ticker": "2882.TW", "weight": 2.0},
        {"ticker": "1303.TW", "weight": 1.7},
        {"ticker": "1301.TW", "weight": 1.6},
    ],
    "tw-0056": [
        {"ticker": "2881.TW", "weight": 3.9},
        {"ticker": "2882.TW", "weight": 3.8},
        {"ticker": "2303.TW", "weight": 3.5},
        {"ticker": "1216.TW", "weight": 3.2},
        {"ticker": "2603.TW", "weight": 3.0},
        {"ticker": "2412.TW", "weight": 2.8},
    ],
    "tw-006208": [
        {"ticker": "2330.TW", "weight": 57.5},
        {"ticker": "2317.TW", "weight": 4.9},
        {"ticker": "2454.TW", "weight": 4.5},
        {"ticker": "2308.TW", "weight": 2.5},
        {"ticker": "2881.TW", "weight": 2.1},
        {"ticker": "2882.TW", "weight": 2.0},
    ],
    "tw-00878": [
        {"ticker": "2881.TW", "weight": 4.0},
        {"ticker": "2882.TW", "weight": 3.8},
        {"ticker": "2891.TW", "weight": 3.6},
        {"ticker": "2886.TW", "weight": 3.3},
        {"ticker": "1216.TW", "weight": 3.0},
        {"ticker": "2603.TW", "weight": 2.9},
    ],
    "us-spy": [
        {"ticker": "AAPL", "weight": 7.1},
        {"ticker": "MSFT", "weight": 6.9},
        {"ticker": "NVDA", "weight": 6.1},
        {"ticker": "AMZN", "weight": 3.7},
        {"ticker": "META", "weight": 2.7},
        {"ticker": "GOOGL", "weight": 2.1},
    ],
    "us-qqq": [
        {"ticker": "MSFT", "weight": 8.9},
        {"ticker": "AAPL", "weight": 8.6},
        {"ticker": "NVDA", "weight": 8.1},
        {"ticker": "AMZN", "weight": 5.2},
        {"ticker": "META", "weight": 4.7},
        {"ticker": "GOOGL", "weight": 2.6},
        {"ticker": "AVGO", "weight": 4.1},
    ],
    "us-voo": [
        {"ticker": "AAPL", "weight": 7.1},
        {"ticker": "MSFT", "weight": 6.9},
        {"ticker": "NVDA", "weight": 6.0},
        {"ticker": "AMZN", "weight": 3.8},
        {"ticker": "META", "weight": 2.6},
        {"ticker": "GOOGL", "weight": 2.1},
    ],
    "us-ivv": [
        {"ticker": "AAPL", "weight": 7.2},
        {"ticker": "MSFT", "weight": 6.9},
        {"ticker": "NVDA", "weight": 6.1},
        {"ticker": "AMZN", "weight": 3.8},
        {"ticker": "META", "weight": 2.6},
        {"ticker": "GOOGL", "weight": 2.1},
    ],
    "us-smh": [
        {"ticker": "NVDA", "weight": 20.1},
        {"ticker": "TSM", "weight": 13.1},
        {"ticker": "AVGO", "weight": 7.4},
        {"ticker": "AMD", "weight": 6.7},
        {"ticker": "QCOM", "weight": 5.1},
        {"ticker": "TXN", "weight": 4.9},
    ],
}

DEFAULT_GURU_HOLDINGS: dict[str, dict[str, object]] = {
    "guru-berkshire": {
        "quarter": "2026-Q1",
        "as_of": "2026-03-31",
        "rows": [
            {"ticker": "AAPL", "weight": 22.5, "change": "Hold"},
            {"ticker": "AXP", "weight": 15.1, "change": "Hold"},
            {"ticker": "KO", "weight": 10.7, "change": "Hold"},
            {"ticker": "OXY", "weight": 8.9, "change": "Add"},
            {"ticker": "BAC", "weight": 8.2, "change": "Trim"},
        ],
    },
    "guru-ark": {
        "quarter": "2026-Q1",
        "as_of": "2026-03-31",
        "rows": [
            {"ticker": "TSLA", "weight": 8.4, "change": "Hold"},
            {"ticker": "PLTR", "weight": 6.3, "change": "Add"},
            {"ticker": "COIN", "weight": 5.7, "change": "Add"},
            {"ticker": "ROKU", "weight": 5.1, "change": "Trim"},
            {"ticker": "CRWD", "weight": 4.8, "change": "Hold"},
        ],
    },
    "guru-bridgewater": {
        "quarter": "2026-Q1",
        "as_of": "2026-03-31",
        "rows": [
            {"ticker": "SPY", "weight": 11.2, "change": "Hold"},
            {"ticker": "IVV", "weight": 8.8, "change": "Hold"},
            {"ticker": "PG", "weight": 4.1, "change": "Add"},
            {"ticker": "KO", "weight": 3.9, "change": "Add"},
            {"ticker": "JNJ", "weight": 3.7, "change": "Hold"},
        ],
    },
    "guru-soros": {
        "quarter": "2026-Q1",
        "as_of": "2026-03-31",
        "rows": [
            {"ticker": "GOOGL", "weight": 9.4, "change": "Add"},
            {"ticker": "AMZN", "weight": 8.2, "change": "Hold"},
            {"ticker": "MSFT", "weight": 6.0, "change": "Hold"},
            {"ticker": "NVDA", "weight": 5.1, "change": "Trim"},
            {"ticker": "META", "weight": 4.9, "change": "Add"},
        ],
    },
}

RECOMMENDATION_PLACEHOLDERS = {
    "",
    "Watchlist",
    "觀察",
    "待分析",
    "Unknown",
}

SUGGESTED_ACTION_PLACEHOLDERS = {
    "",
    "Run analysis to refresh details.",
    "Price is live, but this holding has not entered the latest analysis set yet.",
    "請先執行分析以刷新資料",
    "只有價格資料，尚未進入最新分析集合",
}


def merge_holdings_display_rows(
    holdings_rows: list[dict[str, object]],
    candidate_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    candidate_by_ticker = {
        str(row.get("ticker") or "").upper(): row
        for row in candidate_rows
        if str(row.get("ticker") or "").strip()
    }
    fill_columns = (
        "close_price",
        "composite_signal_score",
        "confluence_score",
        "recommendation_bucket",
        "institutional_buy_streak",
        "relative_strength_score",
        "suggested_action",
        "date",
    )
    merged_rows: list[dict[str, object]] = []
    for row in holdings_rows:
        ticker = str(row.get("ticker") or "").upper()
        merged = dict(row)
        candidate = candidate_by_ticker.get(ticker, {})
        for column in fill_columns:
            current = merged.get(column)
            candidate_value = candidate.get(column)
            if candidate_value in (None, ""):
                continue
            if column == "recommendation_bucket":
                if str(current).strip() in RECOMMENDATION_PLACEHOLDERS:
                    merged[column] = candidate_value
                continue
            if column == "suggested_action":
                if str(current).strip() in SUGGESTED_ACTION_PLACEHOLDERS:
                    merged[column] = candidate_value
                continue
            if current in (None, "", 0):
                merged[column] = candidate_value
        merged_rows.append(merged)
    return merged_rows


class HoldingsLibraryService:
    def __init__(
        self,
        analysis_repository: DailyAnalysisRepository | None = None,
        watchlist_repository: UserWatchlistRepository | None = None,
        guru_repository: GuruPortfolioRepository | None = None,
        market_data: YahooMarketDataClient | None = None,
    ) -> None:
        self.analysis_repository = analysis_repository or DailyAnalysisRepository()
        self.watchlist_repository = watchlist_repository or UserWatchlistRepository()
        self.guru_repository = guru_repository or GuruPortfolioRepository()
        self.market_data = market_data or YahooMarketDataClient()
        self._definitions = {
            definition.source_id: definition
            for definition in (*TW_ETF_SOURCES, *US_ETF_SOURCES, *GURU_SOURCES)
        }

    def list_sources(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        group_order = {"tw_etf": 0, "us_etf": 1, "guru_13f": 2}
        for definition in sorted(
            self._definitions.values(),
            key=lambda item: (group_order.get(item.group_key, 99), item.rank_order),
        ):
            rows.append(
                {
                    "source_id": definition.source_id,
                    "group_key": definition.group_key,
                    "group_label": definition.group_label,
                    "source_type": definition.source_type,
                    "market_type": definition.market_type,
                    "symbol": definition.symbol,
                    "display_name": definition.display_name,
                    "added_from": definition.added_from,
                    "disclosure_hint": definition.disclosure_hint,
                    "last_disclosed_at": self._resolve_disclosed_at(definition),
                }
            )
        return rows

    def get_source_snapshot(self, source_id: str) -> dict[str, object]:
        definition = self._definitions[source_id]
        if definition.source_type == "etf":
            loaded = self._load_etf_holdings(definition)
            quarter = ""
        else:
            loaded = self._load_guru_holdings(definition)
            quarter = str(loaded.get("quarter") or "")
        raw_rows = list(loaded.get("rows", []))
        holdings = [self._enrich_holding_row(definition, row) for row in raw_rows]
        return {
            "source": {
                "source_id": definition.source_id,
                "group_key": definition.group_key,
                "group_label": definition.group_label,
                "source_type": definition.source_type,
                "market_type": definition.market_type,
                "symbol": definition.symbol,
                "display_name": definition.display_name,
                "added_from": definition.added_from,
                "quarter": quarter,
                "as_of": str(loaded.get("as_of") or ""),
                "fetched_at": str(loaded.get("fetched_at") or datetime.now().isoformat()),
                "source_note": str(loaded.get("source_note") or definition.disclosure_hint),
            },
            "holdings": holdings,
        }

    def add_to_watchlist(self, chat_id: str, ticker: str, added_from: str) -> dict[str, object]:
        payload = {
            "telegram_chat_id": str(chat_id),
            "ticker": ticker.upper(),
            "added_from": added_from,
        }
        return self.watchlist_repository.upsert_entry(payload)

    def _resolve_disclosed_at(self, definition: HoldingsSourceDefinition) -> str:
        if definition.source_type == "guru":
            cached = self.guru_repository.fetch_latest_by_guru(definition.display_name)
            if cached and cached.get("disclosed_at"):
                return str(cached["disclosed_at"])
            fallback = DEFAULT_GURU_HOLDINGS.get(definition.source_id, {})
            return str(fallback.get("as_of") or "")
        return date.today().isoformat()

    def _load_etf_holdings(self, definition: HoldingsSourceDefinition) -> dict[str, object]:
        return {
            "as_of": date.today().isoformat(),
            "fetched_at": datetime.now().isoformat(),
            "rows": list(DEFAULT_ETF_HOLDINGS.get(definition.source_id, [])),
            "source_note": definition.disclosure_hint,
        }

    def _load_guru_holdings(self, definition: HoldingsSourceDefinition) -> dict[str, object]:
        cached = self.guru_repository.fetch_latest_by_guru(definition.display_name)
        if cached:
            return {
                "quarter": str(cached.get("quarter") or ""),
                "as_of": str(cached.get("disclosed_at") or ""),
                "fetched_at": str(cached.get("updated_at") or datetime.now().isoformat()),
                "rows": list(cached.get("holdings") or []),
                "source_note": definition.disclosure_hint,
            }
        fallback = DEFAULT_GURU_HOLDINGS.get(definition.source_id, {"quarter": "", "as_of": "", "rows": []})
        return {
            "quarter": str(fallback.get("quarter") or ""),
            "as_of": str(fallback.get("as_of") or ""),
            "fetched_at": datetime.now().isoformat(),
            "rows": list(fallback.get("rows") or []),
            "source_note": definition.disclosure_hint,
        }

    def _enrich_holding_row(self, definition: HoldingsSourceDefinition, row: dict[str, object]) -> dict[str, object]:
        ticker = str(row.get("ticker") or "").upper()
        profile = self.market_data.get_company_profile(ticker)
        growth = self._safe_growth_snapshot(ticker)
        analysis_row = self._latest_analysis_row(ticker)
        company = str(row.get("name") or profile.get("name_zh") or profile.get("name_en") or ticker).strip()
        sector = str(row.get("sector") or profile.get("sector") or "").strip()
        latest_price = analysis_row.get("close_price")
        if latest_price in (None, ""):
            latest_price = self._safe_latest_price(ticker)
        recommendation_bucket = analysis_row.get("recommendation_bucket") or "Watchlist"
        suggested_action = analysis_row.get("suggested_action") or "Run analysis to refresh details."
        if not analysis_row and latest_price is not None:
            suggested_action = "Price is live, but this holding has not entered the latest analysis set yet."
        return {
            "ticker": ticker,
            "company": company,
            "sector": sector,
            "weight": float(row.get("weight") or 0),
            "shares": row.get("shares"),
            "change": row.get("change") or "",
            "source_label": definition.display_name,
            "source_type": definition.source_type,
            "market_type": definition.market_type,
            "close_price": latest_price,
            "composite_signal_score": analysis_row.get("composite_signal_score"),
            "confluence_score": analysis_row.get("confluence_score"),
            "recommendation_bucket": recommendation_bucket,
            "institutional_buy_streak": analysis_row.get("institutional_buy_streak", 0),
            "relative_strength_score": analysis_row.get("relative_strength_score"),
            "suggested_action": suggested_action,
            "date": analysis_row.get("date"),
            "pe_ratio": growth.get("pe_ratio"),
            "pb_ratio": growth.get("pb_ratio"),
            "rev_yoy": growth.get("rev_yoy"),
            "eps_yoy": growth.get("eps_yoy"),
        }

    def _latest_analysis_row(self, ticker: str) -> dict[str, object]:
        history = self.analysis_repository.fetch_history(ticker, limit=1)
        return history[-1] if history else {}

    def _safe_latest_price(self, ticker: str) -> float | None:
        try:
            return float(self.market_data.get_latest_price(ticker))
        except Exception:
            pass
        for period in ("1mo", "6mo"):
            try:
                history = self.market_data.get_price_history(ticker, period=period)
                if history.empty:
                    continue
                close_series = history["Close"].dropna()
                if close_series.empty:
                    continue
                return float(close_series.iloc[-1])
            except Exception:
                continue
        return None

    def _safe_growth_snapshot(self, ticker: str) -> dict[str, object]:
        try:
            return dict(self.market_data.get_growth_snapshot(ticker))
        except Exception:
            return {}
