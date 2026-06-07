from __future__ import annotations

import os
import sys
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

LANG = "zh-TW"
ZH_DECISION_TEXT: dict[str, str] = {}

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def hydrate_env_from_streamlit_secrets() -> None:
    try:
        for key, value in st.secrets.items():
            if key not in os.environ:
                os.environ[key] = str(value)
    except Exception:
        return


hydrate_env_from_streamlit_secrets()
os.environ.setdefault("INVESTBOT_SUPABASE_ROLE", "frontend")

from investbot.config import get_settings
from investbot.data_sources.market_data import YahooMarketDataClient
from investbot.db.repositories import DailyAnalysisRepository, GuruPortfolioRepository, UserWatchlistRepository
from investbot.services.analysis_engine import AnalysisEngine, AnalysisRunSummary, AnalysisUniverse, analysis_summary_from_record
from investbot.services.dashboard_service import DashboardService, DashboardSnapshot
from investbot.services.decision_support import DecisionSupportService
from investbot.services.event_risk_service import EventRiskService
from investbot.services.holdings_library_service import HoldingsLibraryService
from investbot.services.holdings_library_service import merge_holdings_display_rows
from investbot.services.market_panorama_service import MarketPanoramaService
from investbot.services.market_overview_service import MarketOverview, MarketOverviewService
from investbot.services.portfolio_service import PortfolioService
from investbot.services.summary_service import SummaryService
from investbot.services.universe_builder import UniverseBuilder
from investbot.services.user_settings_service import UserSettingsService
try:
    from investbot.db.repositories import AppCacheRepository
except ImportError:
    AppCacheRepository = None  # type: ignore[assignment]

st.set_page_config(page_title="Smart Swing Agent", layout="wide", initial_sidebar_state="expanded")

settings = get_settings()
chat_id = settings.telegram_allowed_chat_id
user_settings_service = UserSettingsService()
runtime_settings = user_settings_service.get_runtime_namespace(chat_id)
LANG = str(getattr(runtime_settings, "app_language", getattr(settings, "app_language", "zh-TW")) or "zh-TW")
repo = DailyAnalysisRepository()
portfolio_service = PortfolioService()
market_data = YahooMarketDataClient()
dashboard_service = DashboardService(portfolio_service=portfolio_service, market_data=market_data)
decision_support = DecisionSupportService()
summary_service = SummaryService(repository=repo, decision_support=decision_support)
overview_service = MarketOverviewService(repository=repo, summary_service=summary_service, market_data=market_data)
watchlist_repository = UserWatchlistRepository()
guru_portfolio_repository = GuruPortfolioRepository()
app_cache_repository = AppCacheRepository() if AppCacheRepository is not None else None
holdings_library_service = HoldingsLibraryService(
    analysis_repository=repo,
    watchlist_repository=watchlist_repository,
    guru_repository=guru_portfolio_repository,
    market_data=market_data,
)
market_panorama_service = MarketPanoramaService()


BENCHMARK_SETS = {
    "tw": [
        ("^TWII", "taiex"),
        ("0050.TW", "taiwan50"),
        ("2330.TW", "tsmc_proxy"),
    ],
    "us": [
        ("^GSPC", "sp500"),
        ("^IXIC", "nasdaq"),
        ("^DJI", "dow"),
    ],
}

BENCHMARK_RANGE_OPTIONS = [
    ("1d", "today"),
    ("1mo", "one_month"),
    ("1y", "one_year"),
    ("3y", "three_year"),
    ("5y", "five_year"),
]


COPY = {
    "zh-TW": {
        "app_title": "Smart Swing Agent",
        "app_caption": "???????????????????????",
        "language": "??",
        "view": "??",
        "dashboard": "??",
        "portfolio": "??",
        "screener": "??",
        "health": "????",
        "run_analysis": "????",
        "run_tw": "??????",
        "run_us": "??????",
        "analysis_done": "????",
        "analysis_failed": "????",
        "analysis_progress": "????",
        "analysis_summary": "????",
        "analysis_options": "????",
        "force_refresh": "????????",
        "cooldown_skip": "??????????????????????????",
        "cooldown_force_hint": "???????????????????",
        "records": "????",
        "market_state": "????",
        "overall_trend": "????",
        "sentiment": "????",
        "fear_greed": "?? / ??",
        "fear_greed_gauge": "????",
        "breadth": "????",
        "momentum_zones": "????",
        "cautions": "??",
        "macro_calendar": "???????",
        "market_overview": "????",
        "market_terminal": "????",
        "benchmark_watch": "????",
        "dashboard_market_view": "????",
        "benchmark_range": "????",
        "today": "??",
        "one_month": "?",
        "one_year": "??",
        "three_year": "??",
        "five_year": "??",
        "benchmark_no_data": "?????????",
        "taiex": "????",
        "taiwan50": "??50",
        "tsmc_proxy": "???",
        "sp500": "??500",
        "nasdaq": "????",
        "dow": "??",
        "taiwan": "??",
        "us": "??",
        "candidates": "??",
        "actionable": "???",
        "safer": "????",
        "focus_lists": "????",
        "decision_cards": "???",
        "core_pool": "???",
        "explore_pool": "???",
        "watchlist": "????",
        "no_data": "??????????????",
        "vix": "VIX",
        "open_pnl": "?????",
        "win_rate": "??",
        "portfolio_curve": "????",
        "open_positions": "????",
        "no_positions": "???????",
        "no_closed_trades": "?????????????????????",
        "stop_buffer": "????",
        "market": "??",
        "bucket": "??",
        "all": "??",
        "min_score": "??????",
        "ticker": "??",
        "company": "??",
        "sector": "??",
        "price_trend": "????",
        "funnel_scores": "????",
        "suggested_action": "????",
        "rationale": "????",
        "risks": "????",
        "forward_score": "????",
        "forward_notes": "????",
        "win_label": "????",
        "risk_label": "????",
        "reward_risk": "???",
        "event_risk": "????",
        "next_event": "?????",
        "universe": "????",
        "score": "??",
        "signal_type": "??",
        "unknown": "??",
        "calm": "??",
        "neutral": "??",
        "risk_off": "??",
        "clear": "??",
        "vix_zone": "VIX ??",
        "vix_meaning": "VIX ??",
        "market_read": "????",
        "visual_scan": "????",
        "market_pulse": "????",
        "sector_heatmap": "????",
        "setup_distribution": "????",
        "breadth_lights": "????",
        "trend_mini": "????",
        "score_trend": "????",
        "session_brief": "????",
        "tw_brief": "????",
        "us_brief": "????",
        "rank_board": "???",
        "leader_board": "????",
        "risk_board": "????",
        "best_score": "????",
        "avg_score": "????",
        "market_bias": "????",
        "day1": "? 1 ?",
        "day2": "? 2 ?",
        "day3": "? 3 ?",
        "core_tab": "??",
        "explore_tab": "??",
        "risk_tab": "??",
        "why_tab": "??",
        "detail_tab": "??",
        "settings_panel": "????",
        "save_settings": "????",
        "settings_saved": "?????",
        "high_risk_dates": "???????",
    },
    "en": {
        "app_title": "Smart Swing Agent",
        "app_caption": "Start with market context, then capital flow and momentum, then single names.",
        "language": "Language",
        "view": "View",
        "dashboard": "Dashboard",
        "portfolio": "Portfolio",
        "screener": "Screener",
        "health": "Health",
        "run_analysis": "Run Analysis",
        "run_tw": "Run Taiwan Analysis",
        "run_us": "Run US Analysis",
        "analysis_done": "Analysis completed",
        "analysis_failed": "Analysis failed",
        "analysis_progress": "Analysis Progress",
        "analysis_summary": "Analysis Summary",
        "analysis_options": "Analysis Options",
        "force_refresh": "Force refresh history",
        "cooldown_skip": "Recent analysis exists, so the app reused it to avoid extra data pulls.",
        "cooldown_force_hint": "Use force refresh if you suspect providers have newer data.",
        "records": "Records written",
        "market_state": "Market State",
        "overall_trend": "Overall Trend",
        "sentiment": "Sentiment",
        "fear_greed": "Fear / Greed",
        "fear_greed_gauge": "Sentiment Gauge",
        "breadth": "Breadth",
        "momentum_zones": "Momentum Zones",
        "cautions": "Cautions",
        "macro_calendar": "Macro Calendar",
        "market_overview": "Market Overview",
        "market_terminal": "Market Terminal",
        "benchmark_watch": "Benchmark Watch",
        "dashboard_market_view": "Home Market",
        "benchmark_range": "Chart Range",
        "today": "Today",
        "one_month": "1M",
        "one_year": "1Y",
        "three_year": "3Y",
        "five_year": "5Y",
        "benchmark_no_data": "No data for this range.",
        "taiex": "TAIEX",
        "taiwan50": "Taiwan 50",
        "tsmc_proxy": "TSMC",
        "sp500": "S&P 500",
        "nasdaq": "Nasdaq",
        "dow": "Dow",
        "taiwan": "Taiwan",
        "us": "US",
        "candidates": "Candidates",
        "actionable": "Actionable",
        "safer": "Safer Follow-Through",
        "focus_lists": "Focus Lists",
        "decision_cards": "Decision Cards",
        "core_pool": "Core Pool",
        "explore_pool": "Explore Pool",
        "watchlist": "Watchlist",
        "no_data": "No data yet. Run an analysis first.",
        "vix": "VIX",
        "open_pnl": "Open PnL",
        "win_rate": "Win Rate",
        "portfolio_curve": "Portfolio Curve",
        "open_positions": "Open Positions",
        "no_positions": "No open positions.",
        "no_closed_trades": "No closed trades yet.",
        "stop_buffer": "Stop Buffer",
        "market": "Market",
        "bucket": "Bucket",
        "all": "All",
        "min_score": "Minimum Composite Score",
        "ticker": "Ticker",
        "company": "Company",
        "sector": "Sector",
        "price_trend": "Price Trend",
        "funnel_scores": "Funnel Scores",
        "suggested_action": "Suggested Action",
        "rationale": "Why It Ranks",
        "risks": "Main Risks",
        "forward_score": "Forward Score",
        "forward_notes": "Forward Factors",
        "win_label": "Win-Rate View",
        "risk_label": "Risk Level",
        "reward_risk": "Reward / Risk",
        "event_risk": "Event Risk",
        "next_event": "Next Event",
        "universe": "Universe",
        "score": "Score",
        "signal_type": "Signal",
        "unknown": "Unknown",
        "calm": "Calm",
        "neutral": "Neutral",
        "risk_off": "Risk-Off",
        "clear": "Clear",
        "vix_zone": "VIX Zone",
        "vix_meaning": "VIX Meaning",
        "market_read": "Market Read",
        "visual_scan": "Visual Scan",
        "market_pulse": "Market Pulse",
        "sector_heatmap": "Sector Heatmap",
        "setup_distribution": "Setup Distribution",
        "breadth_lights": "Market Lights",
        "trend_mini": "Mini Trend",
        "score_trend": "Score Rhythm",
        "session_brief": "Session Brief",
        "tw_brief": "Taiwan Brief",
        "us_brief": "US Brief",
        "rank_board": "Heat Board",
        "leader_board": "Leaders",
        "risk_board": "Risks",
        "best_score": "Best Score",
        "avg_score": "Average Score",
        "market_bias": "Market Bias",
        "day1": "Day 1 Early",
        "day2": "Day 2 Building",
        "day3": "Day 3+ Safer",
        "core_tab": "Core",
        "explore_tab": "Explore",
        "risk_tab": "Risk",
        "why_tab": "Why",
        "detail_tab": "Detail",
        "settings_panel": "Preferences",
        "save_settings": "Save Settings",
        "settings_saved": "Settings saved to database",
        "high_risk_dates": "Manual Fallback Event Dates",
    },
}

COPY["zh-TW"].update(
    {
        "benchmark_range": "????",
        "today": "??",
        "one_month": "?",
        "one_year": "??",
        "three_year": "??",
        "five_year": "??",
        "benchmark_no_data": "?????????",
    }
)

COPY["en"].update(
    {
        "benchmark_range": "Chart Range",
        "today": "Today",
        "one_month": "1M",
        "one_year": "1Y",
        "three_year": "3Y",
        "five_year": "5Y",
        "benchmark_no_data": "No data for this range.",
    }
)

COPY["en"].update(
    {
        "data_freshness": "Data Timing",
        "snapshot_as_of": "Snapshot Date",
        "data_window": "Data Window",
        "page_rendered_at": "Page Fetch Time",
        "latest_analysis_date": "Latest Analysis Date",
        "intraday_source_note": "If intraday data is unavailable, the app shows no data instead of silently widening the range.",
    }
)

COPY["zh-TW"].update(
    {
        "data_freshness": "????",
        "snapshot_as_of": "????",
        "data_window": "????",
        "page_rendered_at": "??????",
        "latest_analysis_date": "??????",
        "intraday_source_note": "????????????????????????????",
    }
)

COPY["zh-TW"].update(
    {
        "decision_score_label": "????",
        "decision_score_help": "80 ??????70-79 ?????60-69 ?????60 ???????",
        "decision_verdict": "??",
        "verdict_buy": "??",
        "verdict_probe": "???",
        "verdict_wait": "???",
        "verdict_avoid": "???",
        "leader_board_help": "????????????????????",
        "risk_board_help": "???????????????????????????",
        "trend_mini": "????",
        "score_trend": "????",
        "rank_board": "???",
        "leader_board": "????",
        "risk_board": "????",
        "market_pulse": "????",
        "sector_heatmap": "????",
        "setup_distribution": "????",
    }
)

LANG = str(globals().get("LANG") or "zh-TW")
ZH_DECISION_TEXT = globals().get("ZH_DECISION_TEXT", {})
if not isinstance(ZH_DECISION_TEXT, dict):
    ZH_DECISION_TEXT = {}
TEXT = COPY["zh-TW"] | COPY.get(LANG, {})

ZH_DECISION_TEXT.update(
    {
        "Institutional buying has just turned positive.": "????????",
        "Institutional buying is building into a second session.": "???????? 2 ??",
        "Institutional buying has persisted for 3 sessions.": "??????? 3 ??",
        "Institutional buying has persisted for 4 sessions.": "??????? 4 ??",
        "Institutional buying has persisted for 5 sessions.": "??????? 5 ??",
        "Relative strength is decisively above the market benchmark.": "?????????????",
        "Relative strength is supportive versus the benchmark.": "???????????",
        "Price location is constructive and not excessively extended.": "????????????",
        "Entry quality is acceptable if execution stays disciplined.": "??????????????",
        "The market regime is supportive for trend-following entries.": "???????????",
        "The broader market is neutral, so follow-through may be slower.": "????????????????",
        "The broader market is risk-off, so hit rates can fall quickly.": "?????????????????",
        "This idea is in the Explore pool, so it should not outrank core large-cap names.": "????????????????????",
        "This name belongs to the core monitoring pool.": "??????????",
        "Event risk is manageable but still worth monitoring.": "???????????????",
        "No major risk flags are active right now, but standard stop discipline still applies.": "?????????????????????",
        "The current signal does not yet have enough stacked evidence.": "????????????",
        "Normal position sizing or staged entries on minor pullbacks.": "??????????????????",
        "Pilot size first, then add if confirmation holds.": "????????????????",
        "Observe only until the odds improve.": "?????????????",
        "Small trial size only; keep core capital focused on large caps.": "????????????????????",
        "High Conviction Core": "?????",
        "Starter Size": "???",
        "Watchlist": "??",
        "Actionable": "???",
        "Candidate": "?????",
        "Dropped": "??",
    }
)



def _translate_macro_event_label(label: str) -> str:
    cleaned = str(label or "").strip().replace("_", " ").lower()
    if not cleaned:
        return ""
    if LANG != "zh-TW":
        return cleaned
    direct_map = {
        "cftc eur speculative net positions": "CFTC ???????",
        "cftc eur speculative net position": "CFTC ???????",
        "annual report": "????",
        "ecb cipollone speech": "ECB Cipollone ??",
        "ecb de guindos speech": "ECB De Guindos ??",
        "ecb survey of monetary analysts": "ECB ???????",
        "ecb survey of professional forecasters": "ECB ???????",
    }
    if cleaned in direct_map:
        return direct_map[cleaned]
    replacements = {
        "cftc": "CFTC",
        "eur": "??",
        "usd": "??",
        "jpy": "??",
        "gbp": "??",
        "speculative": "??",
        "net": "?",
        "position": "??",
        "positions": "??",
        "survey": "??",
        "speech": "??",
        "annual": "??",
        "report": "??",
        "earnings": "??",
        "inflation": "??",
        "payrolls": "????",
        "minutes": "????",
    }
    translated = cleaned
    for source, target in replacements.items():
        translated = translated.replace(source, target)
    return translated


def localize_value(value: object) -> str:
    text_value = str(value).strip()
    if not text_value:
        return text_value
    mapping = {
        "Unknown": "\u672a\u77e5" if LANG == "zh-TW" else "Unknown",
        "Calm": "\u5e73\u7a69" if LANG == "zh-TW" else "Calm",
        "Neutral": "\u4e2d\u6027" if LANG == "zh-TW" else "Neutral",
        "Risk-Off": "Risk-Off / \u9632\u79a6" if LANG == "zh-TW" else "Risk-Off",
        "Risk-On": "\u98a8\u96aa\u504f\u597d" if LANG == "zh-TW" else "Risk-On",
        "Risk-On Uptrend": "\u504f\u591a\u4e0a\u5347\u8da8\u52e2" if LANG == "zh-TW" else "Risk-On Uptrend",
        "Balanced / Selective": "\u5747\u8861 / \u9078\u64c7\u6027\u505a\u591a" if LANG == "zh-TW" else "Balanced / Selective",
        "Defensive / Risk-Off": "\u9632\u79a6 / Risk-Off" if LANG == "zh-TW" else "Defensive / Risk-Off",
        "Greed": "\u8caa\u5a6a" if LANG == "zh-TW" else "Greed",
        "Constructive": "\u7d50\u69cb\u5065\u5eb7" if LANG == "zh-TW" else "Constructive",
        "Cautious": "\u8b39\u614e" if LANG == "zh-TW" else "Cautious",
        "Fear": "\u6050\u61fc" if LANG == "zh-TW" else "Fear",
        "Watchlist": "\u89c0\u5bdf" if LANG == "zh-TW" else "Watchlist",
        "Actionable": "\u53ef\u57f7\u884c" if LANG == "zh-TW" else "Actionable",
        "Candidate": "\u5dee\u81e8\u9580\u4e00\u8173" if LANG == "zh-TW" else "Candidate",
        "Safer Follow-Through": "\u76f8\u5c0d\u5b89\u5168\u5ef6\u7e8c" if LANG == "zh-TW" else "Safer Follow-Through",
        "core": "\u6838\u5fc3\u6c60" if LANG == "zh-TW" else "Core",
        "explore": "\u89c0\u5bdf\u6c60" if LANG == "zh-TW" else "Explore",
        "clear": "\u76ee\u524d\u7121\u660e\u986f\u4e8b\u4ef6\u98a8\u96aa" if LANG == "zh-TW" else "clear",
        "DAY_1_EARLY": "\u7b2c 1 \u5929 / \u8d77\u6f32\u521d\u671f" if LANG == "zh-TW" else "Day 1 Early",
        "DAY_2_BUILDING": "\u7b2c 2 \u5929 / \u52d5\u80fd\u5efa\u7acb" if LANG == "zh-TW" else "Day 2 Building",
        "DAY_3_PLUS_SAFER": "\u7b2c 3 \u5929\u4ee5\u4e0a / \u76f8\u5c0d\u8f03\u5b89\u5168" if LANG == "zh-TW" else "Day 3+ Safer",
        "Institutional Accumulation": "\u6cd5\u4eba\u7d2f\u7a4d\u5438\u7c4c" if LANG == "zh-TW" else "Institutional Accumulation",
        "Panic Reversal": "\u6050\u614c\u53cd\u8f49" if LANG == "zh-TW" else "Panic Reversal",
        "High": "\u9ad8" if LANG == "zh-TW" else "High",
        "Medium": "\u4e2d" if LANG == "zh-TW" else "Medium",
        "Medium-High": "\u4e2d\u9ad8" if LANG == "zh-TW" else "Medium-High",
        "Medium-Low": "\u4e2d\u4f4e" if LANG == "zh-TW" else "Medium-Low",
        "Favorable": "\u6709\u5229" if LANG == "zh-TW" else "Favorable",
        "Balanced": "\u5747\u8861" if LANG == "zh-TW" else "Balanced",
        "Unclear": "\u4e0d\u660e\u78ba" if LANG == "zh-TW" else "Unclear",
        "High Conviction Core": "\u9ad8\u78ba\u4fe1\u6838\u5fc3" if LANG == "zh-TW" else "High Conviction Core",
        "Actionable Setup": "\u53ef\u57f7\u884c\u8a2d\u5b9a" if LANG == "zh-TW" else "Actionable Setup",
        "Watch and Wait": "\u5148\u89c0\u5bdf" if LANG == "zh-TW" else "Watch and Wait",
        "Consumer Electronics": "\u6d88\u8cbb\u96fb\u5b50" if LANG == "zh-TW" else "Consumer Electronics",
        "Software": "\u8edf\u9ad4" if LANG == "zh-TW" else "Software",
        "Semiconductors": "\u534a\u5c0e\u9ad4" if LANG == "zh-TW" else "Semiconductors",
        "Internet Retail": "\u7db2\u8def\u96f6\u552e" if LANG == "zh-TW" else "Internet Retail",
        "Internet Content & Information": "\u7db2\u8def\u5167\u5bb9\u8207\u8cc7\u8a0a" if LANG == "zh-TW" else "Internet Content & Information",
        "Entertainment": "\u5a1b\u6a02" if LANG == "zh-TW" else "Entertainment",
        "Auto Manufacturers": "\u6c7d\u8eca\u88fd\u9020" if LANG == "zh-TW" else "Auto Manufacturers",
        "ETF": "ETF",
        "Cloud Software": "\u96f2\u7aef\u8edf\u9ad4" if LANG == "zh-TW" else "Cloud Software",
        "AI Semiconductors": "AI \u534a\u5c0e\u9ad4" if LANG == "zh-TW" else "AI Semiconductors",
        "AI Software": "AI \u8edf\u9ad4" if LANG == "zh-TW" else "AI Software",
    }
    if text_value in mapping:
        return mapping[text_value]
    if text_value.startswith("macro_event_imminent:") or text_value.startswith("macro_event_near:"):
        prefix, label = text_value.split(":", 1)
        prefix_label = "\u91cd\u5927\u4e8b\u4ef6\u8fd1\u5728\u773c\u524d" if prefix == "macro_event_imminent" and LANG == "zh-TW" else "Macro imminent"
        if prefix == "macro_event_near":
            prefix_label = "\u91cd\u5927\u4e8b\u4ef6\u5373\u5c07\u903c\u8fd1" if LANG == "zh-TW" else "Macro near"
        return f"{prefix_label}: {_translate_macro_event_label(label)}"
    if LANG == "zh-TW" and text_value in ZH_DECISION_TEXT:
        return ZH_DECISION_TEXT[text_value]
    return text_value


def maybe_translate_text(text_value: str) -> str:
    if LANG != "zh-TW":
        return text_value
    if text_value.startswith("Institutional buying has persisted for ") and text_value.endswith(" sessions."):
        days = text_value.replace("Institutional buying has persisted for ", "").replace(" sessions.", "").strip()
        return f"\u6cd5\u4eba\u8cb7\u76e4\u5df2\u9023\u7e8c {days} \u5929\u3002"
    if text_value.startswith("Event risk is elevated:"):
        detail = text_value.replace("Event risk is elevated:", "").strip()
        return f"\u4e8b\u4ef6\u98a8\u96aa\u504f\u9ad8\uff1a{_translate_macro_event_label(detail)}"
    if text_value.startswith("macro_event_imminent ("):
        inner = text_value.replace("macro_event_imminent (", "").rstrip(")")
        return f"\u91cd\u5927\u4e8b\u4ef6\u8fd1\u5728\u773c\u524d\uff1a{_translate_macro_event_label(inner)}"
    if text_value.startswith("macro_event_near ("):
        inner = text_value.replace("macro_event_near (", "").rstrip(")")
        return f"\u91cd\u5927\u4e8b\u4ef6\u5373\u5c07\u903c\u8fd1\uff1a{_translate_macro_event_label(inner)}"
    if text_value.startswith("Volatility is elevated; position sizing should stay conservative."):
        return "\u6ce2\u52d5\u504f\u9ad8\uff0c\u90e8\u4f4d\u61c9\u4fdd\u6301\u4fdd\u5b88\u3002"
    if text_value.startswith("Breadth is weak, so single-name breakouts may fail more often."):
        return "\u5e02\u5834\u5ee3\u5ea6\u504f\u5f31\uff0c\u55ae\u6a94\u7a81\u7834\u5931\u6557\u7387\u6703\u8f03\u9ad8\u3002"
    if text_value.endswith(" names are carrying event-risk flags."):
        count = text_value.split(" ", 1)[0]
        return f"{count} \u6a94\u80a1\u7968\u5e36\u6709\u4e8b\u4ef6\u98a8\u96aa\u6a19\u8a18\u3002"
    if text_value.startswith("No major market-wide warnings are flashing right now."):
        return "\u76ee\u524d\u6c92\u6709\u5e02\u5834\u5c64\u7d1a\u7684\u91cd\u5927\u8b66\u8a0a\u3002"
    if text_value.startswith("Theme support:"):
        return text_value.replace("Theme support:", "\u4e3b\u984c\u652f\u6490\uff1a")
    if text_value.startswith("Institutional flow persistence supports the forward setup."):
        return "\u6cd5\u4eba\u8cc7\u91d1\u6d41\u7684\u6301\u7e8c\u6027\uff0c\u652f\u6490\u4e86\u524d\u77bb\u8a2d\u5b9a\u3002"
    if text_value.startswith("Relative strength confirms demand leadership."):
        return "\u76f8\u5c0d\u5f37\u5ea6\u78ba\u8a8d\u4e86\u9700\u6c42\u9818\u5148\u5730\u4f4d\u3002"
    if text_value.startswith("Forward demand narrative is strong enough for a starter position."):
        return "\u524d\u77bb\u9700\u6c42\u6574\u9ad4\u6578\u64da\u8db3\u4ee5\u652f\u6490\u5148\u884c\u8a66\u55ae\u3002"
    if " | " in text_value and len(text_value.split(" | ")) == 3:
        dt, region, title = text_value.split(" | ", 2)
        region_map = {"US": "\u7f8e\u570b", "EU": "\u6b50\u6d32", "JP": "\u65e5\u672c", "CN": "\u4e2d\u570b", "TW": "\u53f0\u7063"}
        return f"{dt} | {region_map.get(region, region)} | {_translate_macro_event_label(title)}"
    return ZH_DECISION_TEXT.get(text_value, text_value)



def build_market_pulse_chart(snapshot: Any, overview: Any, candidate_frame: pd.DataFrame) -> go.Figure:
    latest = _latest_candidates(candidate_frame)
    setup_quality = 50.0
    if not latest.empty and "composite_signal_score" in latest.columns:
        setup_quality = float(latest["composite_signal_score"].fillna(0).mean())
    pulse = pd.DataFrame(
        [
            {"metric": "VIX ???" if LANG == "zh-TW" else "VIX Comfort", "score": _vix_comfort_score(snapshot.vix)},
            {"metric": t("fear_greed"), "score": float(overview.fear_greed_score)},
            {"metric": t("breadth"), "score": float(overview.breadth_snapshot)},
            {"metric": "????" if LANG == "zh-TW" else "Setup Quality", "score": setup_quality},
        ]
    )
    pulse["color"] = pulse["score"].apply(
        lambda value: "#2fbf71" if value >= 75 else "#8bd36c" if value >= 60 else "#f6c84c" if value >= 45 else "#ff8a4c" if value >= 30 else "#ff5a6b"
    )
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=pulse["score"],
            y=pulse["metric"],
            orientation="h",
            marker_color=pulse["color"],
            text=[f"{value:.0f}/100" for value in pulse["score"]],
            textposition="inside",
            insidetextanchor="middle",
            hovertemplate="%{y}: %{x:.1f}/100<extra></extra>",
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=8, b=8),
        height=240,
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(range=[0, 100], showgrid=True, gridcolor="#edf2f7", zeroline=False, title=None),
        yaxis=dict(title=None, autorange="reversed"),
        showlegend=False,
    )
    return fig


def build_sector_heatmap(candidate_frame: pd.DataFrame) -> go.Figure:
    latest = _latest_candidates(candidate_frame)
    if latest.empty:
        fig = go.Figure()
        fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="white")
        return fig
    enriched = enrich_with_company_metadata(latest)
    grouped = (
        enriched.assign(
            market_label=enriched["type"].map(lambda value: t("taiwan") if value == "tw" else t("us")),
            sector_label=enriched["sector"].fillna(t("unknown")),
            score_value=enriched["composite_signal_score"].fillna(0).astype(float),
        )
        .groupby(["market_label", "sector_label"], as_index=False)
        .agg(avg_score=("score_value", "mean"), names=("ticker", "count"))
    )
    fig = px.treemap(
        grouped,
        path=["market_label", "sector_label"],
        values="names",
        color="avg_score",
        color_continuous_scale=["#ff6b7a", "#f6cf56", "#7bd88f", "#2fbf71"],
        range_color=(40, 85),
    )
    fig.update_traces(
        texttemplate="%{label}<br>%{value} 瑼?br>%{color:.0f}",
        hovertemplate="%{label}<br>" + ("瑼" if LANG == "zh-TW" else "Names") + ": %{value}<br>" + ("撟喳??" if LANG == "zh-TW" else "Avg Score") + ": %{color:.1f}<extra></extra>",
        root_color="white",
    )
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260, paper_bgcolor="white", coloraxis_showscale=False)
    return fig


def _display_name_for_row(row: pd.Series) -> tuple[str, str]:
    ticker = str(row.get("ticker", "")).upper()
    market_type = str(row.get("type", ""))
    profile = get_company_profile_cached(ticker)
    name_zh = str(profile.get("name_zh", "")).strip()
    name_en = str(profile.get("name_en", "")).strip()
    sector = str(profile.get("sector", "")).strip()
    fallback_sector = "?芰" if LANG == "zh-TW" else "Unknown"
    if market_type == "tw":
        return name_zh or name_en or ticker, sector or fallback_sector
    if LANG == "zh-TW":
        if name_en and name_zh:
            return f"{name_en} / {name_zh}", sector or fallback_sector
        return name_zh or name_en or ticker, sector or fallback_sector
    return name_en or name_zh or ticker, sector or fallback_sector


def _signal_tone(score: float) -> tuple[str, str]:
    if score >= 75:
        return ("#2fbf71", "??" if LANG == "zh-TW" else "Risk-on")
    if score >= 60:
        return ("#8bd36c", "????" if LANG == "zh-TW" else "Constructive")
    if score >= 45:
        return ("#f6c84c", "??" if LANG == "zh-TW" else "Neutral")
    if score >= 30:
        return ("#ff8a4c", "??" if LANG == "zh-TW" else "Weakening")
    return ("#ff5a6b", "??" if LANG == "zh-TW" else "Defensive")


def _market_bias_copy(summary: Any) -> str:
    if summary is None:
        return t("no_data")
    regime = localize_value(summary.regime)
    if LANG == "zh-TW":
        return f"{regime}??? {summary.candidate_count} ????? {summary.actionable_count} ???????? {summary.safer_count} ??"
    return f"{regime}, {summary.candidate_count} candidates, {summary.actionable_count} actionable, {summary.safer_count} safer follow-through names."


def render_visual_scan(candidate_frame: pd.DataFrame, snapshot: Any, overview: Any, market_key: str = "tw") -> None:
    st.markdown('<div class="section-label">????</div>', unsafe_allow_html=True)
    summary = summary_service.build_market_summary(market_key)
    st.caption(_market_bias_copy(summary))

    scan_tabs = st.tabs(["????", "????", "????", "??"])
    with scan_tabs[0]:
        st.plotly_chart(
            build_market_pulse_chart(snapshot, overview, candidate_frame),
            use_container_width=True,
            config={"displayModeBar": False},
            key=f"market_pulse_{market_key}"
        )
        light_cols = st.columns(4)
        lights = [
            (t("overall_trend"), localize_value(overview.overall_trend), _signal_tone(float(overview.fear_greed_score))[0], "????" if LANG == "zh-TW" else "Macro tape"),
            (t("sentiment"), localize_value(overview.sentiment_label), _signal_tone(float(overview.fear_greed_score))[0], "????" if LANG == "zh-TW" else "Risk appetite"),
            (t("fear_greed"), f"{float(overview.fear_greed_score):.0f}/100", _signal_tone(float(overview.fear_greed_score))[0], "????" if LANG == "zh-TW" else "Sentiment"),
            (t("breadth"), f"{float(overview.breadth_snapshot):.2f}", _signal_tone(float(overview.breadth_snapshot))[0], "?????" if LANG == "zh-TW" else "Participation"),
        ]
        for col, (label, value, tone, helper) in zip(light_cols, lights):
            col.markdown(
                f"""
                <div class="light-card">
                    <div class="light-card-label">{label}</div>
                    <div class="light-card-value">{value}</div>
                    <div class="light-card-copy" style="color:{tone};">{helper}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with scan_tabs[1]:
        st.plotly_chart(
            build_sector_heatmap(candidate_frame),
            use_container_width=True,
            config={"displayModeBar": False},
            key=f"sector_heatmap_{market_key}"
        )
    with scan_tabs[2]:
        st.plotly_chart(
            build_setup_distribution_chart(candidate_frame),
            use_container_width=True,
            config={"displayModeBar": False},
            key=f"setup_distribution_{market_key}"
        )
    with scan_tabs[3]:
        render_rank_boards(market_key)


def render_rank_boards(market_key: str | None = None) -> None:
    st.markdown('<div class="section-label">???</div>', unsafe_allow_html=True)
    st.caption(f"{market_key.upper() if market_key else 'ALL'} | {datetime.now().strftime('%Y-%m-%d')}")
    left, right = st.columns(2)
    summary_frame = load_latest_focus_frame(market_key) if market_key else load_candidate_frame()
    if summary_frame is None or summary_frame.empty:
        left.info("?????????????")
        right.info("?????????????")
        return

    working = summary_frame.copy()
    if market_key and "ticker" in working.columns:
        working = working[working["ticker"].astype(str).map(_market_key_for_ticker) == market_key]
    if working.empty:
        left.info("?????????????")
        right.info("?????????????")
        return

    leaders = working.sort_values("composite_signal_score", ascending=False).head(5)
    risk_candidates = working.sort_values(["event_risk_score", "composite_signal_score"], ascending=[False, True]) if "event_risk_score" in working.columns else working.sort_values("composite_signal_score", ascending=True)
    risk_rows = risk_candidates[~risk_candidates["ticker"].isin(leaders["ticker"])].head(5)

    with left:
        st.markdown('**????**')
        st.caption("????????????????????")
        for _, row in leaders.iterrows():
            name, sector = _display_name_for_row(row)
            score = float(row.get("composite_signal_score") or 0)
            st.markdown(f"**{name}**")
            st.caption(f"{row.get('ticker', '')} | {sector} | {localize_value(row.get('recommendation_bucket', ''))} | {score:.1f}")
    with right:
        st.markdown('**????**')
        st.caption("???????????????????????????")
        if risk_rows.empty:
            st.info("????????????????????")
        else:
            for _, row in risk_rows.iterrows():
                name, sector = _display_name_for_row(row)
                score = float(row.get("composite_signal_score") or 0)
                st.markdown(f"**{name}**")
                st.caption(f"{row.get('ticker', '')} | {sector} | {localize_value(row.get('recommendation_bucket', ''))} | {score:.1f}")


def render_terminal_table(frame: pd.DataFrame, columns: list[str]) -> None:
    if frame.empty:
        st.info(t("no_data"))
        return
    display = enrich_with_company_metadata(frame)
    for column in ["universe_bucket", "recommendation_bucket", "event_risk_note"]:
        if column in display.columns:
            display[column] = display[column].map(localize_value)
    if "suggested_action" in display.columns:
        display["suggested_action"] = display["suggested_action"].astype(str).map(maybe_translate_text)
    if "ticker" in display.columns:
        display["trend_mini"] = display["ticker"].astype(str).map(lambda ticker: _normalize_trend(get_ticker_trend_cached(ticker)))
        display["score_trend"] = display["ticker"].astype(str).map(lambda ticker: get_ticker_score_trend_cached(ticker))
    selected = [column for column in columns if column in display.columns]
    table = display[selected].copy()
    rename_map = {
        "ticker": t("ticker"),
        "company": t("company"),
        "sector": t("sector"),
        "trend_mini": t("trend_mini"),
        "score_trend": t("score_trend"),
        "recommendation_bucket": t("bucket"),
        "composite_signal_score": t("score"),
        "institutional_buy_streak": "\u6cd5\u4eba\u9023\u8cb7\u5929\u6578" if LANG == "zh-TW" else "Institutional Buy Streak",
        "risk_level": t("risk_label"),
        "event_risk_note": t("event_risk"),
        "next_event_date": t("next_event"),
        "suggested_action": t("suggested_action"),
    }
    table = table.rename(columns=rename_map)
    chart_config: dict[str, Any] = {}
    if t("trend_mini") in table.columns:
        chart_config[t("trend_mini")] = st.column_config.LineChartColumn(t("trend_mini"), width="medium", y_min=-12, y_max=12)
    if t("score_trend") in table.columns:
        chart_config[t("score_trend")] = st.column_config.LineChartColumn(t("score_trend"), width="medium", y_min=0, y_max=100)
    if t("score") in table.columns:
        chart_config[t("score")] = st.column_config.NumberColumn(t("score"), format="%.2f")
    streak_label = "\u6cd5\u4eba\u9023\u8cb7\u5929\u6578" if LANG == "zh-TW" else "Institutional Buy Streak"
    if streak_label in table.columns:
        chart_config[streak_label] = st.column_config.NumberColumn(streak_label, format="%d")
    if t("suggested_action") in table.columns:
        chart_config[t("suggested_action")] = st.column_config.TextColumn(t("suggested_action"), width="large")
    st.dataframe(table, use_container_width=True, hide_index=True, column_config=chart_config or None)

def render_decision_cards(candidate_frame: pd.DataFrame, market_key: str | None = None) -> None:
    st.markdown('<div class="section-label">???</div>', unsafe_allow_html=True)
    if candidate_frame is None or candidate_frame.empty:
        st.info("????????????")
        return

    working = candidate_frame.copy()
    if market_key and "ticker" in working.columns:
        working = working[working["ticker"].astype(str).map(_market_key_for_ticker) == market_key]
    if working.empty:
        st.info("??????????????")
        return

    bucket_cols = st.columns(4)
    bucket_counts = {
        "??": 0,
        "???": 0,
        "???": 0,
        "???": 0,
    }
    for _, row in working.iterrows():
        score = float(row.get("composite_signal_score") or 0)
        if score >= 80:
            bucket_counts["??"] += 1
        elif score >= 70:
            bucket_counts["???"] += 1
        elif score >= 60:
            bucket_counts["???"] += 1
        else:
            bucket_counts["???"] += 1
    for col, (label, value) in zip(bucket_cols, bucket_counts.items()):
        col.metric(label, value)

    for _, row in working.sort_values("composite_signal_score", ascending=False).head(8).iterrows():
        name, sector = _display_name_for_row(row)
        score = float(row.get("composite_signal_score") or 0)
        confluence_score = float(row.get("confluence_score") or 0)
        if score >= 80:
            verdict = "??"
        elif score >= 70:
            verdict = "???"
        elif score >= 60:
            verdict = "???"
        else:
            verdict = "???"
        suggested = maybe_translate_text(str(row.get("suggested_action") or "?????????????"))
        reasons = [
            maybe_translate_text(str(reason).strip())
            for reason in str(row.get("rationale") or "").split("|")
            if str(reason).strip()
        ]
        risks = [
            maybe_translate_text(str(reason).strip())
            for reason in str(row.get("risks") or "").split("|")
            if str(reason).strip()
        ]
        with st.expander(f"{row.get('ticker', '')} | {name} | {verdict} | {score:.1f}", expanded=False):
            st.markdown(f"**{name}**")
            st.caption(f"{row.get('ticker', '')} | ?? {sector} | ?? {localize_value(row.get('signal_type', ''))} | {localize_value(row.get('bucket', row.get('recommendation_bucket', '')))}")
            action_cols = st.columns(4)
            row_market_key = _market_key_for_ticker(str(row.get("ticker", "")))
            if action_cols[0].button("???", key=f"decision_favorite_{row.get('ticker', '')}", use_container_width=True):
                _mutate_market_management_list(row_market_key, str(row.get("ticker", "")), "favorite")
                st.toast(f"{row.get('ticker', '')} ?????")
                st.rerun()
            if action_cols[1].button("???", key=f"decision_watch_{row.get('ticker', '')}", use_container_width=True):
                _mutate_market_management_list(row_market_key, str(row.get("ticker", "")), "watch")
                st.toast(f"{row.get('ticker', '')} ?????")
                st.rerun()
            if action_cols[2].button("??", key=f"decision_exclude_{row.get('ticker', '')}", use_container_width=True):
                _mutate_market_management_list(row_market_key, str(row.get("ticker", "")), "exclude")
                st.toast(f"{row.get('ticker', '')} ?????")
                st.rerun()
            if action_cols[3].button("??", key=f"decision_clear_{row.get('ticker', '')}", use_container_width=True):
                _mutate_market_management_list(row_market_key, str(row.get("ticker", "")), "clear")
                st.toast(f"{row.get('ticker', '')} ???????")
                st.rerun()

            metric_cols = st.columns(5)
            metric_cols[0].metric("??", verdict)
            metric_cols[1].metric("????", f"{score:.1f}")
            metric_cols[2].metric("????", f"{confluence_score:.1f}" if confluence_score else "N/A")
            metric_cols[3].metric("????", f"{float(row.get('relative_strength_score') or 0):.1f}" if pd.notna(row.get("relative_strength_score")) else "N/A")
            metric_cols[4].metric("??????", str(int(row.get("institutional_buy_streak") or 0)))

            st.markdown("**????**")
            st.write(suggested)
            if reasons:
                st.markdown("**????**")
                for item in reasons:
                    st.markdown(f"- {item}")
            if risks:
                st.markdown("**????**")
                for item in risks:
                    st.markdown(f"- {item}")


def load_holdings_sources_cached() -> list[dict[str, object]]:
    return holdings_library_service.list_sources()


@st.cache_data(ttl=1800)
def load_holdings_snapshot_cached(source_id: str) -> dict[str, object]:
    return holdings_library_service.get_source_snapshot(source_id)


@st.cache_data(ttl=1800, show_spinner=False)
def get_live_ticker_trend_cached(ticker: str, limit: int = 12) -> list[float]:
    try:
        history = market_data.get_price_history(ticker, period="1mo", interval="1d")
    except Exception:
        return []
    if history.empty or "Close" not in history.columns:
        return []
    return history["Close"].dropna().astype(float).tolist()[-limit:]


def _market_key_for_ticker(ticker: str) -> str:
    normalized = str(ticker).upper()
    if normalized.endswith(".TW") or normalized.endswith(".TWO"):
        return "tw"
    return "us"


def _source_option_label(row: dict[str, object]) -> str:
    disclosed = str(row.get("last_disclosed_at") or "-")
    return f'{row.get("group_label", "")} | {row.get("display_name", "")} | {row.get("symbol", "")} | {disclosed}'


def _build_holdings_workbench_frame(snapshot: dict[str, object], candidate_frame: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = snapshot.get("holdings", []) or []
    if not rows:
        return pd.DataFrame()
    candidate_rows = candidate_frame.to_dict("records") if candidate_frame is not None and not candidate_frame.empty else []
    rows = merge_holdings_display_rows(list(rows), candidate_rows)
    frame = pd.DataFrame(rows).copy()
    if "ticker" in frame.columns:
        frame["ticker"] = frame["ticker"].astype(str).str.upper()
        frame["trend_mini"] = frame["ticker"].map(
            lambda value: _normalize_trend(get_ticker_trend_cached(str(value)) or get_live_ticker_trend_cached(str(value)))
        )
        frame["score_trend"] = frame["ticker"].map(lambda value: get_ticker_score_trend_cached(str(value)))
    for column in ["company", "sector", "change", "recommendation_bucket", "suggested_action", "source_label"]:
        if column not in frame.columns:
            frame[column] = ""
    for numeric_column in ["institutional_buy_streak", "close_price", "composite_signal_score", "relative_strength_score", "rev_yoy", "eps_yoy", "confluence_score", "weight"]:
        if numeric_column in frame.columns:
            frame[numeric_column] = pd.to_numeric(frame[numeric_column], errors="coerce")
    frame["data_state"] = frame.apply(
        lambda row: "ready"
        if pd.notna(row.get("close_price")) and pd.notna(row.get("composite_signal_score"))
        else ("live_only" if pd.notna(row.get("close_price")) else "missing"),
        axis=1,
    )
    frame["search_blob"] = (
        frame["ticker"].fillna("").astype(str)
        + " "
        + frame["company"].fillna("").astype(str)
        + " "
        + frame["sector"].fillna("").astype(str)
        + " "
        + frame["source_label"].fillna("").astype(str)
    ).str.lower()
    return frame


def _render_holdings_donut(frame: pd.DataFrame, source_name: str, chart_key: str) -> None:
    if frame.empty or "weight" not in frame.columns:
        st.info("???????????????" if LANG == "zh-TW" else "No holding weights available.")
        return
    weight_frame = frame[["company", "weight"]].copy().sort_values("weight", ascending=False)
    top = weight_frame.head(8).copy()
    others_weight = float(weight_frame["weight"].iloc[8:].sum()) if len(weight_frame) > 8 else 0.0
    if others_weight > 0:
        top.loc[len(top)] = {"company": "Others", "weight": others_weight}
    figure = px.pie(top, names="company", values="weight", hole=0.58)
    figure.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="left", x=0),
        annotations=[dict(text=source_name, x=0.5, y=0.5, showarrow=False, font=dict(size=13, color="#243047"))],
    )
    figure.update_traces(texttemplate="%{percent}", hovertemplate="%{label}<br>%{value:.2f}%<extra></extra>")
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False}, key=chart_key)


def _format_holdings_pending_text(state: str) -> str:
    return "\u50c5\u6709\u5373\u6642\u50f9" if state == "live_only" else "\u5f85\u5206\u6790"


def _clear_holdings_related_caches() -> None:
    for func in (
        load_holdings_snapshot_cached,
        get_live_ticker_trend_cached,
        load_holdings_sources_cached,
        load_candidate_frame,
        load_latest_focus_frame,
        load_dashboard_snapshot_cached,
        load_market_overview_cached,
    ):
        clear = getattr(func, "clear", None)
        if callable(clear):
            clear()


def _run_holdings_source_analysis(snapshot: dict[str, object], market_key: str) -> AnalysisRunSummary | None:
    source_meta = snapshot.get("source", {}) or {}
    source_label = str(source_meta.get("display_name") or source_meta.get("symbol") or "\u6301\u80a1\u4f86\u6e90")
    tickers = [
        str(row.get("ticker") or "").upper()
        for row in (snapshot.get("holdings") or [])
        if str(row.get("ticker") or "").strip()
    ]
    tickers = [ticker for ticker in tickers if _market_key_for_ticker(ticker) == market_key]
    deduped: list[str] = []
    for ticker in tickers:
        if ticker not in deduped:
            deduped.append(ticker)
    if not deduped:
        _set_analysis_feedback("warning", "\u9019\u500b\u4f86\u6e90\u76ee\u524d\u6c92\u6709\u53ef\u4ee5\u5206\u6790\u7684\u6301\u80a1\u3002")
        return None

    engine = AnalysisEngine(market_data=market_data, repository=daily_analysis_repo)
    progress_box = st.empty()

    def _progress(stage: str, current: int, total: int, message: str) -> None:
        total_safe = max(total, 1)
        progress_box.info(f"{message} ({min(current, total_safe)}/{total_safe})")

    with st.spinner(f"\u6b63\u5728\u5206\u6790 {source_label} \u7684\u6301\u80a1..."):
        summary = engine.run_with_summary(
            AnalysisUniverse(market_type=market_key, core_tickers=deduped, explore_tickers=[]),
            progress_callback=_progress,
        )
    progress_box.empty()
    st.session_state["analysis_summary"] = summary
    st.session_state["analysis_summary_at"] = datetime.now().isoformat(timespec="seconds")
    _clear_holdings_related_caches()
    _set_analysis_feedback(
        "success",
        (
            f"{source_label} \u5206\u6790\u5b8c\u6210 | \u6383\u63cf {summary.scanned_tickers} \u6a94 | "
            f"\u6709\u8cc7\u6599 {summary.data_ready_tickers} \u6a94 | \u5beb\u5165 {summary.signal_count} \u7b46"
        ),
    )
    return summary


def _render_tradingview_widget(widget_name: str, config: dict[str, object], height: int, key: str) -> None:
    payload = json.dumps(config, ensure_ascii=False)
    html = f"""
    <div class="tradingview-widget-container" style="width:100%;height:{height}px;">
      <div id="{key}" style="width:100%;height:{height}px;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-{widget_name}.js" async>
      {payload}
      </script>
    </div>
    """
    components.html(html, height=height + 8)


def render_market_panorama() -> None:
    st.markdown('<div class="page-title">\u5e02\u5834\u5168\u666f</div>', unsafe_allow_html=True)
    st.caption("\u7528\u7368\u7acb\u5206\u9801\u770b\u5168\u7403\u6307\u6578\u3001\u677f\u584a\u71b1\u5340\u8207\u4e3b\u984c\u6a19\u7684\uff0c\u907f\u514d\u62d6\u6162\u539f\u672c\u7b56\u7565\u9801\u9762\u3002")

    market_key = st.radio(
        "\u5e02\u5834",
        options=["tw", "us"],
        format_func=lambda value: "\u53f0\u80a1" if value == "tw" else "\u7f8e\u80a1",
        index=0,
        horizontal=True,
        key="panorama_market_selector",
    ) or "tw"
    config = market_panorama_service.get_config(str(market_key))

    _render_data_caption("\u8cc7\u6599\u4f86\u6e90\uff1aTradingView Widgets\uff08\u7528\u65bc\u5e02\u5834\u6982\u89bd\uff0c\u975e\u5f8c\u7aef\u7b56\u7565\u8a55\u5206\u4f9d\u64da\uff09")
    _render_tradingview_widget("ticker-tape", config["ticker_tape"], 84, f"panorama_ticker_tape_{market_key}")

    left, right = st.columns((1.7, 1))
    with left:
        st.markdown('<div class="section-label">\u5168\u5c40\u5e02\u5834\u6982\u89bd</div>', unsafe_allow_html=True)
        _render_tradingview_widget("market-overview", config["market_overview"], 540, f"panorama_market_overview_{market_key}")
    with right:
        st.markdown('<div class="section-label">\u91cd\u9ede\u8d70\u52e2</div>', unsafe_allow_html=True)
        _render_tradingview_widget("symbol-overview", config["symbol_overview"], 440, f"panorama_symbol_overview_{market_key}")
        st.markdown('<div class="section-label">\u4e3b\u984c\u89c0\u5bdf</div>', unsafe_allow_html=True)
        for card in config["theme_cards"]:
            st.markdown(
                f"""
                <div class="summary-band" style="margin-bottom:12px;">
                    <div class="summary-band-title">{card["title"]}</div>
                    <div class="summary-band-copy">{card["focus"]}</div>
                    <div class="summary-band-copy">{' / '.join(card["tags"])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            for symbol in card["symbols"]:
                ticker = str(symbol["ticker"])
                label = str(symbol["label"])
                row_market_key = _market_key_for_ticker(ticker)
                action_cols = st.columns((2.2, 0.9, 0.9))
                action_cols[0].markdown(f"**{ticker} | {label}**")
                if action_cols[1].button("\u52a0\u6700\u611b", key=f"panorama_favorite_{market_key}_{card['title']}_{ticker}", use_container_width=True):
                    _mutate_market_management_list(row_market_key, ticker, "favorite")
                    holdings_library_service.add_to_watchlist(chat_id, ticker, f"Panorama {card['title']}")
                    st.toast(f"{ticker} \u5df2\u52a0\u5165\u6700\u611b")
                if action_cols[2].button("\u52a0\u89c0\u5bdf", key=f"panorama_watch_{market_key}_{card['title']}_{ticker}", use_container_width=True):
                    _mutate_market_management_list(row_market_key, ticker, "watch")
                    holdings_library_service.add_to_watchlist(chat_id, ticker, f"Panorama {card['title']}")
                    st.toast(f"{ticker} \u5df2\u52a0\u5165\u89c0\u5bdf")

    st.markdown('<div class="section-label">\u985e\u80a1\u71b1\u5340</div>', unsafe_allow_html=True)
    _render_tradingview_widget("stock-heatmap", config["heatmap"], 580, f"panorama_heatmap_{market_key}")


def render_holdings_library(candidate_frame: pd.DataFrame, market_key: str) -> None:
    st.markdown('<div class="section-label">\u6301\u80a1\u4f86\u6e90\u5eab</div>', unsafe_allow_html=True)
    st.caption("\u628a ETF \u8207 13F \u6301\u80a1\u7576\u6210\u4f86\u6e90\u6e05\u55ae\u4f86\u770b\uff0c\u4f60\u53ef\u4ee5\u5728\u9019\u88e1\u76f4\u63a5\u641c\u5c0b\u3001\u6392\u5e8f\uff0c\u4e26\u52a0\u5165\u6700\u611b\u3001\u89c0\u5bdf\u6216\u5254\u9664\u3002")

    source_rows = load_holdings_sources_cached()
    source_frame = pd.DataFrame(source_rows)
    if source_frame.empty:
        st.info("\u76ee\u524d\u6c92\u6709\u53ef\u7528\u7684\u6301\u80a1\u4f86\u6e90\u3002")
        return

    preferred_groups = {"tw_etf", "guru_13f"} if market_key == "tw" else {"us_etf", "guru_13f"}
    preferred = source_frame[source_frame["group_key"].isin(preferred_groups)].copy()
    if preferred.empty:
        preferred = source_frame.copy()

    source_search = st.text_input(
        "\u641c\u5c0b\u4f86\u6e90",
        placeholder="0050 / Berkshire / QQQ",
        key=f"holdings_source_search_{market_key}",
    ).strip().lower()
    if source_search:
        preferred = preferred[(preferred["display_name"].fillna("").astype(str) + " " + preferred["symbol"].fillna("").astype(str) + " " + preferred["group_label"].fillna("").astype(str)).str.lower().str.contains(source_search, na=False)]

    source_options = preferred.to_dict("records")
    if not source_options:
        st.info("\u6c92\u6709\u7b26\u5408\u641c\u5c0b\u689d\u4ef6\u7684\u4f86\u6e90\u3002")
        return

    default_source_id = st.session_state.get(f"holdings_source_selected_{market_key}")
    option_ids = [str(row["source_id"]) for row in source_options]
    default_index = option_ids.index(default_source_id) if default_source_id in option_ids else 0
    selected_source_id = st.selectbox(
        "\u9078\u64c7\u4f86\u6e90",
        options=option_ids,
        index=default_index,
        format_func=lambda value: _source_option_label(next(row for row in source_options if row["source_id"] == value)),
        key=f"holdings_source_picker_{market_key}",
    )
    st.session_state[f"holdings_source_selected_{market_key}"] = selected_source_id

    snapshot = load_holdings_snapshot_cached(selected_source_id)
    source_meta = snapshot.get("source", {})
    frame = _build_holdings_workbench_frame(snapshot, candidate_frame)

    top_left, top_right = st.columns((1.55, 1))
    with top_left:
        st.markdown(
            f"""
            <div class="summary-band">
                <div>
                    <div class="summary-band-title">{source_meta.get("display_name", "")} ({source_meta.get("symbol", "")})</div>
                    <div class="summary-band-copy">{source_meta.get("source_note", "")}</div>
                    <div class="summary-band-copy">\u6700\u5f8c\u63ed\u9732\uff1a{source_meta.get("as_of", "-")} | \u64f7\u53d6\u6642\u9593\uff1a{source_meta.get("fetched_at", "-")}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        action_bar = st.columns((1.1, 1.1, 1.4))
        if action_bar[0].button("\u5206\u6790\u9019\u500b\u4f86\u6e90\u6301\u80a1", key=f"holdings_analyze_source_{selected_source_id}", use_container_width=True):
            summary = _run_holdings_source_analysis(snapshot, market_key)
            if summary is not None:
                st.rerun()
        if action_bar[1].button("\u91cd\u65b0\u6574\u7406\u9019\u500b\u4f86\u6e90", key=f"holdings_refresh_source_{selected_source_id}", use_container_width=True):
            load_holdings_snapshot_cached.clear()
            get_live_ticker_trend_cached.clear()
            st.toast(f"{source_meta.get('display_name', '')} \u5df2\u91cd\u65b0\u8f09\u5165")
            st.rerun()
        action_bar[2].caption("\u5148\u986f\u793a\u76ee\u524d\u5feb\u7167\uff0c\u9700\u8981\u6642\u518d\u88dc\u8dd1\u9019\u500b\u4f86\u6e90\u7684\u5b8c\u6574\u5206\u6790\u3002")
        summary_cols = st.columns(4)
        summary_cols[0].metric("\u6301\u80a1\u6a94\u6578", len(frame))
        summary_cols[1].metric("Top 1 \u4f54\u6bd4", f'{float(frame["weight"].max()):.2f}%' if not frame.empty and "weight" in frame else "0.00%")
        summary_cols[2].metric("Top 5 \u4f54\u6bd4", f'{float(frame["weight"].nlargest(min(5, len(frame))).sum()):.2f}%' if not frame.empty and "weight" in frame else "0.00%")
        summary_cols[3].metric("\u53ef\u8ffd\u8e64\u6a19\u7684", int(frame["ticker"].nunique()) if "ticker" in frame.columns else 0)
    with top_right:
        _render_holdings_donut(frame, str(source_meta.get("symbol") or source_meta.get("display_name") or ""), f"holdings_donut_{selected_source_id}")

    if frame.empty:
        st.info("\u9019\u500b\u4f86\u6e90\u76ee\u524d\u6c92\u6709\u53ef\u986f\u793a\u7684\u6301\u80a1\u3002")
        return

    filter_cols = st.columns((1.1, 1.1, 1.1, 1.2))
    holding_search = filter_cols[0].text_input("\u641c\u5c0b\u500b\u80a1", placeholder="2330 / \u53f0\u7a4d\u96fb / \u534a\u5c0e\u9ad4", key=f"holdings_item_search_{market_key}_{selected_source_id}").strip().lower()
    only_favorite = filter_cols[1].checkbox("\u53ea\u770b\u6700\u611b", key=f"holdings_only_favorite_{market_key}_{selected_source_id}")
    only_watch = filter_cols[2].checkbox("\u53ea\u770b\u89c0\u5bdf", key=f"holdings_only_watch_{market_key}_{selected_source_id}")
    min_score = filter_cols[3].slider("\u6700\u4f4e\u7d9c\u5408\u5206\u6578", 0, 100, 0, key=f"holdings_min_score_{market_key}_{selected_source_id}")

    management_state = _read_market_management_lists(market_key)
    working = frame.copy()
    working["favorite_flag"] = working["ticker"].isin(management_state["favorite"])
    working["watch_flag"] = working["ticker"].isin(management_state["watch"])
    working["exclude_flag"] = working["ticker"].isin(management_state["exclude"])
    if holding_search:
        working = working[working["search_blob"].str.contains(holding_search, na=False)]
    if only_favorite:
        working = working[working["favorite_flag"]]
    if only_watch:
        working = working[working["watch_flag"]]
    if "composite_signal_score" in working.columns:
        working = working[(working["composite_signal_score"].fillna(0).astype(float)) >= float(min_score)]

    left, right = st.columns((1.6, 1))
    with left:
        display = working[["ticker", "company", "sector", "weight", "change", "close_price", "data_state", "trend_mini", "score_trend", "composite_signal_score", "recommendation_bucket", "favorite_flag", "watch_flag"]].copy()
        display["favorite_flag"] = display["favorite_flag"].map(lambda flag: "Yes" if flag else "")
        display["watch_flag"] = display["watch_flag"].map(lambda flag: "Yes" if flag else "")
        display["change"] = display["change"].map(lambda value: value if str(value).strip() else "-")
        display["close_price"] = display.apply(lambda row: row["close_price"] if pd.notna(row.get("close_price")) else _format_holdings_pending_text(str(row.get("data_state") or "missing")), axis=1)
        display["recommendation_bucket"] = display["recommendation_bucket"].map(lambda value: localize_value(value) if str(value).strip() else "\u5f85\u5206\u6790")
        display["data_state"] = display["data_state"].map({"ready": "\u5df2\u88dc\u9f4a", "live_only": "\u50c5\u6709\u50f9\u683c", "missing": "\u5f85\u5206\u6790"})
        display = display.rename(columns={"ticker": "\u4ee3\u865f", "company": "\u516c\u53f8", "sector": "\u985e\u80a1", "weight": "\u6301\u80a1\u6bd4\u4f8b(%)", "change": "\u589e\u6e1b\u6301", "close_price": "\u6700\u65b0\u80a1\u50f9", "data_state": "\u8cc7\u6599\u72c0\u614b", "trend_mini": "\u77ed\u7dda\u8d70\u52e2", "score_trend": "\u5206\u6578\u7bc0\u594f", "composite_signal_score": "\u7d9c\u5408\u5206\u6578", "recommendation_bucket": "\u63a8\u85a6\u5206\u7d44", "favorite_flag": "\u6700\u611b", "watch_flag": "\u89c0\u5bdf"})
        st.dataframe(display, use_container_width=True, hide_index=True, column_config={"\u6301\u80a1\u6bd4\u4f8b(%)": st.column_config.NumberColumn("\u6301\u80a1\u6bd4\u4f8b(%)", format="%.2f"), "\u7d9c\u5408\u5206\u6578": st.column_config.NumberColumn("\u7d9c\u5408\u5206\u6578", format="%.2f"), "\u77ed\u7dda\u8d70\u52e2": st.column_config.LineChartColumn("\u77ed\u7dda\u8d70\u52e2", width="medium", y_min=-12, y_max=12), "\u5206\u6578\u7bc0\u594f": st.column_config.LineChartColumn("\u5206\u6578\u7bc0\u594f", width="medium", y_min=0, y_max=100)})
        st.markdown('<div class="section-label">\u5217\u8868\u5feb\u6377\u64cd\u4f5c</div>', unsafe_allow_html=True)
        st.caption("\u76f4\u63a5\u5728\u9019\u88e1\u628a\u4f86\u6e90\u6301\u80a1\u52a0\u5165\u6700\u611b\u3001\u89c0\u5bdf\u6216\u5254\u9664\uff0c\u4e0d\u7528\u6bcf\u6b21\u90fd\u5207\u5230\u53f3\u5074\u7d30\u7bc0\u3002")
        for idx, row in working.head(12).reset_index(drop=True).iterrows():
            row_market_key = _market_key_for_ticker(str(row["ticker"]))
            action_cols = st.columns((2.2, 1.1, 0.8, 0.8, 0.8))
            action_cols[0].markdown(f'**{_ticker_option_label(str(row["ticker"]), row_market_key)}**')
            row_score = float(row["composite_signal_score"]) if pd.notna(row.get("composite_signal_score")) else None
            action_cols[1].caption(f'\u6301\u80a1\u6bd4\u4f8b {float(row.get("weight") or 0):.2f}% | \u5206\u6578 {row_score:.2f}' if row_score is not None else f'\u6301\u80a1\u6bd4\u4f8b {float(row.get("weight") or 0):.2f}% | {_format_holdings_pending_text(str(row.get("data_state") or "missing"))}')
            if action_cols[2].button("\u52a0\u6700\u611b", key=f"holdings_row_fav_{selected_source_id}_{idx}", use_container_width=True):
                _mutate_market_management_list(row_market_key, str(row["ticker"]), "favorite")
                holdings_library_service.add_to_watchlist(chat_id, str(row["ticker"]), str(source_meta.get("display_name") or source_meta.get("added_from") or "Manual"))
                st.toast(f'{row["ticker"]} \u5df2\u52a0\u5165\u6700\u611b')
                st.rerun()
            if action_cols[3].button("\u52a0\u89c0\u5bdf", key=f"holdings_row_watch_{selected_source_id}_{idx}", use_container_width=True):
                _mutate_market_management_list(row_market_key, str(row["ticker"]), "watch")
                holdings_library_service.add_to_watchlist(chat_id, str(row["ticker"]), str(source_meta.get("display_name") or source_meta.get("added_from") or "Manual"))
                st.toast(f'{row["ticker"]} \u5df2\u52a0\u5165\u89c0\u5bdf')
                st.rerun()
            if action_cols[4].button("\u5254\u9664", key=f"holdings_row_exclude_{selected_source_id}_{idx}", use_container_width=True):
                _mutate_market_management_list(row_market_key, str(row["ticker"]), "exclude")
                st.toast(f'{row["ticker"]} \u5df2\u52a0\u5165\u5254\u9664')
                st.rerun()
    with right:
        selected_ticker_options = working["ticker"].dropna().astype(str).tolist()
        if not selected_ticker_options:
            st.info("\u6c92\u6709\u7b26\u5408\u7be9\u9078\u689d\u4ef6\u7684\u6301\u80a1\u3002")
            return
        selected_ticker = st.selectbox("\u500b\u80a1\u901f\u89bd", options=selected_ticker_options, format_func=lambda value: _ticker_option_label(value, _market_key_for_ticker(value)), key=f"holdings_detail_pick_{market_key}_{selected_source_id}")
        detail_row = working[working["ticker"] == selected_ticker].head(1)
        if not detail_row.empty:
            row = detail_row.iloc[0]
            st.markdown(f'**{row["company"]}**')
            st.caption(f'{row["ticker"]} | {row["sector"]} | \u6301\u80a1\u6bd4\u4f8b {float(row.get("weight") or 0):.2f}%')
            metrics = st.columns(2)
            metrics[0].metric("\u6700\u65b0\u80a1\u50f9", f'{float(row["close_price"]):.2f}' if pd.notna(row.get("close_price")) else _format_holdings_pending_text(str(row.get("data_state") or "missing")))
            metrics[1].metric("\u7d9c\u5408\u5206\u6578", f'{float(row["composite_signal_score"]):.2f}' if pd.notna(row.get("composite_signal_score")) else _format_holdings_pending_text(str(row.get("data_state") or "missing")))
            metrics2 = st.columns(2)
            metrics2[0].metric("\u63a8\u85a6\u5206\u7d1a", localize_value(row.get("recommendation_bucket", "")) or "\u5f85\u5206\u6790")
            metrics2[1].metric("\u6cd5\u4eba\u9023\u8cb7\u5929\u6578", str(int(row["institutional_buy_streak"])) if pd.notna(row.get("institutional_buy_streak")) else "N/A")
            metrics3 = st.columns(3)
            metrics3[0].metric("\u76f8\u5c0d\u5f37\u5ea6", f'{float(row["relative_strength_score"]):.2f}' if pd.notna(row.get("relative_strength_score")) else "N/A")
            metrics3[1].metric("\u71df\u6536 YoY", f'{float(row["rev_yoy"]):.1f}%' if pd.notna(row.get("rev_yoy")) else "N/A")
            metrics3[2].metric("EPS YoY", f'{float(row["eps_yoy"]):.1f}%' if pd.notna(row.get("eps_yoy")) else "N/A")
            if str(row.get("data_state") or "") == "live_only":
                st.info("\u9019\u6a94\u76ee\u524d\u5df2\u88dc\u56de\u5373\u6642\u50f9\uff0c\u4f46\u9084\u6c92\u6709\u6700\u65b0\u7b56\u7565\u5206\u6790\u7d50\u679c\u3002")
            elif str(row.get("data_state") or "") == "missing":
                st.warning("\u9019\u6a94\u9084\u6c92\u6709\u5206\u6790\u7d50\u679c\uff0c\u8acb\u5148\u57f7\u884c\u5206\u6790\u4ee5\u5237\u65b0\u8a73\u7d30\u8cc7\u6599\u3002")
            if row.get("suggested_action"):
                st.caption(f'\u5efa\u8b70\uff1a{maybe_translate_text(str(row.get("suggested_action")))}')
            action_cols = st.columns(2)
            row_market_key = _market_key_for_ticker(str(row["ticker"]))
            if action_cols[0].button("\u52a0\u6700\u611b", key=f"holdings_add_favorite_{selected_source_id}_{selected_ticker}", use_container_width=True):
                _mutate_market_management_list(row_market_key, selected_ticker, "favorite")
                holdings_library_service.add_to_watchlist(chat_id, selected_ticker, str(source_meta.get("display_name") or source_meta.get("added_from") or "Manual"))
                st.toast(f"{selected_ticker} \u5df2\u52a0\u5165\u6700\u611b")
                st.rerun()
            if action_cols[1].button("\u52a0\u89c0\u5bdf", key=f"holdings_add_watch_{selected_source_id}_{selected_ticker}", use_container_width=True):
                _mutate_market_management_list(row_market_key, selected_ticker, "watch")
                holdings_library_service.add_to_watchlist(chat_id, selected_ticker, str(source_meta.get("display_name") or source_meta.get("added_from") or "Manual"))
                st.toast(f"{selected_ticker} \u5df2\u52a0\u5165\u89c0\u5bdf")
                st.rerun()
            st.caption(f'\u6700\u5f8c\u63ed\u9732\u6642\u9593\uff1a{source_meta.get("as_of", "-")}')
            st.caption(f'\u4f86\u6e90\u6a19\u8a3b\uff1a{source_meta.get("added_from", "-")}')


daily_analysis_repo = repo


def t(key: str) -> str:
    return str(TEXT.get(key, key))


def _set_analysis_feedback(level: str, message: str) -> None:
    st.session_state["analysis_feedback"] = {"level": level, "message": message}


def render_analysis_feedback() -> None:
    feedback = st.session_state.get("analysis_feedback")
    if not feedback:
        return
    level = str(feedback.get("level", "info"))
    message = str(feedback.get("message", ""))
    if not message:
        return
    if level == "success":
        st.success(message)
    elif level == "warning":
        st.warning(message)
    elif level == "error":
        st.error(message)
    else:
        st.info(message)


def _latest_candidates(candidate_frame: pd.DataFrame) -> pd.DataFrame:
    if candidate_frame is None or candidate_frame.empty:
        return pd.DataFrame()
    frame = candidate_frame.copy()
    if "date" in frame.columns:
        frame = frame[frame["date"] == frame["date"].max()].copy()
    return frame


def _vix_comfort_score(vix: float | None) -> float:
    if vix is None:
        return 55.0
    return max(0.0, min(100.0, 100.0 - (float(vix) - 12.0) * 4.0))


@st.cache_data(ttl=1800)
def get_company_profile_cached(ticker: str) -> dict[str, object]:
    return market_data.get_company_profile(ticker)


def enrich_with_company_metadata(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    enriched = frame.copy()
    for column in ["company", "sector"]:
        if column not in enriched.columns:
            enriched[column] = ""
    for idx, row in enriched.iterrows():
        ticker = str(row.get("ticker") or "").upper()
        if not ticker:
            continue
        if not str(enriched.at[idx, "company"] or "").strip() or not str(enriched.at[idx, "sector"] or "").strip():
            profile = get_company_profile_cached(ticker)
            if not str(enriched.at[idx, "company"] or "").strip():
                enriched.at[idx, "company"] = profile.get("company") or ticker
            if not str(enriched.at[idx, "sector"] or "").strip():
                enriched.at[idx, "sector"] = profile.get("sector") or ("Taiwan" if ticker.endswith(".TW") else "US")
    return enriched


def build_setup_distribution_chart(candidate_frame: pd.DataFrame) -> go.Figure:
    latest = _latest_candidates(candidate_frame)
    if latest.empty or "recommendation_bucket" not in latest.columns:
        return go.Figure().update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10))
    counts = latest["recommendation_bucket"].fillna("Unknown").value_counts().reset_index()
    counts.columns = ["bucket", "count"]
    fig = px.bar(counts, x="bucket", y="count", color="bucket")
    fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
    return fig


@st.cache_data(ttl=180)
def load_candidate_frame() -> pd.DataFrame:
    rows = repo.fetch_recent_candidates(limit=300)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(decision_support.enrich_rows(rows))


@st.cache_data(ttl=180)
def load_latest_focus_frame(market_key: str | None = None) -> pd.DataFrame:
    rows: list[dict[str, object]]
    if market_key:
        rows = repo.fetch_latest_market_rows(market_key)
    else:
        rows = repo.fetch_recent_candidates(limit=120)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(decision_support.enrich_rows(rows))


def _normalize_trend(values: object) -> list[float]:
    if not isinstance(values, list):
        return []
    normalized: list[float] = []
    for value in values:
        try:
            normalized.append(float(value))
        except (TypeError, ValueError):
            continue
    return normalized[-12:]


@st.cache_data(ttl=600)
def get_ticker_trend_cached(ticker: str, limit: int = 12) -> list[float]:
    history = market_data.get_price_history(ticker, period="3mo")
    if history.empty or "Close" not in history.columns:
        return []
    closes = history["Close"].dropna().tail(limit)
    if closes.empty:
        return []
    first = float(closes.iloc[0])
    if first == 0:
        return []
    return [round(((float(value) / first) - 1.0) * 100.0, 2) for value in closes]


@st.cache_data(ttl=600)
def get_ticker_score_trend_cached(ticker: str) -> list[float]:
    rows = repo.fetch_history(ticker, limit=12)
    values: list[float] = []
    for row in rows:
        try:
            values.append(float(row.get("composite_signal_score") or 0))
        except (TypeError, ValueError):
            values.append(0.0)
    return values


def _settings_value(name: str, fallback: str = "") -> str:
    return str(getattr(runtime_settings, name, getattr(settings, name, fallback)) or "")


def _split_tickers(raw_value: object) -> list[str]:
    return [item.strip().upper() for item in str(raw_value or "").split(",") if item.strip()]


def _join_tickers(tickers: list[str]) -> str:
    return ",".join(dict.fromkeys(ticker.strip().upper() for ticker in tickers if ticker.strip()))


def _read_market_management_lists(market_key: str) -> dict[str, set[str]]:
    return {
        "favorite": set(_split_tickers(_settings_value(f"{market_key}_manual_hot_tickers"))),
        "watch": set(_split_tickers(_settings_value(f"{market_key}_manual_watch_tickers"))),
        "exclude": set(_split_tickers(_settings_value(f"{market_key}_excluded_tickers"))),
    }


def _mutate_market_management_list(market_key: str, ticker: str, action: str) -> None:
    ticker = ticker.strip().upper()
    if not ticker:
        return
    state = _read_market_management_lists(market_key)
    for values in state.values():
        values.discard(ticker)
    if action in state:
        state[action].add(ticker)
    updates = {
        f"{market_key}_manual_hot_tickers": _join_tickers(sorted(state["favorite"])),
        f"{market_key}_manual_watch_tickers": _join_tickers(sorted(state["watch"])),
        f"{market_key}_excluded_tickers": _join_tickers(sorted(state["exclude"])),
    }
    user_settings_service.update_runtime_preferences(chat_id, updates)
    st.session_state["runtime_settings_dirty"] = True


@st.cache_data(ttl=180)
def load_dashboard_snapshot_cached() -> DashboardSnapshot:
    return dashboard_service.build_snapshot()


@st.cache_data(ttl=180)
def load_market_overview_cached() -> MarketOverview:
    return overview_service.build()


def _serialize_dashboard_snapshot(snapshot: DashboardSnapshot) -> dict[str, object]:
    return {
        "vix": snapshot.vix,
        "market_sentiment": snapshot.market_sentiment,
        "total_open_pnl": snapshot.total_open_pnl,
        "win_rate": snapshot.win_rate,
        "open_trade_count": snapshot.open_trade_count,
        "equity_curve": snapshot.equity_curve.to_dict("records"),
        "open_positions": snapshot.open_positions.to_dict("records"),
        "recent_closed_trades": snapshot.recent_closed_trades.to_dict("records"),
    }


def _deserialize_dashboard_snapshot(payload: dict[str, object]) -> DashboardSnapshot:
    return DashboardSnapshot(
        vix=payload.get("vix"),  # type: ignore[arg-type]
        market_sentiment=str(payload.get("market_sentiment") or "Unknown"),
        total_open_pnl=float(payload.get("total_open_pnl") or 0),
        win_rate=float(payload.get("win_rate") or 0),
        open_trade_count=int(payload.get("open_trade_count") or 0),
        equity_curve=pd.DataFrame(payload.get("equity_curve") or []),
        open_positions=pd.DataFrame(payload.get("open_positions") or []),
        recent_closed_trades=pd.DataFrame(payload.get("recent_closed_trades") or []),
    )


def _serialize_market_overview(overview: MarketOverview) -> dict[str, object]:
    return {
        "overall_trend": overview.overall_trend,
        "sentiment_label": overview.sentiment_label,
        "fear_greed_score": overview.fear_greed_score,
        "fear_greed_rating": overview.fear_greed_rating,
        "fear_greed_source": overview.fear_greed_source,
        "fear_greed_updated_at": overview.fear_greed_updated_at,
        "breadth_snapshot": overview.breadth_snapshot,
        "momentum_zones": overview.momentum_zones,
        "caution_items": overview.caution_items,
        "upcoming_macro_events": overview.upcoming_macro_events,
        "tw_futures_snapshot": None,
        "us_derivatives_note": overview.us_derivatives_note,
    }


def _deserialize_market_overview(payload: dict[str, object]) -> MarketOverview:
    return MarketOverview(
        overall_trend=str(payload.get("overall_trend") or "Unknown"),
        sentiment_label=str(payload.get("sentiment_label") or "Unknown"),
        fear_greed_score=int(payload.get("fear_greed_score") or 50),
        fear_greed_rating=str(payload.get("fear_greed_rating") or "Neutral"),
        fear_greed_source=str(payload.get("fear_greed_source") or "cache"),
        fear_greed_updated_at=str(payload.get("fear_greed_updated_at") or ""),
        breadth_snapshot=float(payload.get("breadth_snapshot") or 50),
        momentum_zones=list(payload.get("momentum_zones") or []),
        caution_items=list(payload.get("caution_items") or []),
        upcoming_macro_events=list(payload.get("upcoming_macro_events") or []),
        tw_futures_snapshot=None,
        us_derivatives_note=str(payload.get("us_derivatives_note") or ""),
    )


def _store_persisted_app_cache(cache_key: str, payload: dict[str, object]) -> None:
    if app_cache_repository is None:
        return
    try:
        app_cache_repository.upsert_payload(cache_key, payload)
    except Exception:
        return


def _load_persisted_app_cache(cache_key: str) -> dict[str, object] | None:
    if app_cache_repository is None:
        return None
    try:
        row = app_cache_repository.get_payload(cache_key)
    except Exception:
        return None
    payload = row.get("payload") if row else None
    return payload if isinstance(payload, dict) else None


def load_dashboard_snapshot_persisted() -> DashboardSnapshot | None:
    payload = _load_persisted_app_cache("dashboard_snapshot")
    return _deserialize_dashboard_snapshot(payload) if payload else None


def load_market_overview_persisted() -> MarketOverview | None:
    payload = _load_persisted_app_cache("market_overview")
    return _deserialize_market_overview(payload) if payload else None


def build_dashboard_snapshot_fallback() -> DashboardSnapshot:
    return DashboardSnapshot(
        vix=None,
        market_sentiment="Unknown",
        total_open_pnl=0.0,
        win_rate=0.0,
        open_trade_count=0,
        equity_curve=pd.DataFrame(columns=["sequence", "equity_pnl"]),
        open_positions=pd.DataFrame(),
        recent_closed_trades=pd.DataFrame(),
    )


def build_market_overview_fallback() -> MarketOverview:
    return MarketOverview(
        overall_trend="Unknown",
        sentiment_label="Neutral",
        fear_greed_score=50,
        fear_greed_rating="Neutral",
        fear_greed_source="Fallback",
        fear_greed_updated_at="",
        breadth_snapshot=50.0,
        momentum_zones=[],
        caution_items=[],
        upcoming_macro_events=[],
        tw_futures_snapshot=None,
        us_derivatives_note="",
    )


def _render_data_caption(text: str) -> None:
    st.caption(text)


def _format_snapshot_date(value: object) -> str:
    if value is None:
        return "-"
    try:
        return pd.to_datetime(value).strftime("%Y-%m-%d")
    except Exception:
        return str(value)


def describe_vix(vix: float | None) -> tuple[str, str]:
    if vix is None:
        return ("N/A", "Unknown")
    if vix < 18:
        return ("Calm", "Risk appetite supportive")
    if vix < 25:
        return ("Neutral", "Two-way market")
    return ("Risk-Off", "Volatility elevated")


def describe_fear_greed(score: float | int | None) -> tuple[str, str]:
    value = float(score or 50)
    if value >= 75:
        return ("Greed", "Extended risk appetite")
    if value >= 60:
        return ("Constructive", "Supportive")
    if value >= 40:
        return ("Neutral", "Balanced")
    return ("Cautious", "Defensive")


def render_market_terminal_header(snapshot: DashboardSnapshot, overview: MarketOverview) -> str:
    st.markdown(f'<div class="section-label">{t("market_terminal")}</div>', unsafe_allow_html=True)
    selected = st.radio(
        t("dashboard_market_view"),
        options=["tw", "us"],
        format_func=lambda value: t("taiwan") if value == "tw" else t("us"),
        index=0,
        horizontal=True,
        key="dashboard_market_selector",
    )
    return str(selected or "tw")


def load_persisted_analysis_summary(market_key: str) -> Any | None:
    try:
        row = repo.fetch_latest_analysis_run(market_key)
    except Exception:
        return None
    return analysis_summary_from_record(row) if row else None


def render_analysis_summary(summary: Any) -> None:
    cols = st.columns(4)
    cols[0].metric(t("market"), getattr(summary, "market_type", "-"))
    cols[1].metric(t("records"), getattr(summary, "signal_count", 0))
    cols[2].metric(t("candidates"), getattr(summary, "scanned_tickers", 0))
    cols[3].metric(t("analysis_done"), getattr(summary, "data_ready_tickers", 0))


def load_market_display_frame(candidate_frame: pd.DataFrame, market_key: str) -> pd.DataFrame:
    if candidate_frame is None or candidate_frame.empty or "ticker" not in candidate_frame.columns:
        return pd.DataFrame()
    return candidate_frame[candidate_frame["ticker"].astype(str).map(_market_key_for_ticker) == market_key].copy()


def render_run_controls() -> None:
    st.markdown(f'<div class="section-label">{t("analysis_options")}</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for market_key, label in [("tw", t("run_tw")), ("us", t("run_us"))]:
        if cols[0 if market_key == "tw" else 1].button(
            label,
            key=f"run_analysis_{market_key}",
            use_container_width=True,
        ):
            runtime = user_settings_service.get_runtime_namespace(chat_id)
            universe = UniverseBuilder(runtime, watchlist_repository=watchlist_repository).build(market_key)
            engine = AnalysisEngine(market_data=market_data, repository=repo)
            with st.spinner(t("analysis_progress")):
                summary = engine.run_with_summary(universe.to_analysis_universe())
            st.session_state["analysis_summary"] = summary
            _set_analysis_feedback("success", f'{t("analysis_done")}: {summary.signal_count}')
            load_candidate_frame.clear()
            load_latest_focus_frame.clear()
            st.rerun()


def render_market_state(market_key: str) -> None:
    summary = summary_service.build_market_summary(market_key)
    if summary is None:
        st.info(t("no_data"))
        return
    cols = st.columns(4)
    cols[0].metric(t("market_state"), localize_value(summary.regime))
    cols[1].metric(t("breadth"), f"{summary.average_breadth:.1f}")
    cols[2].metric(t("candidates"), summary.candidate_count)
    cols[3].metric(t("safer"), summary.safer_count)


def render_session_briefs() -> None:
    rows = []
    for market_key in ["tw", "us"]:
        summary = summary_service.build_market_summary(market_key)
        if summary:
            rows.append({"market": market_key.upper(), "brief": _market_bias_copy(summary)})
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_market_overview() -> None:
    overview = load_market_overview_cached()
    st.write(maybe_translate_text(overview.overall_trend))
    for item in overview.caution_items:
        st.caption(maybe_translate_text(item))


def render_manual_tracking(candidate_frame: pd.DataFrame, market_key: str) -> None:
    state = _read_market_management_lists(market_key)
    st.write(
        {
            "favorite": sorted(state["favorite"]),
            "watch": sorted(state["watch"]),
            "exclude": sorted(state["exclude"]),
        }
    )


def render_focus_lists(candidate_frame: pd.DataFrame, market_key: str) -> None:
    frame = load_market_display_frame(candidate_frame, market_key)
    if frame.empty:
        st.info(t("no_data"))
        return
    render_terminal_table(frame.head(30), ["ticker", "company", "sector", "recommendation_bucket", "composite_signal_score", "suggested_action"])


def _ticker_option_label(row: pd.Series) -> str:
    return f"{row.get('ticker', '')} | {row.get('company', '')}"


def _confluence_label(value: object) -> str:
    return localize_value(value)


def _format_strategy_scores(value: object) -> str:
    if isinstance(value, dict):
        return " | ".join(f"{key}: {score}" for key, score in value.items())
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    return str(value or "")


def render_runtime_settings_panel() -> None:
    with st.sidebar.expander(t("settings_panel"), expanded=False):
        current = user_settings_service.get_runtime_preferences(chat_id)
        large_cap_only = st.checkbox(
            "Large cap only",
            value=bool(current.get("large_cap_only", True)),
            key="settings_large_cap_only",
        )
        risk_tolerance = st.number_input(
            "Risk tolerance %",
            min_value=0.1,
            max_value=50.0,
            value=float(current.get("risk_tolerance_percent") or 5.0),
            step=0.5,
            key="settings_risk_tolerance_percent",
        )
        min_streak = st.slider(
            "Institutional buy streak",
            min_value=1,
            max_value=5,
            value=int(current.get("min_institutional_buy_streak") or 3),
            key="settings_min_institutional_buy_streak",
        )
        if st.button(t("save_settings"), key="settings_save", use_container_width=True):
            user_settings_service.update_runtime_preferences(
                chat_id,
                {
                    "app_language": LANG,
                    "large_cap_only": large_cap_only,
                    "risk_tolerance_percent": risk_tolerance,
                    "min_institutional_buy_streak": min_streak,
                },
            )
            st.success(t("settings_saved"))


def render_dashboard(candidate_frame: pd.DataFrame | None = None) -> None:
    st.title(t("app_title"))
    st.caption(t("app_caption"))
    render_analysis_feedback()
    candidate_notice = st.empty()
    if candidate_frame is None:
        candidate_notice.info("甇?頛???恣????.." if LANG == "zh-TW" else "Loading candidates and management data...")
        try:
            candidate_frame = load_candidate_frame()
        except Exception as exc:
            candidate_frame = pd.DataFrame()
            _set_analysis_feedback(
                "warning",
                (
                    f"?鞈??急????堆??＊蝷箏隞?典?憛?{exc}"
                    if LANG == "zh-TW"
                    else f"Candidate data is temporarily unavailable; showing other sections first: {exc}"
                ),
            )
        finally:
            candidate_notice.empty()
    load_notice = st.empty()
    cached_snapshot = load_dashboard_snapshot_persisted()
    cached_overview = load_market_overview_persisted()
    if cached_snapshot is not None or cached_overview is not None:
        load_notice.info("?＊蝷箔?甈⊥??翰?改???甇交?唳??啣??渲???.." if LANG == "zh-TW" else "Showing the last successful snapshot first while refreshing live market data...")
    else:
        load_notice.info("甇?頛撣敹怎??蝺???.." if LANG == "zh-TW" else "Loading market snapshot and sentiment data...")
    snapshot = cached_snapshot or build_dashboard_snapshot_fallback()
    overview = cached_overview or build_market_overview_fallback()
    snapshot_error = None
    overview_error = None
    try:
        fresh_snapshot = load_dashboard_snapshot_cached()
        snapshot = fresh_snapshot
        _store_persisted_app_cache("dashboard_snapshot", _serialize_dashboard_snapshot(fresh_snapshot))
    except Exception as exc:
        snapshot_error = exc
    try:
        fresh_overview = load_market_overview_cached()
        overview = fresh_overview
        _store_persisted_app_cache("market_overview", _serialize_market_overview(fresh_overview))
    except Exception as exc:
        overview_error = exc
    load_notice.empty()
    if snapshot_error or overview_error:
        problems = []
        if snapshot_error:
            problems.append("撣敹怎")
        if overview_error:
            problems.append("撣璁汗")
        label = "?".join(problems) if LANG == "zh-TW" else ", ".join(problems)
        st.warning(
            (
                f"{label} ???????????????????????????????"
                if LANG == "zh-TW"
                else f"{label} could not be loaded just now. Showing available content first; a refresh usually recovers it."
            )
        )
    selected_market_key = render_market_terminal_header(snapshot, overview)
    latest_summary = st.session_state.get("analysis_summary")
    if latest_summary and getattr(latest_summary, "market_type", "") != selected_market_key:
        latest_summary = None
    if latest_summary is None:
        latest_summary = load_persisted_analysis_summary(selected_market_key)
    if latest_summary:
        render_analysis_summary(latest_summary)
    market_candidate_frame = load_market_display_frame(candidate_frame, selected_market_key)

    top_metrics = st.columns(4)
    vix_zone, _ = describe_vix(snapshot.vix)
    top_metrics[0].metric(t("vix"), f"{snapshot.vix:.2f}" if snapshot.vix is not None else "N/A", delta=vix_zone if snapshot.vix is not None else None)
    top_metrics[1].metric(t("sentiment"), localize_value(snapshot.market_sentiment), delta=describe_fear_greed(overview.fear_greed_score)[0])
    top_metrics[2].metric(t("open_pnl"), f"{snapshot.total_open_pnl:.2f}%")
    top_metrics[3].metric(t("win_rate"), f"{snapshot.win_rate:.2f}%")

    render_run_controls()
    overview_tab, scan_tab, names_tab = st.tabs(
        [
            "????" if LANG == "zh-TW" else "Market Overview",
            "????" if LANG == "zh-TW" else "Visual Scan",
            "?????" if LANG == "zh-TW" else "Lists & Decisions",
        ]
    )
    with overview_tab:
        render_market_state(selected_market_key)
        render_session_briefs()
        render_market_overview()
    with scan_tab:
        scan_pulse_tab, scan_heat_tab, scan_dist_tab, scan_rank_tab = st.tabs(
            [
                "????" if LANG == "zh-TW" else "Pulse",
                "????" if LANG == "zh-TW" else "Heatmap",
                "????" if LANG == "zh-TW" else "Distribution",
                "??" if LANG == "zh-TW" else "Boards",
            ]
        )
        with scan_pulse_tab:
            render_visual_scan(market_candidate_frame, snapshot, overview, selected_market_key)
        with scan_heat_tab:
            st.markdown(f'<div class="section-label">{t("sector_heatmap")}</div>', unsafe_allow_html=True)
            st.plotly_chart(build_sector_heatmap(market_candidate_frame), use_container_width=True, config={"displayModeBar": False}, key="scan_tab_sector_heatmap")
        with scan_dist_tab:
            st.markdown(f'<div class="section-label">{t("setup_distribution")}</div>', unsafe_allow_html=True)
            st.plotly_chart(build_setup_distribution_chart(market_candidate_frame), use_container_width=True, config={"displayModeBar": False}, key="scan_tab_setup_distribution")
        with scan_rank_tab:
            render_rank_boards(selected_market_key)
    with names_tab:
        manual_tab, focus_tab, decision_tab, holdings_tab = st.tabs(
            [
                "????" if LANG == "zh-TW" else "Manual Tracking",
                t("focus_lists"),
                t("decision_cards"),
                "?????" if LANG == "zh-TW" else "Holdings Library",
            ]
        )
        with manual_tab:
            render_manual_tracking(market_candidate_frame, selected_market_key)
        with focus_tab:
            render_focus_lists(market_candidate_frame, selected_market_key)
        with decision_tab:
            left, right = st.columns((1.12, 0.88))
            with left:
                render_decision_cards(market_candidate_frame, selected_market_key)
            with right:
                render_rank_boards(selected_market_key)
        with holdings_tab:
            render_holdings_library(market_candidate_frame, selected_market_key)

    left, right = st.columns((1.55, 1))
    with left:
        st.markdown(f'<div class="section-label">{t("portfolio_curve")}</div>', unsafe_allow_html=True)
        if snapshot.equity_curve.empty:
            st.info(t("no_closed_trades"))
        else:
            st.plotly_chart(
                px.line(snapshot.equity_curve, x="sequence", y="equity_pnl", markers=True, title=t("portfolio_curve")),
                use_container_width=True,
            )
    with right:
        st.markdown(f'<div class="section-label">{t("open_positions")}</div>', unsafe_allow_html=True)
        if snapshot.open_positions.empty:
            st.info(t("no_positions"))
        else:
            st.dataframe(snapshot.open_positions, use_container_width=True, hide_index=True)


def render_portfolio() -> None:
    st.markdown(f'<div class="page-title">{t("portfolio")}</div>', unsafe_allow_html=True)
    positions, _ = portfolio_service.get_open_positions_summary()
    if not positions:
        st.info(t("no_positions"))
        return
    frame = pd.DataFrame(positions)
    st.dataframe(frame, use_container_width=True, hide_index=True)
    st.plotly_chart(px.bar(frame, x="ticker", y="stop_buffer_percent", title=t("stop_buffer")), use_container_width=True)


def render_screener(candidate_frame: pd.DataFrame) -> None:
    st.markdown(f'<div class="page-title">{t("screener")}</div>', unsafe_allow_html=True)
    if candidate_frame.empty:
        st.info(t("no_data"))
        return
    latest_date = candidate_frame["date"].max()
    _render_data_caption(f'{t("snapshot_as_of")}: {_format_snapshot_date(latest_date)}')
    latest = candidate_frame[candidate_frame["date"] == latest_date].copy()
    latest = enrich_with_company_metadata(latest)
    c1, c2, c3 = st.columns(3)
    selected_market = c1.selectbox(t("market"), [t("all"), "tw", "us"], key="screener_market")
    selected_bucket = c2.selectbox(
        t("bucket"),
        [t("all"), "Safer Follow-Through", "Actionable", "Watchlist"],
        key="screener_bucket",
    )
    min_score = c3.slider(t("min_score"), min_value=0, max_value=100, value=60, key="screener_min_score")
    filtered = latest.copy()
    if selected_market != t("all"):
        filtered = filtered[filtered["type"] == selected_market]
    if selected_bucket != t("all"):
        filtered = filtered[filtered["recommendation_bucket"] == selected_bucket]
    filtered = filtered[filtered["composite_signal_score"] >= min_score]

    left, right = st.columns((1.15, 1))
    with left:
        display = filtered.copy()
        for column in ["universe_bucket", "recommendation_bucket", "entry_timing", "market_regime", "event_risk_note"]:
            if column in display.columns:
                display[column] = display[column].map(localize_value)
        if "confluence_classification" in display.columns:
            display["confluence_classification"] = display["confluence_classification"].map(_confluence_label)
        if "strategy_scores" in display.columns:
            display["strategy_scores"] = display["strategy_scores"].apply(_format_strategy_scores)
        st.dataframe(
            display[
                [
                    column
                    for column in [
                        "ticker",
                        "company",
                        "sector",
                        "type",
                        "universe_bucket",
                        "signal_type",
                        "recommendation_bucket",
                        "composite_signal_score",
                        "confluence_score",
                        "confluence_classification",
                        "strategy_scores",
                        "recommendation_level",
                        "win_rate_label",
                        "risk_level",
                    ]
                    if column in display.columns
                ]
            ].rename(
                columns={
                    "ticker": t("ticker"),
                    "company": t("company"),
                    "sector": t("sector"),
                    "type": t("market"),
                    "universe_bucket": t("universe"),
                    "signal_type": t("signal_type"),
                    "recommendation_bucket": t("bucket"),
                    "composite_signal_score": t("score"),
                    "recommendation_level": "撱箄降蝑?" if LANG == "zh-TW" else "Recommendation Level",
                    "win_rate_label": t("win_label"),
                    "risk_level": t("risk_label"),
                    "forward_score": t("forward_score"),
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    with right:
        ticker = st.text_input(t("ticker"), value="2330.TW", key="screener_ticker_history")
        history = pd.DataFrame(repo.fetch_history(ticker))
        if history.empty:
            st.info(t("no_data"))
            return
        history = pd.DataFrame(decision_support.enrich_rows(history.to_dict("records")))
        history_start = _format_snapshot_date(history["date"].min()) if "date" in history.columns else ""
        history_end = _format_snapshot_date(history["date"].max()) if "date" in history.columns else ""
        if history_start or history_end:
            _render_data_caption(f'{t("data_window")}: {history_start} -> {history_end}')
        latest_row = history.iloc[-1]
        top1, top2 = st.columns(2)
        top1.metric(t("score"), f"{float(latest_row.get('composite_signal_score', 0)):.2f}")
        top2.metric(t("bucket"), localize_value(latest_row.get("recommendation_bucket", "Watchlist")))
        detail_tab, why_tab = st.tabs([t("detail_tab"), t("why_tab")])
        with detail_tab:
            st.plotly_chart(px.line(history, x="date", y="close_price", markers=True, title=t("price_trend")), use_container_width=True)
            st.plotly_chart(
                px.line(
                    history,
                    x="date",
                    y=[
                        "market_regime_score",
                        "breadth_score",
                        "relative_strength_score",
                        "institutional_conviction_score",
                        "entry_quality_score",
                        "composite_signal_score",
                    ],
                    markers=True,
                    title=t("funnel_scores"),
                ),
                use_container_width=True,
            )
            if "confluence_score" in history.columns:
                st.plotly_chart(
                    px.line(
                        history,
                        x="date",
                        y=["confluence_score", "composite_signal_score"],
                        markers=True,
                        title="\u591a\u7b56\u7565\u5171\u632f vs \u7d9c\u5408\u5206\u6578" if LANG == "zh-TW" else "Confluence vs Composite",
                    ),
                    use_container_width=True,
                )
        with why_tab:
            st.markdown(f"**{t('suggested_action')}**  \n{maybe_translate_text(str(latest_row.get('suggested_action', '')))}")
            st.markdown(
                f"**{'\u591a\u7b56\u7565\u5171\u632f' if LANG == 'zh-TW' else 'Confluence'}**  \n"
                f"{float(latest_row.get('confluence_score', 0) or 0):.1f} | {_confluence_label(latest_row.get('confluence_classification', ''))}"
            )
            st.markdown(
                f"**{'\u7b56\u7565\u62c6\u89e3' if LANG == 'zh-TW' else 'Strategy Mix'}**  \n"
                f"{_format_strategy_scores(latest_row.get('strategy_scores', {}))}"
            )
            st.markdown(f"**{t('rationale')}**")
            for item in latest_row.get("rationale", []):
                st.write(f"- {maybe_translate_text(item)}")
            if latest_row.get("confluence_reasons"):
                st.markdown(f"**{'\u591a\u7b56\u7565\u5171\u632f\u539f\u56e0' if LANG == 'zh-TW' else 'Confluence Reasons'}**")
                for item in latest_row.get("confluence_reasons", []):
                    st.write(f"- {maybe_translate_text(str(item))}")
            st.markdown(f"**{t('risks')}**")
            for item in latest_row.get("risks", []):
                st.write(f"- {maybe_translate_text(item)}")


def render_health_check() -> None:
    st.markdown(f'<div class="page-title">{t("health")}</div>', unsafe_allow_html=True)
    if st.button("Run Source Diagnostics", key="health_run_source_diagnostics", use_container_width=True):
        with st.spinner("Checking market-data sources..."):
            rows = market_data.diagnose_providers()
        frame = pd.DataFrame(rows)
        if LANG == "zh-TW":
            frame = frame.rename(columns={"source": "??", "status": "??", "latency_ms": "??(ms)", "note": "??"})
            frame["??"] = frame["??"].map(lambda s: "??" if s == "ok" else "??")
        st.dataframe(frame, use_container_width=True, hide_index=True)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        .page-title {
            font-size: 1.8rem;
            line-height: 1.2;
            font-weight: 700;
            color: #172033;
            margin: 0 0 0.35rem;
        }
        .section-label {
            font-size: 0.94rem;
            line-height: 1.3;
            font-weight: 700;
            color: #26344d;
            margin: 1.1rem 0 0.45rem;
        }
        .light-card {
            border: 1px solid #dbe3ef;
            border-radius: 8px;
            padding: 0.85rem 0.9rem;
            background: #ffffff;
            min-height: 112px;
        }
        .light-card-label,
        .summary-band-copy {
            color: #64748b;
            font-size: 0.82rem;
            line-height: 1.35;
        }
        .light-card-value {
            color: #172033;
            font-size: 1.18rem;
            font-weight: 700;
            margin-top: 0.25rem;
        }
        .light-card-copy {
            font-size: 0.78rem;
            line-height: 1.35;
            margin-top: 0.35rem;
        }
        .summary-band {
            border: 1px solid #dbe3ef;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            background: #f8fafc;
        }
        .summary-band-title {
            color: #172033;
            font-weight: 700;
            line-height: 1.35;
            margin-bottom: 0.2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_styles()

language_options = {"繁體中文": "zh-TW", "English": "en"}
selected_label = st.sidebar.selectbox(
    f'Language / {COPY["zh-TW"]["language"]}',
    options=list(language_options.keys()),
    index=0 if LANG == "zh-TW" else 1,
    key="language_selector",
)
LANG = language_options[selected_label]
TEXT = COPY["zh-TW"] | COPY[language_options[selected_label]]
render_runtime_settings_panel()

panorama_label = "市場全景" if LANG == "zh-TW" else "Market Panorama"
nav = st.sidebar.radio(
    t("view"),
    [t("dashboard"), panorama_label, t("portfolio"), t("screener"), t("health")],
    index=0,
    key="main_nav",
)

if nav == t("dashboard"):
    render_dashboard()
elif nav == panorama_label:
    render_market_panorama()
elif nav == t("portfolio"):
    render_portfolio()
elif nav == t("health"):
    render_health_check()
else:
    candidate_frame = load_candidate_frame()
    render_screener(candidate_frame)

