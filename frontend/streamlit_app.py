from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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

from investbot.config import get_settings
from investbot.data_sources.market_data import YahooMarketDataClient
from investbot.db.repositories import DailyAnalysisRepository
from investbot.services.analysis_engine import AnalysisEngine, AnalysisRunSummary
from investbot.services.dashboard_service import DashboardService
from investbot.services.decision_support import DecisionSupportService
from investbot.services.event_risk_service import EventRiskService
from investbot.services.market_overview_service import MarketOverviewService
from investbot.services.portfolio_service import PortfolioService
from investbot.services.summary_service import SummaryService
from investbot.services.universe_builder import UniverseBuilder
from investbot.services.user_settings_service import UserSettingsService

st.set_page_config(page_title="Smart Swing Agent", layout="wide", initial_sidebar_state="expanded")

settings = get_settings()
chat_id = settings.telegram_allowed_chat_id
user_settings_service = UserSettingsService()
runtime_settings = user_settings_service.get_runtime_namespace(chat_id)
repo = DailyAnalysisRepository()
portfolio_service = PortfolioService()
market_data = YahooMarketDataClient()
dashboard_service = DashboardService(portfolio_service=portfolio_service, market_data=market_data)
decision_support = DecisionSupportService()
summary_service = SummaryService(repository=repo, decision_support=decision_support)
overview_service = MarketOverviewService(repository=repo, summary_service=summary_service, market_data=market_data)


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
        "app_caption": "先看總體市場，再看資金流與動能，最後再看個股。",
        "language": "語言",
        "view": "檢視",
        "dashboard": "總覽",
        "portfolio": "持股",
        "screener": "篩選",
        "health": "健康檢查",
        "run_analysis": "執行分析",
        "run_tw": "執行台股分析",
        "run_us": "執行美股分析",
        "analysis_done": "分析完成",
        "analysis_failed": "分析失敗",
        "analysis_progress": "分析進度",
        "analysis_summary": "分析摘要",
        "analysis_options": "分析選項",
        "force_refresh": "強制重抓歷史資料",
        "cooldown_skip": "剛分析過，直接沿用近期結果，避免重複抓資料。",
        "cooldown_force_hint": "若你懷疑資料源更新較慢，再勾選強制重抓。",
        "records": "寫入筆數",
        "market_state": "市場狀態",
        "overall_trend": "整體趨勢",
        "sentiment": "市場情緒",
        "fear_greed": "恐慌 / 貪婪",
        "fear_greed_gauge": "情緒儀表",
        "breadth": "市場廣度",
        "momentum_zones": "動能區域",
        "cautions": "提醒",
        "macro_calendar": "重大事件行事曆",
        "market_overview": "市場總覽",
        "market_terminal": "市場首頁",
        "benchmark_watch": "基準觀察",
        "dashboard_market_view": "首頁市場",
        "taiex": "加權指數",
        "taiwan50": "台灣50",
        "tsmc_proxy": "台積電",
        "sp500": "標普500",
        "nasdaq": "納斯達克",
        "dow": "道瓊",
        "taiwan": "台股",
        "us": "美股",
        "candidates": "候選數",
        "actionable": "可行動",
        "safer": "相對安全延續",
        "focus_lists": "重點名單",
        "decision_cards": "決策卡",
        "core_pool": "核心池",
        "explore_pool": "觀察池",
        "watchlist": "觀察",
        "no_data": "目前沒有資料，先跑一次分析。",
        "vix": "VIX",
        "open_pnl": "未實現報酬",
        "win_rate": "勝率",
        "portfolio_curve": "資金曲線",
        "open_positions": "持有部位",
        "no_positions": "目前沒有持倉。",
        "no_closed_trades": "目前還沒有已平倉交易。",
        "stop_buffer": "停損緩衝",
        "market": "市場",
        "bucket": "分組",
        "all": "全部",
        "min_score": "最低綜合分數",
        "ticker": "代號",
        "company": "公司",
        "sector": "類股",
        "price_trend": "價格趨勢",
        "funnel_scores": "漏斗分數",
        "suggested_action": "建議動作",
        "rationale": "推薦理由",
        "risks": "主要風險",
        "forward_score": "前瞻分數",
        "forward_notes": "前瞻因子",
        "win_label": "勝率評估",
        "risk_label": "風險等級",
        "reward_risk": "風報比",
        "event_risk": "事件風險",
        "next_event": "下一事件",
        "universe": "池別",
        "score": "分數",
        "signal_type": "訊號",
        "unknown": "未知",
        "calm": "平穩",
        "neutral": "中性",
        "risk_off": "避險",
        "clear": "正常",
        "vix_zone": "VIX 區間",
        "vix_meaning": "VIX 解讀",
        "market_read": "市場判讀",
        "visual_scan": "視覺掃描",
        "market_pulse": "市場脈搏",
        "sector_heatmap": "類股熱區",
        "setup_distribution": "台美建議分佈",
        "breadth_lights": "市場燈號",
        "trend_mini": "短線走勢",
        "score_trend": "分數節奏",
        "session_brief": "開盤摘要",
        "tw_brief": "台股摘要",
        "us_brief": "美股摘要",
        "rank_board": "熱度榜",
        "leader_board": "領先名單",
        "risk_board": "風險名單",
        "best_score": "最佳分數",
        "avg_score": "平均分數",
        "market_bias": "市場偏向",
        "day1": "第 1 天",
        "day2": "第 2 天",
        "day3": "第 3 天以上",
        "core_tab": "核心",
        "explore_tab": "觀察",
        "risk_tab": "風險",
        "why_tab": "原因",
        "detail_tab": "細節",
        "settings_panel": "偏好設定",
        "save_settings": "儲存設定",
        "settings_saved": "設定已寫入資料庫",
        "high_risk_dates": "手動補充事件日期",
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
        "benchmark_range": "走勢區間",
        "today": "當天",
        "one_month": "月",
        "one_year": "一年",
        "three_year": "三年",
        "five_year": "五年",
        "benchmark_no_data": "這個區間沒有資料。",
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

COPY["zh-TW"].update(
    {
        "data_freshness": "資料時間",
        "snapshot_as_of": "快照日期",
        "data_window": "資料區間",
        "page_rendered_at": "頁面抓取時間",
        "latest_analysis_date": "最新分析日期",
        "intraday_source_note": "當日分時若來源不足，會顯示沒有資料，不自動冒充較長區間。",
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
        "data_freshness": "資料時間",
        "snapshot_as_of": "快照日期",
        "data_window": "資料區間",
        "page_rendered_at": "頁面抓取時間",
        "latest_analysis_date": "最新分析日期",
        "intraday_source_note": "當日分時若來源不足，會顯示沒有資料，不自動冒充較長區間。",
    }
)

COPY["zh-TW"].update(
    {
        "decision_score_label": "決策分數",
        "decision_score_help": "80+ 偏強、70-79 可試單、60-69 觀察、60 以下先不動。",
        "decision_verdict": "結論",
        "verdict_buy": "可買",
        "verdict_probe": "可試單",
        "verdict_wait": "先觀察",
        "verdict_avoid": "先不買",
        "leader_board_help": "這裡看的是目前最強、最接近可執行的標的。",
        "risk_board_help": "這裡看的是事件風險高、延續性差，或暫時不適合追的標的。",
    }
)

COPY["en"].update(
    {
        "decision_score_label": "Decision Score",
        "decision_score_help": "80+ strong, 70-79 starter size, 60-69 watch, below 60 no action.",
        "decision_verdict": "Verdict",
        "verdict_buy": "Buy",
        "verdict_probe": "Starter Size",
        "verdict_wait": "Watch",
        "verdict_avoid": "Avoid",
        "leader_board_help": "These are the strongest names and the closest to execution right now.",
        "risk_board_help": "These names carry higher event risk, weaker follow-through, or simply are not chaseable right now.",
    }
)

ZH_DECISION_TEXT = {
    "Institutional buying has persisted for 3 sessions.": "法人買超已連續 3 天。",
    "Institutional buying has persisted for 4 sessions.": "法人買超已連續 4 天。",
    "Institutional buying has persisted for 5 sessions.": "法人買超已連續 5 天。",
    "Institutional buying is building into a second session.": "法人買超延續到第 2 天，動能正在建立。",
    "Institutional buying has just turned positive.": "法人買盤剛轉正。",
    "Relative strength is decisively above the market benchmark.": "相對強度明顯優於市場基準。",
    "Relative strength is supportive versus the benchmark.": "相對強度優於基準，屬於正向支持。",
    "Price location is constructive and not excessively extended.": "價格位階健康，且未過度乖離。",
    "Entry quality is acceptable if execution stays disciplined.": "進場品質尚可，前提是執行紀律要嚴格。",
    "The market regime is supportive for trend-following entries.": "市場環境偏向有利順勢操作。",
    "The broader market is neutral, so follow-through may be slower.": "大盤偏中性，延續力可能較慢。",
    "The broader market is risk-off, so hit rates can fall quickly.": "市場偏避險，命中率可能快速下滑。",
    "This idea is in the Explore pool, so it should not outrank core large-cap names.": "此標的屬於觀察池，不應優先於核心大型股。",
    "This name belongs to the core monitoring pool.": "此標的屬於核心追蹤池。",
    "Event risk is manageable but still worth monitoring.": "事件風險可控，但仍需持續追蹤。",
    "No major risk flags are active right now, but standard stop discipline still applies.": "目前無重大風險警訊，但仍需遵守停損紀律。",
    "The current signal does not yet have enough stacked evidence.": "目前訊號累積證據仍不足。",
    "Normal position sizing or staged entries on minor pullbacks.": "可採正常部位，或在小幅拉回時分批進場。",
    "Pilot size first, then add if confirmation holds.": "先用試單部位，確認延續後再加碼。",
    "Observe only until the odds improve.": "先觀察，等待勝率提升再行動。",
    "Small trial size only; keep core capital focused on large caps.": "僅小部位試單，核心資金維持在大型股。",
    "High Conviction Core": "高把握核心標的",
    "Actionable Setup": "可執行設定",
    "Watch and Wait": "觀望等待",
    "High": "高",
    "Medium-High": "中高",
    "Medium-Low": "中低",
    "Medium": "中",
    "Medium-High": "中高",
    "Favorable": "風報比佳",
    "Balanced": "風報平衡",
    "Unclear": "風報不明",
}


ZH_DECISION_TEXT.update(
    {
        "Institutional buying has persisted for 3 sessions.": "法人買超已連續 3 天。",
        "Institutional buying has persisted for 4 sessions.": "法人買超已連續 4 天。",
        "Institutional buying has persisted for 5 sessions.": "法人買超已連續 5 天。",
        "Institutional buying is building into a second session.": "法人買超延續到第 2 天，動能正在建立。",
        "Institutional buying has just turned positive.": "法人買盤剛轉正。",
        "Relative strength is decisively above the market benchmark.": "相對強度明顯優於市場基準。",
        "Relative strength is supportive versus the benchmark.": "相對強度優於基準，屬於正向支持。",
        "Price location is constructive and not excessively extended.": "價格位階健康，且未過度乖離。",
        "Entry quality is acceptable if execution stays disciplined.": "進場品質尚可，前提是執行紀律要嚴格。",
        "The market regime is supportive for trend-following entries.": "市場環境偏向有利順勢操作。",
        "The broader market is neutral, so follow-through may be slower.": "大盤偏中性，延續力可能較慢。",
        "The broader market is risk-off, so hit rates can fall quickly.": "市場偏避險，命中率可能快速下滑。",
        "This idea is in the Explore pool, so it should not outrank core large-cap names.": "此標的屬於觀察池，不應優先於核心大型股。",
        "This name belongs to the core monitoring pool.": "此標的屬於核心追蹤池。",
        "Event risk is manageable but still worth monitoring.": "事件風險可控，但仍需持續追蹤。",
        "No major risk flags are active right now, but standard stop discipline still applies.": "目前無重大風險警訊，但仍需遵守停損紀律。",
        "The current signal does not yet have enough stacked evidence.": "目前訊號的堆疊證據還不夠。",
        "Normal position sizing or staged entries on minor pullbacks.": "可用正常部位，或在小幅拉回時分批進場。",
        "Pilot size first, then add if confirmation holds.": "先用試單部位，確認延續後再加碼。",
        "Observe only until the odds improve.": "先觀察，等勝率提升再行動。",
        "Small trial size only; keep core capital focused on large caps.": "只用小部位試單，核心資金仍以大型股為主。",
        "High Conviction Core": "高信心核心",
        "Actionable Setup": "可執行設定",
        "Watch and Wait": "觀察等待",
        "High": "高",
        "Medium-High": "中高",
        "Medium-Low": "中低",
        "Medium": "中",
        "Favorable": "風報偏佳",
        "Balanced": "風報平衡",
        "Unclear": "風報不明",
    }
)


def current_language() -> str:
    runtime_language = getattr(runtime_settings, "app_language", "")
    if runtime_language:
        return str(runtime_language)
    try:
        accept = str(st.context.headers.get("Accept-Language", "")).lower()
    except Exception:
        accept = ""
    if "zh" in accept:
        return "zh-TW"
    return os.environ.get("APP_LANGUAGE", "zh-TW")


LANG = current_language()
TEXT = COPY["zh-TW"] | COPY.get(LANG, {})


def t(key: str) -> str:
    return TEXT[key]


def _translate_macro_event_label(label: str) -> str:
    cleaned = str(label or "").strip().replace("_", " ").lower()
    if not cleaned:
        return ""
    if LANG != "zh-TW":
        return cleaned
    direct_map = {
        "cftc eur speculative net positions": "CFTC 歐元投機淨部位",
        "cftc eur speculative net position": "CFTC 歐元投機淨部位",
        "annual report": "年報",
        "ecb cipollone speech": "歐洲央行 Cipollone 談話",
        "ecb de guindos speech": "歐洲央行 De Guindos 談話",
        "ecb survey of monetary analysts": "歐洲央行貨幣分析師調查",
        "ecb survey of professional forecasters": "歐洲央行專業預測調查",
    }
    if cleaned in direct_map:
        return direct_map[cleaned]
    replacements = {
        "cftc": "CFTC",
        "eur": "歐元",
        "usd": "美元",
        "jpy": "日圓",
        "gbp": "英鎊",
        "speculative": "投機",
        "net": "淨",
        "position": "部位",
        "positions": "部位",
        "survey": "調查",
        "speech": "談話",
        "annual": "年度",
        "report": "報告",
        "earnings": "財報",
        "inflation": "通膨",
        "payrolls": "非農就業",
        "minutes": "會議紀要",
    }
    translated = cleaned
    for source, target in replacements.items():
        translated = translated.replace(source, target)
    return translated


def localize_value(value: object) -> str:
    text_value = str(value)
    mapping = {
        "Unknown": t("unknown"),
        "Calm": t("calm"),
        "Neutral": t("neutral"),
        "Risk-Off": t("risk_off"),
        "Risk-On": "??" if LANG == "zh-TW" else "Risk-On",
        "Risk-On Uptrend": "??????" if LANG == "zh-TW" else "Risk-On Uptrend",
        "Balanced / Selective": "?? / ??" if LANG == "zh-TW" else "Balanced / Selective",
        "Defensive / Risk-Off": "?? / ????" if LANG == "zh-TW" else "Defensive / Risk-Off",
        "Greed": "??" if LANG == "zh-TW" else "Greed",
        "Constructive": "????" if LANG == "zh-TW" else "Constructive",
        "Cautious": "??" if LANG == "zh-TW" else "Cautious",
        "Fear": "??" if LANG == "zh-TW" else "Fear",
        "Watchlist": t("watchlist"),
        "Actionable": t("actionable"),
        "Safer Follow-Through": t("safer"),
        "core": t("core_pool"),
        "explore": t("explore_pool"),
        "clear": t("clear"),
        "DAY_1_EARLY": t("day1"),
        "DAY_2_BUILDING": t("day2"),
        "DAY_3_PLUS_SAFER": t("day3"),
        "Institutional Accumulation": "??????" if LANG == "zh-TW" else "Institutional Accumulation",
        "Panic Reversal": "????" if LANG == "zh-TW" else "Panic Reversal",
        "High": "?" if LANG == "zh-TW" else "High",
        "Medium": "?" if LANG == "zh-TW" else "Medium",
        "Medium-High": "??" if LANG == "zh-TW" else "Medium-High",
        "Medium-Low": "??" if LANG == "zh-TW" else "Medium-Low",
        "Favorable": "????" if LANG == "zh-TW" else "Favorable",
        "Balanced": "????" if LANG == "zh-TW" else "Balanced",
        "Unclear": "????" if LANG == "zh-TW" else "Unclear",
        "High Conviction Core": "????" if LANG == "zh-TW" else "High Conviction Core",
        "Actionable Setup": "???" if LANG == "zh-TW" else "Actionable Setup",
        "Watch and Wait": "???" if LANG == "zh-TW" else "Watch and Wait",
    }
    if text_value in mapping:
        return mapping[text_value]
    if text_value.startswith("macro_event_imminent:") or text_value.startswith("macro_event_near:"):
        prefix, label = text_value.split(":", 1)
        prefix_label = "??????" if prefix == "macro_event_imminent" and LANG == "zh-TW" else "Macro imminent"
        if prefix == "macro_event_near":
            prefix_label = "??????" if LANG == "zh-TW" else "Macro near"
        return f"{prefix_label}: {_translate_macro_event_label(label)}"
    if LANG == "zh-TW" and text_value in ZH_DECISION_TEXT:
        return ZH_DECISION_TEXT[text_value]
    return text_value


def maybe_translate_text(text_value: str) -> str:
    if LANG != "zh-TW":
        return text_value
    if text_value.startswith("Institutional buying has persisted for ") and text_value.endswith(" sessions."):
        days = text_value.replace("Institutional buying has persisted for ", "").replace(" sessions.", "").strip()
        return f"??????? {days} ??"
    if text_value.startswith("Event risk is elevated:"):
        detail = text_value.replace("Event risk is elevated:", "").strip()
        return f"???????{_translate_macro_event_label(detail)}"
    if text_value.startswith("macro_event_imminent ("):
        inner = text_value.replace("macro_event_imminent (", "").rstrip(")")
        return f"???????{_translate_macro_event_label(inner)}?"
    if text_value.startswith("macro_event_near ("):
        inner = text_value.replace("macro_event_near (", "").rstrip(")")
        return f"???????{_translate_macro_event_label(inner)}?"
    if text_value.startswith("Volatility is elevated; position sizing should stay conservative."):
        return "?????????????"
    if text_value.startswith("Breadth is weak, so single-name breakouts may fail more often."):
        return "?????????????????????"
    if text_value.endswith(" names are carrying event-risk flags."):
        count = text_value.split(" ", 1)[0]
        return f"{count} ??????????????"
    if text_value.startswith("No major market-wide warnings are flashing right now."):
        return "???????????????"
    if text_value.startswith("Theme support:"):
        return text_value.replace("Theme support:", "?????")
    if text_value.startswith("Institutional flow persistence supports the forward setup."):
        return "??????????????????"
    if text_value.startswith("Relative strength confirms demand leadership."):
        return "??????????????"
    if text_value.startswith("Forward demand narrative is strong enough for a starter position."):
        return "????????????????????"
    if " | " in text_value and len(text_value.split(" | ")) == 3:
        dt, region, title = text_value.split(" | ", 2)
        region_map = {"US": "??", "EU": "??", "JP": "??", "CN": "??", "TW": "??"}
        return f"{dt} | {region_map.get(region, region)} | {_translate_macro_event_label(title)}"
    return ZH_DECISION_TEXT.get(text_value, text_value)

def describe_vix(vix_value: float | None) -> tuple[str, str]:
    if vix_value is None:
        return (t("unknown"), "VIX 無法取得，先以市場廣度與情緒分數輔助判讀。" if LANG == "zh-TW" else "VIX unavailable; rely on breadth and sentiment instead.")
    if vix_value < 15:
        return (
            "極低波動 / 偏樂觀" if LANG == "zh-TW" else "Very low vol / optimistic",
            "市場波動很低，資金風險偏好強，但也要留意過熱追價。" if LANG == "zh-TW" else "Volatility is very low and risk appetite is strong, but crowded longs can overheat quickly.",
        )
    if vix_value < 20:
        return (
            "低波動 / 偏正向" if LANG == "zh-TW" else "Low vol / constructive",
            "目前屬於相對健康的風險區，順勢交易通常比較舒服。" if LANG == "zh-TW" else "This is a relatively healthy risk regime where trend-following tends to work better.",
        )
    if vix_value < 25:
        return (
            "中等波動 / 謹慎" if LANG == "zh-TW" else "Moderate vol / cautious",
            "波動開始升高，進場可以更挑、部位可以更小。" if LANG == "zh-TW" else "Volatility is rising, so entries should be more selective and sizing should shrink.",
        )
    if vix_value < 32:
        return (
            "高波動 / 偏避險" if LANG == "zh-TW" else "High vol / defensive",
            "市場進入偏防守狀態，單日震盪大，勝率與持有體驗都會變差。" if LANG == "zh-TW" else "Markets are defensive here, with wider daily swings and weaker holding quality.",
        )
    return (
        "極高波動 / 恐慌" if LANG == "zh-TW" else "Extreme vol / panic",
        "這通常是明顯的恐慌帶，除非是高把握逆勢交易，否則先保守。" if LANG == "zh-TW" else "This is a panic regime; stay conservative unless the reversal setup is exceptionally strong.",
    )


def describe_fear_greed(score: int) -> tuple[str, str, str]:
    if score <= 24:
        return (
            "極度恐慌" if LANG == "zh-TW" else "Extreme Fear",
            "市場參與者明顯在避險，搶反彈要很挑位置。" if LANG == "zh-TW" else "Participants are clearly de-risking; only the best reversal setups deserve attention.",
            "#ff5a6b",
        )
    if score <= 44:
        return (
            "恐慌" if LANG == "zh-TW" else "Fear",
            "情緒偏保守，單日反彈有機會，但延續力通常還不穩。" if LANG == "zh-TW" else "Sentiment is defensive; bounces can happen, but follow-through is still less reliable.",
            "#ff8a4c",
        )
    if score <= 55:
        return (
            "中性" if LANG == "zh-TW" else "Neutral",
            "市場沒有明顯偏多或偏空，適合精選個股，不適合亂追。" if LANG == "zh-TW" else "The tape is balanced; stock selection matters more than aggressive chasing.",
            "#f6c84c",
        )
    if score <= 75:
        return (
            "貪婪" if LANG == "zh-TW" else "Greed",
            "風險偏好不差，順勢策略通常比較吃香，但也要防過熱。" if LANG == "zh-TW" else "Risk appetite is healthy and trend-following tends to work, though overheating risk rises.",
            "#8bd36c",
        )
    return (
        "極度貪婪" if LANG == "zh-TW" else "Extreme Greed",
        "資金願意追價，但這也常是短線過熱區，別把節奏搞丟。" if LANG == "zh-TW" else "Capital is chasing upside aggressively, which can also mean short-term overheating.",
        "#2fbf71",
    )


def build_fear_greed_gauge(score: int) -> go.Figure:
    _, _, accent = describe_fear_greed(score)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 30}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": "rgba(0,0,0,0)"},
                "bar": {"color": accent, "thickness": 0.3},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 24], "color": "#ff6678"},
                    {"range": [25, 44], "color": "#ff9a5a"},
                    {"range": [45, 55], "color": "#f6cf56"},
                    {"range": [56, 75], "color": "#9bd66f"},
                    {"range": [76, 100], "color": "#49c57d"},
                ],
            },
        )
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=10), height=240, paper_bgcolor="white")
    return fig


def build_vix_gauge(vix_value: float | None) -> go.Figure:
    value = 0 if vix_value is None else min(max(float(vix_value), 0), 60)
    accent = "#94a3b8"
    if vix_value is not None:
        if vix_value < 15:
            accent = "#2fbf71"
        elif vix_value < 20:
            accent = "#8bd36c"
        elif vix_value < 25:
            accent = "#f6c84c"
        elif vix_value < 32:
            accent = "#ff8a4c"
        else:
            accent = "#ff5a6b"
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"font": {"size": 30}},
            title={"text": "VIX"},
            gauge={
                "axis": {"range": [0, 60], "tickvals": [0, 15, 20, 25, 32, 60]},
                "bar": {"color": accent, "thickness": 0.3},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 15], "color": "#d9f7e8"},
                    {"range": [15, 20], "color": "#ebf7cf"},
                    {"range": [20, 25], "color": "#fff2c2"},
                    {"range": [25, 32], "color": "#ffe0c2"},
                    {"range": [32, 60], "color": "#ffd0d6"},
                ],
            },
        )
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=10), height=240, paper_bgcolor="white")
    return fig


def _latest_candidates(candidate_frame: pd.DataFrame) -> pd.DataFrame:
    if candidate_frame.empty:
        return candidate_frame.copy()
    latest_date = candidate_frame["date"].max()
    return candidate_frame[candidate_frame["date"] == latest_date].copy()


def _vix_comfort_score(vix_value: float | None) -> float:
    if vix_value is None:
        return 50.0
    if vix_value <= 15:
        return 88.0
    if vix_value <= 20:
        return 74.0
    if vix_value <= 25:
        return 56.0
    if vix_value <= 32:
        return 34.0
    return 16.0


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
        .agg(
            avg_score=("score_value", "mean"),
            names=("ticker", "count"),
        )
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
        texttemplate="%{label}<br>%{value} ?<br>%{color:.0f}",
        hovertemplate="%{label}<br>" + ("??" if LANG == "zh-TW" else "Names") + ": %{value}<br>" + ("????" if LANG == "zh-TW" else "Avg Score") + ": %{color:.1f}<extra></extra>",
        root_color="white",
    )
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260, paper_bgcolor="white", coloraxis_showscale=False)
    return fig


def build_setup_distribution_chart(candidate_frame: pd.DataFrame) -> go.Figure:
    latest = _latest_candidates(candidate_frame)
    if latest.empty:
        fig = go.Figure()
        fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="white")
        return fig
    grouped = (
        latest.assign(
            market_label=latest["type"].map(lambda value: t("taiwan") if value == "tw" else t("us")),
            bucket_label=latest["recommendation_bucket"].map(localize_value),
        )
        .groupby(["market_label", "bucket_label"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )
    bucket_order = [t("safer"), t("actionable"), t("watchlist")]
    color_map = {
        t("safer"): "#2fbf71",
        t("actionable"): "#8bd36c",
        t("watchlist"): "#f6c84c",
    }
    fig = px.bar(
        grouped,
        x="market_label",
        y="count",
        color="bucket_label",
        category_orders={"bucket_label": bucket_order},
        color_discrete_map=color_map,
        text="count",
    )
    fig.update_traces(textposition="inside", hovertemplate="%{x}<br>%{fullData.name}: %{y}<extra></extra>")
    fig.update_layout(
        barmode="stack",
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend_title_text="",
        xaxis_title=None,
        yaxis_title=None,
    )
    return fig


@st.cache_data(ttl=21600, show_spinner=False)
def get_company_profile_cached(ticker: str) -> dict[str, str]:
    return market_data.get_company_profile(ticker)


@st.cache_data(ttl=1800, show_spinner=False)
def get_ticker_trend_cached(ticker: str, limit: int = 12) -> list[float]:
    history = repo.fetch_history(ticker, limit=limit)
    if not history:
        return []
    frame = pd.DataFrame(history)
    if "close_price" not in frame.columns:
        return []
    return frame["close_price"].fillna(0).astype(float).tolist()[-limit:]


@st.cache_data(ttl=1800, show_spinner=False)
def get_ticker_score_trend_cached(ticker: str, limit: int = 12) -> list[float]:
    history = repo.fetch_history(ticker, limit=limit)
    if not history:
        return []
    frame = pd.DataFrame(history)
    if "composite_signal_score" not in frame.columns:
        return []
    return frame["composite_signal_score"].fillna(0).astype(float).tolist()[-limit:]


def _display_name_for_row(row: pd.Series) -> tuple[str, str]:
    ticker = str(row.get("ticker", "")).upper()
    market_type = str(row.get("type", ""))
    profile = get_company_profile_cached(ticker)
    name_zh = str(profile.get("name_zh", "")).strip()
    name_en = str(profile.get("name_en", "")).strip()
    sector = str(profile.get("sector", "")).strip()

    if market_type == "tw":
        display_name = name_zh or name_en or ticker
        display_sector = sector or "??"
    else:
        if LANG == "zh-TW" and name_zh:
            display_name = f"{name_en}?{name_zh}?" if name_en else name_zh
        else:
            display_name = name_en or ticker
        display_sector = sector or ("??" if LANG == "zh-TW" else "Unknown")
    return display_name, display_sector


def _signal_tone(score: float) -> tuple[str, str]:
    if score >= 75:
        return ("#2fbf71", "????" if LANG == "zh-TW" else "Risk-on")
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


def _decision_verdict(row: pd.Series) -> tuple[str, str]:
    bucket = str(row.get("recommendation_bucket", "Watchlist"))
    score = float(row.get("composite_signal_score", 0) or 0)
    if bucket == "Safer Follow-Through" or score >= 80:
        return t("verdict_buy"), "#16a34a"
    if bucket == "Actionable" or score >= 70:
        return t("verdict_probe"), "#65a30d"
    if score >= 60:
        return t("verdict_wait"), "#d97706"
    return t("verdict_avoid"), "#dc2626"


def _normalize_trend(values: list[float]) -> list[float]:
    if not values:
        return []
    clean = [float(value) for value in values]
    base = clean[0] if clean[0] != 0 else 1.0
    return [round(((value / base) - 1.0) * 100, 2) for value in clean]


def _benchmark_config(range_key: str) -> tuple[str, str, int]:
    mapping = {
        "1d": ("1d", "5m", 78),
        "1mo": ("1mo", "1d", 22),
        "1y": ("1y", "1wk", 52),
        "3y": ("3y", "1wk", 156),
        "5y": ("5y", "1mo", 60),
    }
    return mapping.get(range_key, ("1d", "5m", 78))


def _benchmark_range_caption(range_key: str, trend_window: int) -> str:
    if LANG == "zh-TW":
        mapping = {
            "1d": "當日分時走勢",
            "1mo": f"近 {trend_window} 個交易日收盤趨勢",
            "1y": f"近 {trend_window} 週走勢",
            "3y": f"近 {trend_window} 週走勢",
            "5y": f"近 {trend_window} 個月走勢",
        }
    else:
        mapping = {
            "1d": "Intraday trend",
            "1mo": f"Last {trend_window} daily closes",
            "1y": f"Last {trend_window} weekly closes",
            "3y": f"Last {trend_window} weekly closes",
            "5y": f"Last {trend_window} monthly closes",
        }
    return mapping.get(range_key, mapping["1d"])


def _format_benchmark_datetime(value: pd.Timestamp | None) -> str:
    if value is None or pd.isna(value):
        return ""
    stamp = pd.Timestamp(value)
    return stamp.strftime("%Y-%m-%d %H:%M:%S")


def _format_snapshot_date(value: object) -> str:
    if value in (None, "", "nan"):
        return ""
    try:
        stamp = pd.to_datetime(value, errors="coerce")
    except Exception:
        return str(value)
    if pd.isna(stamp):
        return str(value)
    if isinstance(stamp, pd.Series):
        return str(value)
    return pd.Timestamp(stamp).strftime("%Y-%m-%d")


def _render_data_caption(*parts: str) -> None:
    items = [part.strip() for part in parts if part and str(part).strip()]
    if items:
        st.caption(" | ".join(items))


def _render_segmented_control(label: str, options: list[str], format_func, key: str) -> str:
    segmented = getattr(st, "segmented_control", None)
    if callable(segmented):
        return segmented(label, options=options, format_func=format_func, selection_mode="single", key=key)
    return st.radio(label, options=options, format_func=format_func, horizontal=True, label_visibility="collapsed", key=key)


@st.cache_data(ttl=900, show_spinner=False)
def get_benchmark_snapshot_cached(symbol: str, label_key: str, range_key: str) -> dict[str, Any]:
    period, interval, default_window = _benchmark_config(range_key)
    history = pd.DataFrame()
    if range_key == "1d":
        try:
            history = market_data._fetch_from_yahoo_chart(symbol, period=period, interval=interval)
        except Exception:
            history = pd.DataFrame()
    if history.empty:
        history = market_data.get_price_history(symbol, period=period, interval=interval)
    frame = history.copy()
    if "Date" in frame.columns:
        frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
        frame = frame.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    if frame.empty or "Close" not in frame.columns:
        return {
            "symbol": symbol,
            "label_key": label_key,
            "latest": None,
            "delta": None,
            "pct": None,
            "trend": [],
            "trend_window": 0,
            "range_key": range_key,
            "has_data": False,
            "start_at": None,
            "end_at": None,
        }
    frame["Close"] = frame["Close"].astype(float)
    latest = float(frame["Close"].iloc[-1])
    previous = float(frame["Close"].iloc[0]) if len(frame) > 1 else latest
    if range_key == "1d":
        previous_close = _get_previous_session_close(symbol, frame)
        if previous_close is not None:
            previous = previous_close
    delta = latest - previous
    pct = 0.0 if previous == 0 else (delta / previous) * 100
    trend_window = min(len(frame), default_window)
    trend = _normalize_trend(frame["Close"].tail(trend_window).tolist())
    return {
        "symbol": symbol,
        "label_key": label_key,
        "latest": latest,
        "delta": delta,
        "pct": pct,
        "trend": trend,
        "trend_window": trend_window,
        "range_key": range_key,
        "has_data": True,
        "start_at": _format_benchmark_datetime(frame["Date"].iloc[0] if "Date" in frame.columns and not frame.empty else None),
        "end_at": _format_benchmark_datetime(frame["Date"].iloc[-1] if "Date" in frame.columns and not frame.empty else None),
    }


@st.cache_data(ttl=900, show_spinner=False)
def _get_previous_session_close(symbol: str, intraday_frame: pd.DataFrame) -> float | None:
    try:
        daily_frame = market_data.get_price_history(symbol, period="5d", interval="1d")
    except Exception:
        return None
    if daily_frame.empty or "Close" not in daily_frame.columns:
        return None
    frame = daily_frame.copy()
    if "Date" in frame.columns:
        frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
        frame = frame.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    if frame.empty:
        return None
    frame["Close"] = frame["Close"].astype(float)
    intraday_date = None
    if "Date" in intraday_frame.columns and not intraday_frame.empty:
        intraday_date = pd.Timestamp(intraday_frame["Date"].iloc[-1]).normalize()
    if intraday_date is not None:
        frame["NormDate"] = frame["Date"].dt.normalize()
        older_rows = frame[frame["NormDate"] < intraday_date]
        if not older_rows.empty:
            return float(older_rows["Close"].iloc[-1])
        same_day_rows = frame[frame["NormDate"] == intraday_date]
        if not same_day_rows.empty and len(frame) >= 2:
            return float(frame["Close"].iloc[-2])
    if len(frame) >= 2:
        return float(frame["Close"].iloc[-2])
    return float(frame["Close"].iloc[-1]) if not frame.empty else None


def load_benchmark_snapshots(symbol_pairs: list[tuple[str, str]], range_key: str) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=min(3, len(symbol_pairs) or 1)) as executor:
        future_map = {
            executor.submit(get_benchmark_snapshot_cached, symbol, label_key, range_key): (symbol, label_key)
            for symbol, label_key in symbol_pairs
        }
        for future in as_completed(future_map):
            symbol, label_key = future_map[future]
            try:
                results[symbol] = future.result()
            except Exception:
                results[symbol] = {
                    "label_key": label_key,
                    "latest": None,
                    "delta": None,
                    "pct": None,
                    "trend": [],
                    "trend_window": 0,
                    "range_key": range_key,
                    "has_data": False,
                    "start_at": None,
                    "end_at": None,
                }
    return results


def build_benchmark_chart(series: list[float], positive: bool) -> go.Figure:
    color = "#16a34a" if positive else "#ef4444"
    fill = "rgba(34,197,94,0.12)" if positive else "rgba(239,68,68,0.12)"
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            y=series,
            mode="lines",
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor=fill,
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=72,
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


def enrich_with_company_metadata(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    enriched = frame.copy()
    names: list[str] = []
    sectors: list[str] = []
    for _, row in enriched.iterrows():
        company_name, sector = _display_name_for_row(row)
        names.append(company_name)
        sectors.append(sector)
    enriched["company"] = names
    enriched["sector"] = sectors
    return enriched


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container { max-width: 1450px; padding-top: 2.15rem; padding-bottom: 1.8rem; }
        section[data-testid="stSidebar"] { min-width: 340px !important; max-width: 340px !important; }
        .page-title { font-size: 1.9rem; font-weight: 800; line-height: 1.2; margin: 0 0 1rem 0; color: #243047; }
        .section-label { font-size: 0.78rem; font-weight: 700; color: #616c7c; margin: 0.85rem 0 0.45rem; text-transform: uppercase; }
        .hero-shell { border-bottom:1px solid rgba(118,128,145,.16); padding-bottom:16px; margin-bottom:14px; }
        .hero-title { font-size:2.15rem; font-weight:900; color:#101828; letter-spacing:0; margin:0; }
        .hero-sub { font-size:0.92rem; color:#667085; margin-top:4px; }
        .hero-time { text-align:right; font-size:0.88rem; color:#98a2b3; font-weight:700; margin-top:8px; }
        .benchmark-card { border:1px solid rgba(118,128,145,.14); border-radius:10px; background:#fff; padding:10px 12px; min-height:128px; }
        .benchmark-name { font-size:0.98rem; font-weight:800; color:#243047; margin-bottom:2px; }
        .benchmark-price { font-size:1.75rem; font-weight:900; line-height:1.05; margin:2px 0 4px; }
        .benchmark-change { font-size:0.9rem; font-weight:700; }
        .hero-summary-band { display:grid; grid-template-columns:1.25fr repeat(4,minmax(0,1fr)); gap:12px; margin:10px 0 8px; }
        .hero-summary-card { border:1px solid rgba(118,128,145,.16); border-radius:10px; background:#f8fafc; padding:12px 14px; min-height:110px; }
        .hero-summary-card.main { background:linear-gradient(180deg, #f8fafc 0%, #f4f7fb 100%); }
        .hero-summary-title { font-size:0.76rem; font-weight:800; color:#475467; text-transform:uppercase; margin-bottom:8px; letter-spacing:.02em; }
        .hero-summary-main { font-size:1.18rem; font-weight:900; color:#101828; margin-bottom:6px; }
        .hero-summary-copy { font-size:0.84rem; color:#667085; line-height:1.45; }
        .hero-summary-kpi-label { font-size:0.74rem; color:#667085; font-weight:700; margin-bottom:4px; text-transform:uppercase; }
        .hero-summary-kpi-value { font-size:1.05rem; color:#101828; font-weight:900; line-height:1.2; }
        .terminal-card, .summary-band, .decision-card { border: 1px solid rgba(118,128,145,.22); border-radius: 8px; background: #ffffff; }
        .terminal-card { padding: 14px; min-height: 174px; }
        .summary-band { padding: 12px 14px; min-height: 112px; background: #f7f9fc; }
        .summary-title { font-size: 0.75rem; font-weight: 700; color: #697483; margin-bottom: 5px; text-transform: uppercase; }
        .summary-main { font-size: 1.08rem; font-weight: 800; margin-bottom: 8px; }
        .summary-sub { font-size: 0.82rem; color: #596474; line-height: 1.45; }
        .state-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin-bottom:12px; }
        .state-metric { border:1px solid rgba(118,128,145,.16); border-radius:8px; padding:10px 12px; background:#f7f9fc; min-height:72px; }
        .state-label { font-size:0.73rem; color:#6b7685; text-transform:uppercase; margin-bottom:4px; font-weight:700; }
        .state-value { font-size:0.98rem; font-weight:800; line-height:1.2; }
        .state-card { border:1px solid rgba(118,128,145,.18); border-radius:12px; background:#ffffff; padding:14px 16px; min-height:100%; }
        .state-card-head { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; margin-bottom:10px; }
        .state-card-title { font-size:0.84rem; font-weight:800; color:#243047; text-transform:uppercase; }
        .state-card-meta { font-size:0.76rem; color:#98a2b3; line-height:1.35; text-align:right; }
        .state-read { border:1px solid rgba(118,128,145,.16); border-radius:8px; padding:12px 14px; background:#f7f9fc; min-height:118px; }
        .state-read-title { font-size:0.73rem; color:#6b7685; text-transform:uppercase; margin-bottom:6px; font-weight:700; }
        .state-read-main { font-size:1rem; font-weight:800; margin-bottom:6px; color:#243047; }
        .state-read-copy { font-size:0.86rem; color:#596474; line-height:1.5; }
        .light-strip { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin: 8px 0 14px; }
        .light-card { border:1px solid rgba(118,128,145,.16); border-radius:8px; padding:10px 12px; background:#f7f9fc; min-height:78px; }
        .light-top { display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:7px; }
        .light-name { font-size:0.72rem; text-transform:uppercase; color:#6b7685; font-weight:700; }
        .light-dot { width:10px; height:10px; border-radius:50%; display:inline-block; }
        .light-value { font-size:1rem; font-weight:800; color:#243047; margin-bottom:4px; }
        .light-copy { font-size:0.82rem; color:#596474; line-height:1.35; }
        .mini-list { margin: 0; padding-left: 18px; color: #1f2937; font-size: 0.88rem; }
        .brief-card { border:1px solid rgba(118,128,145,.18); border-radius:8px; background:#f7f9fc; padding:12px 14px; min-height:132px; }
        .brief-head { display:flex; justify-content:space-between; gap:10px; align-items:flex-start; margin-bottom:8px; }
        .brief-title { font-size:0.78rem; font-weight:800; color:#243047; }
        .brief-bias { font-size:0.76rem; font-weight:700; color:#647080; text-transform:uppercase; }
        .brief-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; margin-bottom:8px; }
        .brief-kpi { background:#fff; border:1px solid rgba(118,128,145,.14); border-radius:8px; padding:8px 10px; }
        .brief-kpi-label { font-size:0.7rem; color:#6b7685; text-transform:uppercase; margin-bottom:3px; font-weight:700; }
        .brief-kpi-value { font-size:0.95rem; font-weight:800; color:#243047; }
        .brief-copy { font-size:0.84rem; color:#596474; line-height:1.45; }
        .rank-card { border:1px solid rgba(118,128,145,.18); border-radius:8px; background:#fff; padding:12px 14px; min-height:240px; }
        .rank-item { display:flex; justify-content:space-between; gap:10px; align-items:flex-start; padding:8px 0; border-bottom:1px solid rgba(118,128,145,.1); }
        .rank-item:last-child { border-bottom:none; }
        .rank-left { min-width:0; }
        .rank-name { font-size:0.86rem; font-weight:800; color:#243047; margin-bottom:2px; }
        .rank-meta { font-size:0.78rem; color:#647080; line-height:1.35; }
        .rank-score { font-size:0.9rem; font-weight:800; color:#243047; white-space:nowrap; }
        .decision-card { padding: 14px; margin-bottom: 10px; }
        .decision-head { display:flex; justify-content:space-between; gap:10px; align-items:flex-start; margin-bottom:10px; }
        .decision-ticker { font-size: 0.98rem; font-weight: 800; }
        .decision-meta { font-size: 0.8rem; color: #5f6977; }
        .decision-pill { display:inline-block; border: 1px solid rgba(95,105,119,.18); border-radius:999px; padding: 2px 8px; font-size:0.74rem; margin-right:6px; margin-bottom:6px; }
        .decision-label { font-size: 0.75rem; font-weight: 700; color: #647080; margin: 8px 0 4px; text-transform: uppercase; }
        .decision-list { margin: 0; padding-left: 18px; color: #1f2937; font-size: 0.88rem; }
        button[data-baseweb="tab"] { border-radius: 999px !important; padding: 0.35rem 0.9rem !important; font-weight: 700 !important; color: #475467 !important; }
        button[data-baseweb="tab"][aria-selected="true"] { background: #101828 !important; color: #ffffff !important; }
        div[data-testid="stMetric"] { background:#f7f9fc; border:1px solid rgba(118,128,145,.18); border-radius:8px; padding:10px 12px; }
        div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
        @media (max-width: 1200px) {
            section[data-testid="stSidebar"] { min-width: 290px !important; max-width: 290px !important; }
            .page-title { font-size: 1.55rem; }
            .block-container { padding-top: 2.4rem; }
            .hero-summary-band { grid-template-columns:1fr 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_analysis_summary(summary: AnalysisRunSummary) -> str:
    if LANG == "zh-TW":
        return (
            f"掃描 {summary.scanned_tickers} 檔 | "
            f"有資料 {summary.data_ready_tickers} 檔 | "
            f"資料不足 {summary.skipped_data_tickers} 檔 | "
            f"未入選 {summary.no_signal_tickers} 檔 | "
            f"寫入 {summary.signal_count} 筆"
        )
    return (
        f"Scanned {summary.scanned_tickers} | "
        f"Data-ready {summary.data_ready_tickers} | "
        f"Missing {summary.skipped_data_tickers} | "
        f"No-signal {summary.no_signal_tickers} | "
        f"Written {summary.signal_count}"
    )


def format_skip_reasons(reason_counts: dict[str, int]) -> str:
    if not reason_counts:
        return ""
    labels = {
        "no_market_data": "查無市場資料" if LANG == "zh-TW" else "no market data",
        "incomplete_history": "歷史資料不足" if LANG == "zh-TW" else "incomplete history",
        "request_timeout": "來源逾時" if LANG == "zh-TW" else "request timeout",
        "provider_error": "來源異常" if LANG == "zh-TW" else "provider error",
    }
    ordered = sorted(reason_counts.items(), key=lambda item: item[1], reverse=True)
    return " | ".join(f"{labels.get(key, key)} {count}" for key, count in ordered)


def format_no_signal_reasons(reason_counts: dict[str, int]) -> str:
    if not reason_counts:
        return ""
    labels = {
        "core_below_60ma": "核心池跌破 60MA" if LANG == "zh-TW" else "core below 60MA",
        "core_60ma_not_rising": "核心池 60MA 未上彎" if LANG == "zh-TW" else "core 60MA not rising",
        "explore_below_60ma": "觀察池跌破 60MA" if LANG == "zh-TW" else "explore below 60MA",
        "explore_growth_missing": "觀察池營收 / EPS 未過底線" if LANG == "zh-TW" else "explore growth baseline failed",
        "no_institutional_buy_streak": "近 3 日法人淨買超未轉正" if LANG == "zh-TW" else "3-day institutional flow not positive",
        "below_20ma": "收盤仍在 20MA 下方" if LANG == "zh-TW" else "price still below 20MA",
        "volume_below_5d_avg": "量能未高於 5 日均量" if LANG == "zh-TW" else "volume below the 5-day average",
        "explore_waiting_for_trigger": "觀察池已過底線，但尚未觸發型態" if LANG == "zh-TW" else "explore passed baseline but has no trigger",
        "no_strategy_trigger": "未觸發任一進場型態" if LANG == "zh-TW" else "no trigger",
        "market_risk_off": "大盤 Risk-Off，轉入防守觀察" if LANG == "zh-TW" else "market risk-off",
        "wait_pullback_to_20ma": "分數夠高，但乖離過大，等回測 20MA" if LANG == "zh-TW" else "wait for pullback to 20MA",
        "wait_for_institutional_confirmation": "VCP 已到位，但法人尚未明確跟進" if LANG == "zh-TW" else "wait for institutional confirmation",
        "score_borderline_65_74": "已觸發型態，但綜合分數落在 65-74" if LANG == "zh-TW" else "score between 65 and 74",
        "triggered_but_low_score": "已觸發型態，但健康分數仍偏弱" if LANG == "zh-TW" else "triggered but score too low",
    }
    ordered = sorted(reason_counts.items(), key=lambda item: item[1], reverse=True)
    return " | ".join(f"{labels.get(key, key)} {count}" for key, count in ordered)


def _stage_name_label(stage: str) -> str:
    mapping = {
        "baseline_reject": "第一階段淘汰" if LANG == "zh-TW" else "Baseline Reject",
        "watch": "觀察" if LANG == "zh-TW" else "Watch",
        "candidate": "差臨門一腳" if LANG == "zh-TW" else "Candidate",
        "actionable": "今日可執行" if LANG == "zh-TW" else "Actionable",
    }
    return mapping.get(stage, stage)


def _stage_reason_label(reason: str) -> str:
    mapping = {
        "core_below_60ma": "核心池跌破 60MA" if LANG == "zh-TW" else "core below 60MA",
        "core_60ma_not_rising": "核心池 60MA 未上彎" if LANG == "zh-TW" else "core 60MA not rising",
        "explore_below_60ma": "觀察池跌破 60MA" if LANG == "zh-TW" else "explore below 60MA",
        "explore_growth_missing": "觀察池營收 / EPS 未過底線" if LANG == "zh-TW" else "explore growth baseline failed",
        "panic_exception_baseline_ok": "恐慌極端反轉例外" if LANG == "zh-TW" else "panic reversal exception",
        "core_trend_template_ok": "核心池底線通過" if LANG == "zh-TW" else "core baseline passed",
        "explore_baseline_ok": "觀察池底線通過" if LANG == "zh-TW" else "explore baseline passed",
        "no_institutional_buy_streak": "近 3 日法人淨買超未轉正" if LANG == "zh-TW" else "3-day institutional flow not positive",
        "below_20ma": "收盤仍在 20MA 下方" if LANG == "zh-TW" else "below 20MA",
        "volume_below_5d_avg": "量能未高於 5 日均量" if LANG == "zh-TW" else "volume below the 5-day average",
        "explore_waiting_for_trigger": "觀察池已過底線，但未出現進場型態" if LANG == "zh-TW" else "explore waiting for trigger",
        "no_strategy_trigger": "未觸發任一進場型態" if LANG == "zh-TW" else "no trigger",
        "market_risk_off": "大盤偏 Risk-Off，先以防守為主" if LANG == "zh-TW" else "market risk-off",
        "ready_now": "條件完整，可直接執行" if LANG == "zh-TW" else "ready now",
        "wait_pullback_to_20ma": "乖離過大，等量縮回測 20MA" if LANG == "zh-TW" else "wait pullback to 20MA",
        "wait_for_institutional_confirmation": "VCP 已到位，等待法人跟單" if LANG == "zh-TW" else "wait for institutional confirmation",
        "score_borderline_65_74": "分數落在 65-74，差臨門一腳" if LANG == "zh-TW" else "score borderline 65-74",
        "triggered_but_low_score": "型態出現，但整體健康度仍不足" if LANG == "zh-TW" else "triggered but low score",
    }
    return mapping.get(reason, reason)


def _trigger_label_list(values: list[str]) -> str:
    mapping = {
        "SMART_MONEY_TREND": "法人順勢動能" if LANG == "zh-TW" else "Smart Money Trend",
        "VCP_BREAKOUT": "VCP 量縮突破" if LANG == "zh-TW" else "VCP Breakout",
        "PANIC_REVERSAL": "恐慌極端反轉" if LANG == "zh-TW" else "Panic Reversal",
    }
    if not values:
        return "—"
    return " / ".join(mapping.get(value, value) for value in values)


def _format_stage_counts(stage_counts: dict[str, int]) -> str:
    if not stage_counts:
        return ""
    parts: list[str] = []
    for key in ["baseline_reject", "watch", "candidate", "actionable"]:
        if key in stage_counts:
            parts.append(f"{_stage_name_label(key)} {stage_counts[key]}")
    return " | ".join(parts)


def render_funnel_stage_table(summary: AnalysisRunSummary) -> None:
    stage_rows = getattr(summary, "stage_rows", None) or []
    if not stage_rows:
        return
    frame = pd.DataFrame(stage_rows)
    if frame.empty:
        return
    frame = enrich_with_company_metadata(frame)
    frame["stage_label"] = frame["stage"].map(_stage_name_label)
    frame["reason_label"] = frame["reason"].map(_stage_reason_label)
    frame["triggers_label"] = frame["triggers"].apply(lambda values: _trigger_label_list(list(values) if isinstance(values, list) else []))
    frame["fundamental_snapshot"] = frame.apply(
        lambda row: (
            f"營收 YoY {float(row['revenue_yoy']):.1f}% / EPS {float(row['eps_ttm']):.2f}"
            if LANG == "zh-TW" and pd.notna(row.get("revenue_yoy")) and pd.notna(row.get("eps_ttm"))
            else (
                f"Revenue YoY {float(row['revenue_yoy']):.1f}% / EPS {float(row['eps_ttm']):.2f}"
                if pd.notna(row.get("revenue_yoy")) and pd.notna(row.get("eps_ttm"))
                else "—"
            )
        ),
        axis=1,
    )
    display = frame[
        [
            "ticker",
            "company",
            "sector",
            "universe_bucket",
            "stage_label",
            "triggers_label",
            "composite_signal_score",
            "relative_strength_score",
            "institutional_buy_streak",
            "fundamental_snapshot",
            "reason_label",
        ]
    ].rename(
        columns={
            "ticker": "代號" if LANG == "zh-TW" else "Ticker",
            "company": "公司" if LANG == "zh-TW" else "Company",
            "sector": "類股" if LANG == "zh-TW" else "Sector",
            "universe_bucket": "池別" if LANG == "zh-TW" else "Pool",
            "stage_label": "漏斗階段" if LANG == "zh-TW" else "Stage",
            "triggers_label": "觸發型態" if LANG == "zh-TW" else "Trigger",
            "composite_signal_score": "綜合分數" if LANG == "zh-TW" else "Score",
            "relative_strength_score": "相對強度" if LANG == "zh-TW" else "RS",
            "institutional_buy_streak": "法人連買天數" if LANG == "zh-TW" else "Buy Streak",
            "fundamental_snapshot": "基本面快照" if LANG == "zh-TW" else "Fundamental Snapshot",
            "reason_label": "未入選 / 歸類原因" if LANG == "zh-TW" else "Reason",
        }
    )
    display = display.fillna("")
    for column in display.columns:
        display[column] = display[column].map(lambda value: "" if value is None else str(value))
    st.markdown(f'<div class="section-label">{"漏斗過程" if LANG == "zh-TW" else "Funnel Trail"}</div>', unsafe_allow_html=True)
    st.dataframe(display, use_container_width=True, hide_index=True)


def _analysis_cooldown_key(market_type: str) -> str:
    return f"analysis_last_run_{market_type}"


def should_skip_recent_analysis(market_type: str, force_refresh: bool, cooldown_minutes: int = 20) -> bool:
    if force_refresh:
        return False
    last_run = st.session_state.get(_analysis_cooldown_key(market_type))
    if not isinstance(last_run, datetime):
        return False
    return datetime.now() - last_run < timedelta(minutes=cooldown_minutes)


def run_market_analysis(
    market_type: str,
    progress_bar: Any | None = None,
    status_box: Any | None = None,
    force_refresh: bool = False,
) -> AnalysisRunSummary | None:
    if should_skip_recent_analysis(market_type, force_refresh=force_refresh):
        _set_analysis_feedback("info", t("cooldown_skip"))
        return None
    universe = UniverseBuilder(runtime_settings).build(market_type)
    engine = AnalysisEngine(
        event_risk_service=EventRiskService(high_risk_event_dates=runtime_settings.high_risk_event_dates)
    )

    def on_progress(stage: str, current: int, total: int, detail: str) -> None:
        if progress_bar is not None:
            if stage == "done":
                progress_bar.progress(100)
            else:
                pct = 5 if total <= 0 else min(95, max(5, int((current / max(total, 1)) * 100)))
                progress_bar.progress(pct)
        if status_box is not None:
            status_box.info(f"{t('analysis_progress')} | {detail}")

    summary = engine.run_with_summary(universe.to_analysis_universe(), progress_callback=on_progress)
    if progress_bar is not None:
        progress_bar.progress(100)
    st.session_state[_analysis_cooldown_key(market_type)] = datetime.now()
    return summary


def _set_analysis_feedback(kind: str, message: str) -> None:
    st.session_state["analysis_feedback"] = {"kind": kind, "message": message}


def render_analysis_feedback() -> None:
    feedback = st.session_state.pop("analysis_feedback", None)
    if not feedback:
        return
    kind = feedback.get("kind", "info")
    message = str(feedback.get("message", ""))
    if kind == "success":
        st.success(message)
    elif kind == "warning":
        st.warning(message)
    elif kind == "error":
        st.error(message)
    else:
        st.info(message)


def render_analysis_summary(summary: AnalysisRunSummary) -> None:
    st.markdown(f'<div class="section-label">{t("analysis_summary")}</div>', unsafe_allow_html=True)
    scanned_tickers = int(getattr(summary, "scanned_tickers", 0) or 0)
    data_ready_tickers = int(getattr(summary, "data_ready_tickers", 0) or 0)
    skipped_data_tickers = int(getattr(summary, "skipped_data_tickers", 0) or 0)
    no_signal_tickers = int(getattr(summary, "no_signal_tickers", 0) or 0)
    signal_count = int(getattr(summary, "signal_count", 0) or 0)
    skipped_reason_counts = getattr(summary, "skipped_reason_counts", {}) or {}
    no_signal_reason_counts = getattr(summary, "no_signal_reason_counts", {}) or {}
    core_ticker_count = int(getattr(summary, "core_ticker_count", 0) or 0)
    explore_ticker_count = int(getattr(summary, "explore_ticker_count", 0) or 0)
    stage_counts = getattr(summary, "stage_counts", {}) or {}

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("掃描" if LANG == "zh-TW" else "Scanned", scanned_tickers)
    c2.metric("有資料" if LANG == "zh-TW" else "Data Ready", data_ready_tickers)
    c3.metric("資料不足" if LANG == "zh-TW" else "Missing", skipped_data_tickers)
    c4.metric("未入選" if LANG == "zh-TW" else "No Signal", no_signal_tickers)
    c5.metric(t("records"), signal_count)
    summary_at = str(st.session_state.get("analysis_summary_at") or "")
    if summary_at:
        _render_data_caption(f'{t("page_rendered_at")}: {summary_at}')
    if core_ticker_count or explore_ticker_count:
        if LANG == "zh-TW":
            st.caption(f"核心池 {core_ticker_count} 檔、觀察池 {explore_ticker_count} 檔。這些是掃描宇宙，不是保證最後會入選。")
        else:
            st.caption(
                f"Scanned {core_ticker_count} core names and {explore_ticker_count} explore names. "
                f"These lists define the universe, not guaranteed outputs."
            )
    if stage_counts:
        st.caption(("漏斗分佈：" if LANG == "zh-TW" else "Funnel counts: ") + _format_stage_counts(stage_counts))
    if skipped_reason_counts:
        st.caption(("資料不足原因：" if LANG == "zh-TW" else "Missing-data reasons: ") + format_skip_reasons(skipped_reason_counts))
    if no_signal_reason_counts:
        st.caption(("未入選主因：" if LANG == "zh-TW" else "Main no-signal reasons: ") + format_no_signal_reasons(no_signal_reason_counts))
    if signal_count == 0:
        if data_ready_tickers == 0:
            st.warning("流程有跑完，但沒有拿到足夠可用資料。" if LANG == "zh-TW" else "Execution completed, but no usable market data was available.")
        else:
            st.info(
                "流程有跑完，但目前沒有股票同時通過底線、型態、分數與風險檢查。"
                if LANG == "zh-TW"
                else "Execution completed, but no names passed the baseline, trigger, score, and risk filters together."
            )
    else:
        pass_rate = (signal_count / scanned_tickers * 100) if scanned_tickers else 0.0
        st.info(
            (
                f"最後只有 {signal_count} 檔進入結果，不代表偏好池失效，而是只有 {pass_rate:.1f}% 同時通過底線、觸發、分數與風險門檻。"
                if LANG == "zh-TW"
                else f"Only {signal_count} names survived. That means {pass_rate:.1f}% cleared baseline, trigger, score, and risk checks."
            )
        )
    render_funnel_stage_table(summary)


def load_candidate_frame(limit: int = 220) -> pd.DataFrame:
    frame = pd.DataFrame(repo.fetch_recent_candidates(limit=limit))
    if frame.empty:
        return frame
    frame = pd.DataFrame(decision_support.enrich_rows(frame.to_dict("records")))
    defaults = {
        "recommendation_bucket": "Watchlist",
        "universe_bucket": "core",
        "market_regime": "Unknown",
        "event_risk_note": "clear",
        "institutional_buy_streak": 0,
        "composite_signal_score": 0.0,
        "relative_strength_score": 0.0,
        "entry_quality_score": 0.0,
    }
    for column, default in defaults.items():
        if column not in frame.columns:
            frame[column] = default
        else:
            frame[column] = frame[column].fillna(default)
    return frame


def filter_candidate_frame_for_market(candidate_frame: pd.DataFrame, market_key: str) -> pd.DataFrame:
    if candidate_frame.empty or "type" not in candidate_frame.columns:
        return candidate_frame.copy()
    return candidate_frame[candidate_frame["type"].astype(str).str.lower() == market_key].copy()


def _parse_runtime_tickers(raw_value: object) -> list[str]:
    return [item.strip().upper() for item in str(raw_value or "").split(",") if item.strip()]


def render_run_controls() -> None:
    st.markdown(f'<div class="section-label">{t("run_analysis")}</div>', unsafe_allow_html=True)
    st.caption(t("cooldown_force_hint"))
    force_refresh = st.checkbox(t("force_refresh"), value=False, key="force_refresh_history")
    left, right = st.columns(2)
    if left.button(t("run_tw"), use_container_width=True):
        try:
            progress_bar = st.progress(0)
            status_box = st.empty()
            summary = run_market_analysis("tw", progress_bar=progress_bar, status_box=status_box, force_refresh=force_refresh)
            status_box.empty()
            progress_bar.empty()
            if summary is None:
                st.rerun()
            if summary.signal_count > 0:
                _set_analysis_feedback("success", f'{t("analysis_done")} | {format_analysis_summary(summary)}')
            else:
                _set_analysis_feedback("warning", f'{t("analysis_done")} | {format_analysis_summary(summary)}')
            st.session_state["analysis_summary"] = summary
            st.session_state["analysis_summary_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.rerun()
        except Exception as exc:
            _set_analysis_feedback("error", f'{t("analysis_failed")}: {exc}')
            st.rerun()
    if right.button(t("run_us"), use_container_width=True):
        try:
            progress_bar = st.progress(0)
            status_box = st.empty()
            summary = run_market_analysis("us", progress_bar=progress_bar, status_box=status_box, force_refresh=force_refresh)
            status_box.empty()
            progress_bar.empty()
            if summary is None:
                st.rerun()
            if summary.signal_count > 0:
                _set_analysis_feedback("success", f'{t("analysis_done")} | {format_analysis_summary(summary)}')
            else:
                _set_analysis_feedback("warning", f'{t("analysis_done")} | {format_analysis_summary(summary)}')
            st.session_state["analysis_summary"] = summary
            st.session_state["analysis_summary_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.rerun()
        except Exception as exc:
            _set_analysis_feedback("error", f'{t("analysis_failed")}: {exc}')
            st.rerun()


def render_runtime_settings_panel() -> None:
    with st.sidebar.expander(t("settings_panel")):
        with st.form("runtime_settings_form"):
            app_language = st.selectbox(
                t("language"),
                options=["zh-TW", "en"],
                index=0 if runtime_settings.app_language == "zh-TW" else 1,
            )
            tw_core_tickers = st.text_area("TW Core", value=str(runtime_settings.tw_core_tickers), height=90)
            us_core_tickers = st.text_area("US Core", value=str(runtime_settings.us_core_tickers), height=80)
            tw_explore_tickers = st.text_area("TW Explore", value=str(runtime_settings.tw_explore_tickers), height=70)
            us_explore_tickers = st.text_area("US Explore", value=str(runtime_settings.us_explore_tickers), height=70)
            tw_explore_limit = st.number_input(
                "TW Explore Limit", min_value=1, max_value=30, value=int(runtime_settings.tw_explore_limit), step=1
            )
            us_explore_limit = st.number_input(
                "US Explore Limit", min_value=1, max_value=30, value=int(runtime_settings.us_explore_limit), step=1
            )
            tw_manual_watch_tickers = st.text_area(
                "TW Manual Watch",
                value=str(getattr(runtime_settings, "tw_manual_watch_tickers", "")),
                height=65,
            )
            us_manual_watch_tickers = st.text_area(
                "US Manual Watch",
                value=str(getattr(runtime_settings, "us_manual_watch_tickers", "")),
                height=65,
            )
            tw_manual_hot_tickers = st.text_area(
                "TW Manual Hot",
                value=str(getattr(runtime_settings, "tw_manual_hot_tickers", "")),
                height=65,
            )
            us_manual_hot_tickers = st.text_area(
                "US Manual Hot",
                value=str(getattr(runtime_settings, "us_manual_hot_tickers", "")),
                height=65,
            )
            st.caption("FMP economic calendar is used first. This field is only for manual fallback or custom override dates.")
            high_risk_event_dates = st.text_input(t("high_risk_dates"), value=str(runtime_settings.high_risk_event_dates))
            submitted = st.form_submit_button(t("save_settings"), use_container_width=True)
        if submitted:
            user_settings_service.update_runtime_preferences(
                chat_id,
                {
                    "app_language": app_language,
                    "tw_core_tickers": tw_core_tickers,
                    "us_core_tickers": us_core_tickers,
                    "tw_explore_tickers": tw_explore_tickers,
                    "us_explore_tickers": us_explore_tickers,
                    "tw_explore_limit": int(tw_explore_limit),
                    "us_explore_limit": int(us_explore_limit),
                    "tw_manual_watch_tickers": tw_manual_watch_tickers,
                    "us_manual_watch_tickers": us_manual_watch_tickers,
                    "tw_manual_hot_tickers": tw_manual_hot_tickers,
                    "us_manual_hot_tickers": us_manual_hot_tickers,
                    "high_risk_event_dates": high_risk_event_dates,
                },
            )
            st.success(t("settings_saved"))
            st.rerun()


def render_market_state() -> None:
    overview = overview_service.build()
    vix_value = market_data.get_vix_value()
    render_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tw_summary = summary_service.build_market_summary("tw")
    us_summary = summary_service.build_market_summary("us")
    vix_zone, vix_copy = describe_vix(vix_value)
    fear_greed_label, fear_greed_copy, _ = describe_fear_greed(overview.fear_greed_score)
    fear_greed_source = getattr(overview, "fear_greed_source", "CNN Fear & Greed Index")
    fear_greed_updated_at = getattr(overview, "fear_greed_updated_at", "")

    def _format_detail_time(value: str) -> str:
        if not value:
            return "—"
        try:
            parsed = pd.to_datetime(value)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return value

    st.markdown(f'<div class="section-label">{t("market_state")}</div>', unsafe_allow_html=True)
    freshness_bits = [f'{t("page_rendered_at")}: {render_time}', t("intraday_source_note")]
    for summary in (tw_summary, us_summary):
        if summary is not None:
            freshness_bits.append(f'{summary.market_type.upper()}: {_format_snapshot_date(summary.summary_date)}')
    _render_data_caption(*freshness_bits)
    momentum_items = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in overview.momentum_zones) or f"<li>{t('no_data')}</li>"
    macro_items = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in overview.upcoming_macro_events) or f"<li>{t('no_data')}</li>"
    caution_items = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in overview.caution_items)
    left_card, right_card = st.columns(2)
    with left_card:
        with st.container(border=True):
            st.markdown(f"**{t('fear_greed')}**")
            _render_data_caption(
                f"來源: {fear_greed_source}" if LANG == "zh-TW" else f"Source: {fear_greed_source}",
                f"更新時間: {_format_detail_time(fear_greed_updated_at)}" if LANG == "zh-TW" else f"Updated: {_format_detail_time(fear_greed_updated_at)}",
            )
            st.plotly_chart(
                build_fear_greed_gauge(overview.fear_greed_score),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            st.markdown(
                f"""
                <div class="state-read">
                    <div class="state-read-title">{t("market_read")}</div>
                    <div class="state-read-main">{fear_greed_label} / {localize_value(overview.sentiment_label)}</div>
                    <div class="state-read-copy">{fear_greed_copy}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with right_card:
        with st.container(border=True):
            st.markdown("**VIX**")
            _render_data_caption(
                "來源: CBOE / Yahoo Finance" if LANG == "zh-TW" else "Source: CBOE / Yahoo Finance",
                f"頁面抓取時間: {render_time}" if LANG == "zh-TW" else f"Fetched: {render_time}",
            )
            st.plotly_chart(
                build_vix_gauge(vix_value),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            st.markdown(
                f"""
                <div class="state-read">
                    <div class="state-read-title">{t("vix_zone")}</div>
                    <div class="state-read-main">{vix_zone}</div>
                    <div class="state-read-copy">{vix_copy}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown(
        f"""
        <div class="terminal-card">
            <div class="state-grid">
                <div class="state-metric">
                    <div class="state-label">{t("overall_trend")}</div>
                    <div class="state-value">{localize_value(overview.overall_trend)}</div>
                </div>
                <div class="state-metric">
                    <div class="state-label">{t("sentiment")}</div>
                    <div class="state-value">{localize_value(overview.sentiment_label)}</div>
                </div>
                <div class="state-metric">
                    <div class="state-label">{t("fear_greed")}</div>
                    <div class="state-value">{overview.fear_greed_score}/100</div>
                </div>
                <div class="state-metric">
                    <div class="state-label">{t("breadth")}</div>
                    <div class="state-value">{overview.breadth_snapshot:.2f}</div>
                </div>
            </div>
            <div class="decision-label">{t("momentum_zones")}</div>
            <ul class="mini-list">{momentum_items}</ul>
            <div class="decision-label">{t("macro_calendar")}</div>
            <ul class="mini-list">{macro_items}</ul>
            <div class="decision-label">{t("cautions")}</div>
            <ul class="mini-list">{caution_items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_band(label: str, summary: Any) -> None:
    if summary is None:
        st.info(t("no_data"))
        return
    _render_data_caption(f'{t("snapshot_as_of")}: {_format_snapshot_date(getattr(summary, "summary_date", ""))}')
    st.markdown(
        f"""
        <div class="summary-band">
            <div class="summary-title">{label}</div>
            <div class="summary-main">{localize_value(summary.regime)}</div>
            <div class="summary-sub">
                {t("breadth")} {summary.average_breadth:.2f} |
                {t("candidates")} {summary.candidate_count} |
                {t("actionable")} {summary.actionable_count} |
                {t("safer")} {summary.safer_count}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_market_overview() -> None:
    st.markdown(f'<div class="section-label">{t("market_overview")}</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        render_summary_band(t("taiwan"), summary_service.build_market_summary("tw"))
    with right:
        render_summary_band(t("us"), summary_service.build_market_summary("us"))


def render_market_terminal_header(snapshot: Any, overview: Any) -> str:
    selected_market = _render_segmented_control(
        t("dashboard_market_view"),
        [t("taiwan"), t("us")],
        format_func=lambda value: value,
        key="dashboard_market_view",
    )
    market_key = "tw" if selected_market == t("taiwan") else "us"
    selected_range_key = _render_segmented_control(
        t("benchmark_range"),
        [key for key, _ in BENCHMARK_RANGE_OPTIONS],
        format_func=lambda key: t(dict(BENCHMARK_RANGE_OPTIONS)[key]),
        key=f"benchmark_range_{market_key}",
    )
    summary = summary_service.build_market_summary(market_key)
    benchmark_pairs = BENCHMARK_SETS[market_key]
    benchmark_snapshots = load_benchmark_snapshots(benchmark_pairs, selected_range_key)
    now_label = datetime.now().strftime("%m/%d %H:%M")
    summary_text = _market_bias_copy(summary) if summary else t("no_data")
    summary_date = _format_snapshot_date(getattr(summary, "summary_date", "")) if summary else "—"
    summary_breadth = f"{float(summary.average_breadth):.2f}" if summary is not None else "—"
    summary_candidates = str(int(getattr(summary, "candidate_count", 0))) if summary is not None else "—"
    summary_actionable = str(int(getattr(summary, "actionable_count", 0))) if summary is not None else "—"
    summary_safer = str(int(getattr(summary, "safer_count", 0))) if summary is not None else "—"

    st.markdown(
        f"""
        <div class="hero-shell">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;">
                <div>
                    <div class="hero-title">{selected_market}</div>
                    <div class="hero-sub">{t("market_terminal")} | {localize_value(overview.overall_trend)}</div>
                </div>
                <div class="hero-time">{now_label} ({selected_market})</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    card_columns = st.columns(3)
    for column, (symbol, label_key) in zip(card_columns, benchmark_pairs):
        benchmark = benchmark_snapshots.get(
            symbol,
            {
                "label_key": label_key,
                "latest": None,
                "delta": None,
                "pct": None,
                "trend": [],
                "trend_window": 0,
                "range_key": selected_range_key,
                "has_data": False,
                "start_at": None,
                "end_at": None,
            },
        )
        positive = float(benchmark["delta"] or 0) >= 0
        change_color = "#16a34a" if positive else "#ef4444"
        delta_prefix = "+" if float(benchmark["delta"] or 0) >= 0 else ""
        with column:
            if benchmark.get("has_data"):
                st.markdown(
                    f"""
                    <div class="benchmark-card">
                        <div class="benchmark-name">{t(str(benchmark["label_key"]))}</div>
                        <div class="benchmark-price">{float(benchmark["latest"]):,.2f}</div>
                        <div class="benchmark-change" style="color:{change_color};">{delta_prefix}{float(benchmark["delta"]):.2f}  {delta_prefix}{float(benchmark["pct"]):.2f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.plotly_chart(
                    build_benchmark_chart(benchmark["trend"], positive),
                    use_container_width=True,
                    config={"displayModeBar": False},
                    key=f"benchmark_chart_{market_key}_{selected_range_key}_{benchmark['label_key']}",
                )
                st.caption(_benchmark_range_caption(str(benchmark.get("range_key", "1d")), int(benchmark.get("trend_window", 0) or 0)))
                start_at = str(benchmark.get("start_at") or "")
                end_at = str(benchmark.get("end_at") or "")
                if start_at and end_at:
                    st.caption(f"{start_at} -> {end_at}")
            else:
                st.markdown(
                    f"""
                    <div class="benchmark-card">
                        <div class="benchmark-name">{t(str(benchmark["label_key"]))}</div>
                        <div class="benchmark-price">N/A</div>
                        <div class="benchmark-change" style="color:#94a3b8;">{t("benchmark_no_data")}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown(
        f"""
        <div class="hero-summary-band">
            <div class="hero-summary-card main">
                <div class="hero-summary-title">{t("analysis_summary")}</div>
                <div class="hero-summary-main">{localize_value(overview.sentiment_label)} / {overview.fear_greed_score}</div>
                <div class="hero-summary-copy">{summary_text}</div>
                <div class="hero-summary-copy" style="margin-top:10px;">
                    {t("latest_analysis_date")}: {summary_date}<br/>
                    {t("breadth")}: {summary_breadth}
                </div>
            </div>
            <div class="hero-summary-card">
                <div class="hero-summary-kpi-label">{t("overall_trend")}</div>
                <div class="hero-summary-kpi-value">{localize_value(overview.overall_trend)}</div>
            </div>
            <div class="hero-summary-card">
                <div class="hero-summary-kpi-label">{t("candidates")}</div>
                <div class="hero-summary-kpi-value">{summary_candidates}</div>
            </div>
            <div class="hero-summary-card">
                <div class="hero-summary-kpi-label">{t("actionable")}</div>
                <div class="hero-summary-kpi-value">{summary_actionable}</div>
            </div>
            <div class="hero-summary-card">
                <div class="hero-summary-kpi-label">{t("safer")}</div>
                <div class="hero-summary-kpi-value">{summary_safer}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return market_key


def render_session_briefs() -> None:
    tw_summary = summary_service.build_market_summary("tw")
    us_summary = summary_service.build_market_summary("us")
    st.markdown(f'<div class="section-label">{t("session_brief")}</div>', unsafe_allow_html=True)
    dates = []
    for summary in (tw_summary, us_summary):
        if summary is not None:
            dates.append(f'{summary.market_type.upper()}: {_format_snapshot_date(summary.summary_date)}')
    if dates:
        _render_data_caption(*dates)
    left, right = st.columns(2)
    for column, title, summary in (
        (left, t("tw_brief"), tw_summary),
        (right, t("us_brief"), us_summary),
    ):
        with column:
            if summary is None:
                st.info(t("no_data"))
                continue
            best_score = max((float(row.get("composite_signal_score", 0)) for row in summary.top_rows), default=0.0)
            avg_signal_score = (
                sum(float(row.get("composite_signal_score", 0)) for row in summary.top_rows) / len(summary.top_rows)
                if summary.top_rows
                else 0.0
            )
            st.markdown(
                f"""
                <div class="brief-card">
                    <div class="brief-head">
                        <div class="brief-title">{title}</div>
                        <div class="brief-bias">{localize_value(summary.regime)}</div>
                    </div>
                    <div class="brief-grid">
                        <div class="brief-kpi">
                            <div class="brief-kpi-label">{t("avg_score")}</div>
                            <div class="brief-kpi-value">{avg_signal_score:.1f}</div>
                        </div>
                        <div class="brief-kpi">
                            <div class="brief-kpi-label">{t("actionable")}</div>
                            <div class="brief-kpi-value">{summary.actionable_count}</div>
                        </div>
                        <div class="brief-kpi">
                            <div class="brief-kpi-label">{t("best_score")}</div>
                            <div class="brief-kpi-value">{best_score:.1f}</div>
                        </div>
                    </div>
                    <div class="brief-copy">{_market_bias_copy(summary)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_visual_scan(candidate_frame: pd.DataFrame, snapshot: Any, overview: Any) -> None:
    st.markdown(f'<div class="section-label">{t("visual_scan")}</div>', unsafe_allow_html=True)
    latest_date = _format_snapshot_date(candidate_frame["date"].max()) if not candidate_frame.empty and "date" in candidate_frame.columns else ""
    if latest_date:
        _render_data_caption(f'{t("snapshot_as_of")}: {latest_date}')
    lights = [
        (t("overall_trend"), localize_value(overview.overall_trend), *(_signal_tone(float(overview.fear_greed_score))), "總體盤勢" if LANG == "zh-TW" else "Macro tape"),
        (t("fear_greed"), f"{overview.fear_greed_score}/100", *(_signal_tone(float(overview.fear_greed_score))), "分數越高代表風險偏好越強" if LANG == "zh-TW" else "Higher means more risk appetite"),
        (t("breadth"), f"{overview.breadth_snapshot:.0f}/100", *(_signal_tone(float(overview.breadth_snapshot))), "分數越高代表參與面越廣" if LANG == "zh-TW" else "Higher breadth means broader participation"),
        ("VIX", f"{snapshot.vix:.2f}" if snapshot.vix is not None else "N/A", *(_signal_tone(_vix_comfort_score(snapshot.vix))), "VIX 越低通常越容易順勢操作" if LANG == "zh-TW" else "Lower VIX is usually easier"),
    ]
    light_columns = st.columns(4)
    for column, (name, value, color, tone, copy) in zip(light_columns, lights):
        with column:
            st.markdown(
                f"""
                <div class="light-card">
                    <div class="light-top">
                        <div class="light-name">{name}</div>
                        <span class="light-dot" style="background:{color}"></span>
                    </div>
                    <div class="light-value">{value}</div>
                    <div class="light-copy">{tone} | {copy}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    left, middle, right = st.columns((1, 1.1, 1))
    with left:
        st.markdown(f'<div class="section-label">{t("market_pulse")}</div>', unsafe_allow_html=True)
        st.plotly_chart(build_market_pulse_chart(snapshot, overview, candidate_frame), use_container_width=True, config={"displayModeBar": False}, key="scan_visual_market_pulse")
    with middle:
        st.markdown(f'<div class="section-label">{t("sector_heatmap")}</div>', unsafe_allow_html=True)
        st.plotly_chart(build_sector_heatmap(candidate_frame), use_container_width=True, config={"displayModeBar": False}, key="scan_visual_sector_heatmap")
    with right:
        st.markdown(f'<div class="section-label">{t("setup_distribution")}</div>', unsafe_allow_html=True)
        st.plotly_chart(build_setup_distribution_chart(candidate_frame), use_container_width=True, config={"displayModeBar": False}, key="scan_visual_setup_distribution")


def _render_rank_items(rows: list[dict[str, object]], score_key: str = "composite_signal_score", meta_mode: str = "leader") -> None:
    if not rows:
        st.info(t("no_data"))
        return
    for row in rows[:6]:
        company, sector = _display_name_for_row(pd.Series(row))
        score = float(row.get(score_key, 0) or 0)
        trend = get_ticker_score_trend_cached(str(row.get("ticker", "")))
        delta = ""
        if len(trend) >= 2:
            change = trend[-1] - trend[-2]
            delta = f" | {'+' if change >= 0 else ''}{change:.1f}"
        meta = (
            f"{sector} | {localize_value(row.get('recommendation_bucket', 'Watchlist'))}"
            if meta_mode == "leader"
            else f"{sector} | {localize_value(row.get('event_risk_note', 'clear'))}"
        )
        st.markdown(
            f"""
            <div class="rank-item">
                <div class="rank-left">
                    <div class="rank-name">{company}</div>
                    <div class="rank-meta">{row.get('ticker', '')} | {meta}</div>
                </div>
                <div class="rank-score">{score:.1f}{delta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_rank_boards(market_key: str | None = None) -> None:
    if market_key in {"tw", "us"}:
        summaries = [summary_service.build_market_summary(market_key)]
    else:
        summaries = [
            summary_service.build_market_summary("tw"),
            summary_service.build_market_summary("us"),
        ]
    leader_rows: list[dict[str, object]] = []
    risk_rows: list[dict[str, object]] = []
    for summary in summaries:
        if summary is None:
            continue
        leader_rows.extend(summary.top_rows)
        risk_rows.extend(summary.risk_rows)
    leader_rows = sorted(leader_rows, key=lambda row: float(row.get("composite_signal_score", 0) or 0), reverse=True)[:6]
    leader_tickers = {str(row.get("ticker", "")) for row in leader_rows}
    risk_rows = sorted(
        [row for row in risk_rows if str(row.get("ticker", "")) not in leader_tickers],
        key=lambda row: (float(row.get("event_risk_score", 50) or 50), float(row.get("composite_signal_score", 0) or 0)),
    )[:6]
    st.markdown(f'<div class="section-label">{t("rank_board")}</div>', unsafe_allow_html=True)
    dates = []
    for summary in summaries:
        if summary is not None:
            dates.append(f'{summary.market_type.upper()}: {_format_snapshot_date(summary.summary_date)}')
    if dates:
        _render_data_caption(*dates)
    left, right = st.columns(2)
    with left:
        st.markdown(f'<div class="section-label">{t("leader_board")}</div>', unsafe_allow_html=True)
        st.caption(t("leader_board_help"))
        with st.container(border=True):
            _render_rank_items(leader_rows, meta_mode="leader")
    with right:
        st.markdown(f'<div class="section-label">{t("risk_board")}</div>', unsafe_allow_html=True)
        st.caption(t("risk_board_help"))
        with st.container(border=True):
            if risk_rows:
                _render_rank_items(risk_rows, meta_mode="risk")
            else:
                st.info("目前沒有與領先名單明顯不同的高風險標的。" if LANG == "zh-TW" else "No distinct risk names beyond the current leaders.")


def render_manual_tracking(candidate_frame: pd.DataFrame) -> None:
    latest = _latest_candidates(candidate_frame)
    if latest.empty:
        return
    latest = enrich_with_company_metadata(latest)
    groups = [
        ("台股手動觀察" if LANG == "zh-TW" else "TW Manual Watch", _parse_runtime_tickers(getattr(runtime_settings, "tw_manual_watch_tickers", ""))),
        ("美股手動觀察" if LANG == "zh-TW" else "US Manual Watch", _parse_runtime_tickers(getattr(runtime_settings, "us_manual_watch_tickers", ""))),
        ("台股手動熱區" if LANG == "zh-TW" else "TW Manual Hot", _parse_runtime_tickers(getattr(runtime_settings, "tw_manual_hot_tickers", ""))),
        ("美股手動熱區" if LANG == "zh-TW" else "US Manual Hot", _parse_runtime_tickers(getattr(runtime_settings, "us_manual_hot_tickers", ""))),
    ]
    st.markdown(f'<div class="section-label">{"手動追蹤" if LANG == "zh-TW" else "Manual Tracking"}</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    for column, (title, tickers) in zip([left, right, left, right], groups):
        with column:
            st.markdown(f"**{title}**")
            if not tickers:
                st.caption("尚未設定。" if LANG == "zh-TW" else "No tickers configured.")
                continue
            subset = latest[latest["ticker"].isin(tickers)].copy()
            if subset.empty:
                st.caption("本次快照沒有這些標的的資料。" if LANG == "zh-TW" else "No rows for these tickers in the latest snapshot.")
                continue
            display = subset[["ticker", "company", "sector", "recommendation_bucket", "composite_signal_score"]].copy()
            display["recommendation_bucket"] = display["recommendation_bucket"].map(localize_value)
            display = display.rename(
                columns={
                    "ticker": "代號" if LANG == "zh-TW" else "Ticker",
                    "company": "公司" if LANG == "zh-TW" else "Company",
                    "sector": "類股" if LANG == "zh-TW" else "Sector",
                    "recommendation_bucket": "系統歸類" if LANG == "zh-TW" else "Bucket",
                    "composite_signal_score": "綜合分數" if LANG == "zh-TW" else "Score",
                }
            )
            st.dataframe(display, use_container_width=True, hide_index=True)


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
        "institutional_buy_streak": "法人連買天數" if LANG == "zh-TW" else "Institutional Buy Streak",
        "risk_level": t("risk_label"),
        "event_risk_note": t("event_risk"),
        "next_event_date": t("next_event"),
        "suggested_action": t("suggested_action"),
    }
    table = table.rename(columns=rename_map)
    chart_config: dict[str, Any] = {}
    if t("trend_mini") in table.columns:
        chart_config[t("trend_mini")] = st.column_config.LineChartColumn(
            t("trend_mini"),
            width="medium",
            y_min=-12,
            y_max=12,
        )
    if t("score_trend") in table.columns:
        chart_config[t("score_trend")] = st.column_config.LineChartColumn(
            t("score_trend"),
            width="medium",
            y_min=0,
            y_max=100,
        )
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config=chart_config or None,
    )


def render_focus_lists(candidate_frame: pd.DataFrame) -> None:
    st.markdown(f'<div class="section-label">{t("focus_lists")}</div>', unsafe_allow_html=True)
    if candidate_frame.empty:
        st.info(t("no_data"))
        return
    latest_date = candidate_frame["date"].max()
    _render_data_caption(f'{t("snapshot_as_of")}: {_format_snapshot_date(latest_date)}')
    latest = candidate_frame[candidate_frame["date"] == latest_date].copy()
    core_tab, explore_tab, risk_tab = st.tabs([t("core_tab"), t("explore_tab"), t("risk_tab")])
    with core_tab:
        render_terminal_table(
            latest[latest["universe_bucket"] == "core"]
            .sort_values(by=["composite_signal_score", "institutional_buy_streak"], ascending=[False, False])
            .head(12),
            ["ticker", "company", "sector", "trend_mini", "score_trend", "recommendation_bucket", "composite_signal_score", "institutional_buy_streak", "suggested_action"],
        )
    with explore_tab:
        render_terminal_table(
            latest[latest["universe_bucket"] == "explore"]
            .sort_values(by=["composite_signal_score"], ascending=[False])
            .head(12),
            ["ticker", "company", "sector", "trend_mini", "score_trend", "recommendation_bucket", "composite_signal_score", "risk_level", "suggested_action"],
        )
    with risk_tab:
        render_terminal_table(
            latest[latest["event_risk_note"] != "clear"]
            .sort_values(by=["composite_signal_score"], ascending=[True])
            .head(12),
            ["ticker", "company", "sector", "trend_mini", "score_trend", "recommendation_bucket", "event_risk_note", "next_event_date", "risk_level"],
        )


def render_decision_cards(candidate_frame: pd.DataFrame) -> None:
    st.markdown(f'<div class="section-label">{t("decision_cards")}</div>', unsafe_allow_html=True)
    st.caption(
        "綜合分數越高，代表越接近可執行。75 分以上通常進入可執行或候選，65-74 分代表差臨門一腳。"
        if LANG == "zh-TW"
        else f'{t("decision_score_label")}: {t("decision_score_help")}'
    )
    if candidate_frame.empty:
        st.info(t("no_data"))
        return
    latest_date = candidate_frame["date"].max()
    _render_data_caption(f'{t("snapshot_as_of")}: {_format_snapshot_date(latest_date)}')
    latest = (
        candidate_frame[candidate_frame["date"] == latest_date]
        .sort_values(by=["composite_signal_score", "institutional_buy_streak"], ascending=[False, False])
        .head(8)
    )
    for _, row in latest.iterrows():
        company_name, sector_name = _display_name_for_row(row)
        verdict_label, verdict_color = _decision_verdict(row)
        rationale = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in row.get("rationale", []))
        risks = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in row.get("risks", []))
        suggestion = maybe_translate_text(str(row.get("suggested_action", "")))
        level = maybe_translate_text(str(row.get("recommendation_level", "")))
        win_label = maybe_translate_text(str(row.get("win_rate_label", "")))
        risk_label = maybe_translate_text(str(row.get("risk_level", "")))
        reward_risk = maybe_translate_text(str(row.get("reward_risk_label", "")))
        forward_score = float(row.get("forward_score", 0))
        forward_notes = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in row.get("forward_notes", []))
        if LANG == "zh-TW":
            verdict_copy = {
                t("verdict_buy"): "條件完整，可直接依風控計畫執行。",
                t("verdict_probe"): "先用小部位試單，確認延續後再加碼。",
                t("verdict_wait"): "先觀察，等條件更完整再出手。",
                t("verdict_avoid"): "目前風險偏高，暫時不要出手。",
            }.get(verdict_label, "")
        else:
            verdict_copy = ""
        st.markdown(
            f"""
            <div class="decision-card">
                <div class="decision-head">
                    <div>
                        <div class="decision-ticker">{row["ticker"]}</div>
                        <div class="decision-meta">
                            {company_name} | {t("sector")} {sector_name} <br/>
                            {t("signal_type")} {localize_value(row.get("signal_type", ""))} |
                            {localize_value(row.get("universe_bucket", "core"))} |
                            {localize_value(row.get("recommendation_bucket", "Watchlist"))}
                        </div>
                    </div>
                    <div class="decision-meta">{t("decision_score_label")} {float(row.get("composite_signal_score", 0)):.2f}</div>
                </div>
                <div class="decision-meta" style="margin-bottom:8px;">
                    {t("decision_verdict")}：
                    <span style="color:{verdict_color};font-weight:800;">{verdict_label}</span>
                    {verdict_copy}
                </div>
                <span class="decision-pill">{level}</span>
                <span class="decision-pill">{t("win_label")}: {win_label}</span>
                <span class="decision-pill">{t("risk_label")}: {risk_label}</span>
                <span class="decision-pill">{t("reward_risk")}: {reward_risk}</span>
                <span class="decision-pill">{t("forward_score")}: {forward_score:.2f}</span>
                <span class="decision-pill">{t("event_risk")}: {localize_value(row.get("event_risk_note", "clear"))}</span>
                <div class="decision-label">{t("suggested_action")}</div>
                <div>{suggestion}</div>
                <div class="decision-label">{t("forward_notes")}</div>
                <ul class="decision-list">{forward_notes}</ul>
                <div class="decision-label">{t("rationale")}</div>
                <ul class="decision-list">{rationale}</ul>
                <div class="decision-label">{t("risks")}</div>
                <ul class="decision-list">{risks}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )



COPY["zh-TW"].update(
    {
        "decision_score_label": "綜合判讀分數",
        "decision_score_help": "80 分以上偏強，可正常看待；70-79 分可先小部位試單；60-69 分先觀察；60 分以下先避開。",
        "decision_verdict": "結論",
        "verdict_buy": "可買",
        "verdict_probe": "可試單",
        "verdict_wait": "先觀察",
        "verdict_avoid": "先避開",
        "leader_board_help": "這裡放的是目前最強、最接近可執行的標的。",
        "risk_board_help": "這裡放的是事件風險較高、容易影響勝率或不適合追價的標的。",
        "trend_mini": "短線走勢",
        "score_trend": "分數節奏",
        "rank_board": "熱度榜",
        "leader_board": "領先名單",
        "risk_board": "風險名單",
        "market_pulse": "市場脈搏",
        "sector_heatmap": "類股熱區",
        "setup_distribution": "訊號分布",
    }
)
TEXT = COPY["zh-TW"] | COPY.get(LANG, {})

ZH_DECISION_TEXT.update(
    {
        "Institutional buying has just turned positive.": "法人買盤剛轉正。",
        "Institutional buying is building into a second session.": "法人買盤延續到第 2 天。",
        "Relative strength is decisively above the market benchmark.": "相對強度明顯優於市場基準。",
        "Relative strength is supportive versus the benchmark.": "相對強度仍比市場基準健康。",
        "Price location is constructive and not excessively extended.": "價位位置健康，且未過度乖離。",
        "Entry quality is acceptable if execution stays disciplined.": "進場品質尚可，前提是執行紀律要嚴格。",
        "The market regime is supportive for trend-following entries.": "市場環境偏向有利順勢操作。",
        "The broader market is neutral, so follow-through may be slower.": "大盤偏中性，延續力可能較慢。",
        "The broader market is risk-off, so hit rates can fall quickly.": "大盤偏防守，勝率容易快速下降。",
        "This idea is in the Explore pool, so it should not outrank core large-cap names.": "這檔屬於觀察池，不應高於核心大型股的優先順序。",
        "This name belongs to the core monitoring pool.": "此標的屬於核心追蹤池。",
        "Event risk is manageable but still worth monitoring.": "事件風險可控，但仍值得持續追蹤。",
        "No major risk flags are active right now, but standard stop discipline still applies.": "目前沒有重大風險警示，但停損紀律仍要保留。",
        "The current signal does not yet have enough stacked evidence.": "目前訊號還沒有堆出足夠證據。",
        "Normal position sizing or staged entries on minor pullbacks.": "可用正常部位，或等待小拉回分批進場。",
        "Pilot size first, then add if confirmation holds.": "先用試單部位，確認延續後再加碼。",
        "Observe only until the odds improve.": "先觀察，等勝率提升再行動。",
        "Small trial size only; keep core capital focused on large caps.": "僅適合小部位試單，核心資金仍應聚焦大型股。",
        "High Conviction Core": "核心可買",
        "Actionable Setup": "可試單",
        "Watch and Wait": "先觀察",
        "High": "高",
        "Medium-High": "中高",
        "Medium-Low": "中低",
        "Medium": "中",
        "Favorable": "報酬優勢",
        "Balanced": "風報平衡",
        "Unclear": "風報不明",
    }
)


def _translate_macro_event_label(label: str) -> str:
    cleaned = str(label or "").strip().replace("_", " ").lower()
    if not cleaned:
        return ""
    if LANG != "zh-TW":
        return cleaned
    direct_map = {
        "cftc eur speculative net positions": "CFTC 歐元投機淨部位",
        "cftc eur speculative net position": "CFTC 歐元投機淨部位",
        "annual report": "年報",
        "ecb cipollone speech": "ECB Cipollone 談話",
        "ecb de guindos speech": "ECB De Guindos 談話",
        "ecb survey of monetary analysts": "ECB 貨幣分析師調查",
        "ecb survey of professional forecasters": "ECB 專業預測調查",
    }
    if cleaned in direct_map:
        return direct_map[cleaned]
    replacements = {
        "cftc": "CFTC",
        "eur": "歐元",
        "usd": "美元",
        "jpy": "日圓",
        "gbp": "英鎊",
        "speculative": "投機",
        "net": "淨",
        "position": "部位",
        "positions": "部位",
        "survey": "調查",
        "speech": "談話",
        "annual": "年度",
        "report": "報告",
        "earnings": "財報",
        "inflation": "通膨",
        "payrolls": "非農就業",
        "minutes": "會議紀要",
    }
    translated = cleaned
    for source, target in replacements.items():
        translated = translated.replace(source, target)
    return translated


def localize_value(value: object) -> str:
    text_value = str(value)
    mapping = {
        "Unknown": "??" if LANG == "zh-TW" else "Unknown",
        "Calm": "??" if LANG == "zh-TW" else "Calm",
        "Neutral": "??" if LANG == "zh-TW" else "Neutral",
        "Risk-Off": "Risk-Off / ??" if LANG == "zh-TW" else "Risk-Off",
        "Risk-On": "Risk-On / ??" if LANG == "zh-TW" else "Risk-On",
        "Risk-On Uptrend": "??????" if LANG == "zh-TW" else "Risk-On Uptrend",
        "Balanced / Selective": "?? / ?????" if LANG == "zh-TW" else "Balanced / Selective",
        "Defensive / Risk-Off": "?? / Risk-Off" if LANG == "zh-TW" else "Defensive / Risk-Off",
        "Greed": "??" if LANG == "zh-TW" else "Greed",
        "Constructive": "?????" if LANG == "zh-TW" else "Constructive",
        "Cautious": "??" if LANG == "zh-TW" else "Cautious",
        "Fear": "??" if LANG == "zh-TW" else "Fear",
        "Watchlist": "??" if LANG == "zh-TW" else "Watchlist",
        "Actionable": "?????" if LANG == "zh-TW" else "Actionable",
        "Candidate": "?????" if LANG == "zh-TW" else "Candidate",
        "Safer Follow-Through": "??????" if LANG == "zh-TW" else "Safer Follow-Through",
        "core": "???" if LANG == "zh-TW" else "Core",
        "explore": "???" if LANG == "zh-TW" else "Explore",
        "clear": "?????????" if LANG == "zh-TW" else "clear",
        "DAY_1_EARLY": "? 1 ? / ??" if LANG == "zh-TW" else "Day 1 Early",
        "DAY_2_BUILDING": "? 2 ? / ???" if LANG == "zh-TW" else "Day 2 Building",
        "DAY_3_PLUS_SAFER": "? 3 ??? / ????" if LANG == "zh-TW" else "Day 3+ Safer",
        "Institutional Accumulation": "??????" if LANG == "zh-TW" else "Institutional Accumulation",
        "Panic Reversal": "??????" if LANG == "zh-TW" else "Panic Reversal",
        "High": "?" if LANG == "zh-TW" else "High",
        "Medium": "?" if LANG == "zh-TW" else "Medium",
        "Medium-High": "??" if LANG == "zh-TW" else "Medium-High",
        "Medium-Low": "??" if LANG == "zh-TW" else "Medium-Low",
        "Favorable": "?????" if LANG == "zh-TW" else "Favorable",
        "Balanced": "?????" if LANG == "zh-TW" else "Balanced",
        "Unclear": "?????" if LANG == "zh-TW" else "Unclear",
        "High Conviction Core": "?????" if LANG == "zh-TW" else "High Conviction Core",
        "Actionable Setup": "?????" if LANG == "zh-TW" else "Actionable Setup",
        "Watch and Wait": "???" if LANG == "zh-TW" else "Watch and Wait",
    }
    if text_value in mapping:
        return mapping[text_value]
    if text_value.startswith("macro_event_imminent:") or text_value.startswith("macro_event_near:"):
        prefix, label = text_value.split(":", 1)
        prefix_label = "??????" if prefix == "macro_event_imminent" and LANG == "zh-TW" else "Macro imminent"
        if prefix == "macro_event_near":
            prefix_label = "??????" if LANG == "zh-TW" else "Macro near"
        return f"{prefix_label}: {_translate_macro_event_label(label)}"
    if LANG == "zh-TW" and text_value in ZH_DECISION_TEXT:
        return ZH_DECISION_TEXT[text_value]
    return text_value


def maybe_translate_text(text_value: str) -> str:
    if LANG != "zh-TW":
        return text_value
    if text_value.startswith("Institutional buying has persisted for ") and text_value.endswith(" sessions."):
        days = text_value.replace("Institutional buying has persisted for ", "").replace(" sessions.", "").strip()
        return f"????????? {days} ??"
    if text_value.startswith("Event risk is elevated:"):
        detail = text_value.replace("Event risk is elevated:", "").strip()
        return f"???????{_translate_macro_event_label(detail)}"
    if text_value.startswith("macro_event_imminent ("):
        inner = text_value.replace("macro_event_imminent (", "").rstrip(")")
        return f"???????{_translate_macro_event_label(inner)}"
    if text_value.startswith("macro_event_near ("):
        inner = text_value.replace("macro_event_near (", "").rstrip(")")
        return f"???????{_translate_macro_event_label(inner)}"
    if text_value.startswith("Volatility is elevated; position sizing should stay conservative."):
        return "?????????????"
    if text_value.startswith("Breadth is weak, so single-name breakouts may fail more often."):
        return "?????????????????????"
    if text_value.endswith(" names are carrying event-risk flags."):
        count = text_value.split(" ", 1)[0]
        return f"{count} ????????????"
    if text_value.startswith("No major market-wide warnings are flashing right now."):
        return "????????????????"
    if text_value.startswith("Theme support:"):
        return text_value.replace("Theme support:", "?????")
    if text_value.startswith("Institutional flow persistence supports the forward setup."):
        return "??????????????"
    if text_value.startswith("Relative strength confirms demand leadership."):
        return "????????????????"
    if text_value.startswith("Forward demand narrative is strong enough for a starter position."):
        return "????????????????????"
    if " | " in text_value and len(text_value.split(" | ")) == 3:
        dt, region, title = text_value.split(" | ", 2)
        region_map = {"US": "??", "EU": "??", "JP": "??", "CN": "??", "TW": "??"}
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
        .agg(
            avg_score=("score_value", "mean"),
            names=("ticker", "count"),
        )
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
        texttemplate="%{label}<br>%{value} ?<br>%{color:.0f}",
        hovertemplate="%{label}<br>" + ("??" if LANG == "zh-TW" else "Names") + ": %{value}<br>" + ("????" if LANG == "zh-TW" else "Avg Score") + ": %{color:.1f}<extra></extra>",
        root_color="white",
    )
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260, paper_bgcolor="white", coloraxis_showscale=False)
    return fig


def build_setup_distribution_chart(candidate_frame: pd.DataFrame) -> go.Figure:
    latest = _latest_candidates(candidate_frame)
    if latest.empty:
        fig = go.Figure()
        fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="white")
        return fig
    grouped = (
        latest.assign(
            market_label=latest["type"].map(lambda value: t("taiwan") if value == "tw" else t("us")),
            bucket_label=latest["recommendation_bucket"].map(localize_value),
        )
        .groupby(["market_label", "bucket_label"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )
    bucket_order = [t("safer"), t("actionable"), t("watchlist")]
    color_map = {
        t("safer"): "#2fbf71",
        t("actionable"): "#8bd36c",
        t("watchlist"): "#f6c84c",
    }
    fig = px.bar(
        grouped,
        x="market_label",
        y="count",
        color="bucket_label",
        category_orders={"bucket_label": bucket_order},
        color_discrete_map=color_map,
        text="count",
    )
    fig.update_traces(textposition="inside", hovertemplate="%{x}<br>%{fullData.name}: %{y}<extra></extra>")
    fig.update_layout(
        barmode="stack",
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend_title_text="",
        xaxis_title=None,
        yaxis_title=None,
    )
    return fig


@st.cache_data(ttl=21600, show_spinner=False)
def get_company_profile_cached(ticker: str) -> dict[str, str]:
    return market_data.get_company_profile(ticker)


@st.cache_data(ttl=1800, show_spinner=False)
def get_ticker_trend_cached(ticker: str, limit: int = 12) -> list[float]:
    history = repo.fetch_history(ticker, limit=limit)
    if not history:
        return []
    frame = pd.DataFrame(history)
    if "close_price" not in frame.columns:
        return []
    return frame["close_price"].fillna(0).astype(float).tolist()[-limit:]


@st.cache_data(ttl=1800, show_spinner=False)
def get_ticker_score_trend_cached(ticker: str, limit: int = 12) -> list[float]:
    history = repo.fetch_history(ticker, limit=limit)
    if not history:
        return []
    frame = pd.DataFrame(history)
    if "composite_signal_score" not in frame.columns:
        return []
    return frame["composite_signal_score"].fillna(0).astype(float).tolist()[-limit:]


def _display_name_for_row(row: pd.Series) -> tuple[str, str]:
    ticker = str(row.get("ticker", "")).upper()
    market_type = str(row.get("type", ""))
    profile = get_company_profile_cached(ticker)
    name_zh = str(profile.get("name_zh", "")).strip()
    name_en = str(profile.get("name_en", "")).strip()
    sector = str(profile.get("sector", "")).strip()

    if market_type == "tw":
        display_name = name_zh or name_en or ticker
        display_sector = sector or "??"
    else:
        if LANG == "zh-TW" and name_zh:
            display_name = f"{name_en}?{name_zh}?" if name_en else name_zh
        else:
            display_name = name_en or ticker
        display_sector = sector or ("??" if LANG == "zh-TW" else "Unknown")
    return display_name, display_sector


def _signal_tone(score: float) -> tuple[str, str]:
    if score >= 75:
        return ("#2fbf71", "????" if LANG == "zh-TW" else "Risk-on")
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


def _decision_verdict(row: pd.Series) -> tuple[str, str]:
    bucket = str(row.get("recommendation_bucket", "Watchlist"))
    score = float(row.get("composite_signal_score", 0) or 0)
    if bucket == "Safer Follow-Through" or score >= 80:
        return t("verdict_buy"), "#16a34a"
    if bucket == "Actionable" or score >= 70:
        return t("verdict_probe"), "#65a30d"
    if score >= 60:
        return t("verdict_wait"), "#d97706"
    return t("verdict_avoid"), "#dc2626"


def _normalize_trend(values: list[float]) -> list[float]:
    if not values:
        return []
    clean = [float(value) for value in values]
    base = clean[0] if clean[0] != 0 else 1.0
    return [round(((value / base) - 1.0) * 100, 2) for value in clean]


def _benchmark_config(range_key: str) -> tuple[str, str, int]:
    mapping = {
        "1d": ("1d", "5m", 78),
        "1mo": ("1mo", "1d", 22),
        "1y": ("1y", "1wk", 52),
        "3y": ("3y", "1wk", 156),
        "5y": ("5y", "1mo", 60),
    }
    return mapping.get(range_key, ("1d", "5m", 78))


def _benchmark_range_caption(range_key: str, trend_window: int) -> str:
    if LANG == "zh-TW":
        mapping = {
            "1d": "當日分時走勢",
            "1mo": f"近 {trend_window} 個交易日收盤趨勢",
            "1y": f"近 {trend_window} 週走勢",
            "3y": f"近 {trend_window} 週走勢",
            "5y": f"近 {trend_window} 個月走勢",
        }
    else:
        mapping = {
            "1d": "Intraday trend",
            "1mo": f"Last {trend_window} daily closes",
            "1y": f"Last {trend_window} weekly closes",
            "3y": f"Last {trend_window} weekly closes",
            "5y": f"Last {trend_window} monthly closes",
        }
    return mapping.get(range_key, mapping["1d"])


def _format_benchmark_datetime(value: pd.Timestamp | None) -> str:
    if value is None or pd.isna(value):
        return ""
    stamp = pd.Timestamp(value)
    return stamp.strftime("%Y-%m-%d %H:%M:%S")


def _format_snapshot_date(value: object) -> str:
    if value in (None, "", "nan"):
        return ""
    try:
        stamp = pd.to_datetime(value, errors="coerce")
    except Exception:
        return str(value)
    if pd.isna(stamp):
        return str(value)
    if isinstance(stamp, pd.Series):
        return str(value)
    return pd.Timestamp(stamp).strftime("%Y-%m-%d")


def _render_data_caption(*parts: str) -> None:
    items = [part.strip() for part in parts if part and str(part).strip()]
    if items:
        st.caption(" | ".join(items))


def _render_segmented_control(label: str, options: list[str], format_func, key: str) -> str:
    segmented = getattr(st, "segmented_control", None)
    if callable(segmented):
        return segmented(label, options=options, format_func=format_func, selection_mode="single", key=key)
    return st.radio(label, options=options, format_func=format_func, horizontal=True, label_visibility="collapsed", key=key)


@st.cache_data(ttl=900, show_spinner=False)
def get_benchmark_snapshot_cached(symbol: str, label_key: str, range_key: str) -> dict[str, Any]:
    period, interval, default_window = _benchmark_config(range_key)
    history = pd.DataFrame()
    if range_key == "1d":
        try:
            history = market_data._fetch_from_yahoo_chart(symbol, period=period, interval=interval)
        except Exception:
            history = pd.DataFrame()
    if history.empty:
        history = market_data.get_price_history(symbol, period=period, interval=interval)
    frame = history.copy()
    if "Date" in frame.columns:
        frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
        frame = frame.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    if frame.empty or "Close" not in frame.columns:
        return {
            "symbol": symbol,
            "label_key": label_key,
            "latest": None,
            "delta": None,
            "pct": None,
            "trend": [],
            "trend_window": 0,
            "range_key": range_key,
            "has_data": False,
            "start_at": None,
            "end_at": None,
        }
    frame["Close"] = frame["Close"].astype(float)
    latest = float(frame["Close"].iloc[-1])
    previous = float(frame["Close"].iloc[0]) if len(frame) > 1 else latest
    if range_key == "1d":
        previous_close = _get_previous_session_close(symbol, frame)
        if previous_close is not None:
            previous = previous_close
    delta = latest - previous
    pct = 0.0 if previous == 0 else (delta / previous) * 100
    trend_window = min(len(frame), default_window)
    trend = _normalize_trend(frame["Close"].tail(trend_window).tolist())
    return {
        "symbol": symbol,
        "label_key": label_key,
        "latest": latest,
        "delta": delta,
        "pct": pct,
        "trend": trend,
        "trend_window": trend_window,
        "range_key": range_key,
        "has_data": True,
        "start_at": _format_benchmark_datetime(frame["Date"].iloc[0] if "Date" in frame.columns and not frame.empty else None),
        "end_at": _format_benchmark_datetime(frame["Date"].iloc[-1] if "Date" in frame.columns and not frame.empty else None),
    }


@st.cache_data(ttl=900, show_spinner=False)
def _get_previous_session_close(symbol: str, intraday_frame: pd.DataFrame) -> float | None:
    try:
        daily_frame = market_data.get_price_history(symbol, period="5d", interval="1d")
    except Exception:
        return None
    if daily_frame.empty or "Close" not in daily_frame.columns:
        return None
    frame = daily_frame.copy()
    if "Date" in frame.columns:
        frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
        frame = frame.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    if frame.empty:
        return None
    frame["Close"] = frame["Close"].astype(float)
    intraday_date = None
    if "Date" in intraday_frame.columns and not intraday_frame.empty:
        intraday_date = pd.Timestamp(intraday_frame["Date"].iloc[-1]).normalize()
    if intraday_date is not None:
        frame["NormDate"] = frame["Date"].dt.normalize()
        older_rows = frame[frame["NormDate"] < intraday_date]
        if not older_rows.empty:
            return float(older_rows["Close"].iloc[-1])
        same_day_rows = frame[frame["NormDate"] == intraday_date]
        if not same_day_rows.empty and len(frame) >= 2:
            return float(frame["Close"].iloc[-2])
    if len(frame) >= 2:
        return float(frame["Close"].iloc[-2])
    return float(frame["Close"].iloc[-1]) if not frame.empty else None


def load_benchmark_snapshots(symbol_pairs: list[tuple[str, str]], range_key: str) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=min(3, len(symbol_pairs) or 1)) as executor:
        future_map = {
            executor.submit(get_benchmark_snapshot_cached, symbol, label_key, range_key): (symbol, label_key)
            for symbol, label_key in symbol_pairs
        }
        for future in as_completed(future_map):
            symbol, label_key = future_map[future]
            try:
                results[symbol] = future.result()
            except Exception:
                results[symbol] = {
                    "label_key": label_key,
                    "latest": None,
                    "delta": None,
                    "pct": None,
                    "trend": [],
                    "trend_window": 0,
                    "range_key": range_key,
                    "has_data": False,
                    "start_at": None,
                    "end_at": None,
                }
    return results


def build_benchmark_chart(series: list[float], positive: bool) -> go.Figure:
    color = "#16a34a" if positive else "#ef4444"
    fill = "rgba(34,197,94,0.12)" if positive else "rgba(239,68,68,0.12)"
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            y=series,
            mode="lines",
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor=fill,
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=72,
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


def enrich_with_company_metadata(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    enriched = frame.copy()
    names: list[str] = []
    sectors: list[str] = []
    for _, row in enriched.iterrows():
        company_name, sector = _display_name_for_row(row)
        names.append(company_name)
        sectors.append(sector)
    enriched["company"] = names
    enriched["sector"] = sectors
    return enriched


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container { max-width: 1450px; padding-top: 2.15rem; padding-bottom: 1.8rem; }
        section[data-testid="stSidebar"] { min-width: 340px !important; max-width: 340px !important; }
        .page-title { font-size: 1.9rem; font-weight: 800; line-height: 1.2; margin: 0 0 1rem 0; color: #243047; }
        .section-label { font-size: 0.78rem; font-weight: 700; color: #616c7c; margin: 0.85rem 0 0.45rem; text-transform: uppercase; }
        .hero-shell { border-bottom:1px solid rgba(118,128,145,.16); padding-bottom:16px; margin-bottom:10px; }
        .hero-title { font-size:2.15rem; font-weight:900; color:#101828; letter-spacing:0; margin:0; }
        .hero-sub { font-size:0.92rem; color:#667085; margin-top:4px; }
        .hero-time { text-align:right; font-size:0.88rem; color:#98a2b3; font-weight:700; margin-top:8px; }
        .benchmark-card { border:1px solid rgba(118,128,145,.14); border-radius:10px; background:#fff; padding:10px 12px; min-height:128px; }
        .benchmark-name { font-size:0.98rem; font-weight:800; color:#243047; margin-bottom:2px; }
        .benchmark-price { font-size:1.75rem; font-weight:900; line-height:1.05; margin:2px 0 4px; }
        .benchmark-change { font-size:0.9rem; font-weight:700; }
        .hero-side { border:1px solid rgba(118,128,145,.16); border-radius:10px; background:#f8fafc; padding:12px 14px; min-height:128px; }
        .hero-side-title { font-size:0.8rem; font-weight:800; color:#475467; text-transform:uppercase; margin-bottom:8px; }
        .hero-side-main { font-size:1.2rem; font-weight:900; color:#101828; margin-bottom:6px; }
        .hero-side-copy { font-size:0.86rem; color:#667085; line-height:1.45; }
        .terminal-card, .summary-band, .decision-card { border: 1px solid rgba(118,128,145,.22); border-radius: 8px; background: #ffffff; }
        .terminal-card { padding: 14px; min-height: 174px; }
        .summary-band { padding: 12px 14px; min-height: 112px; background: #f7f9fc; }
        .summary-title { font-size: 0.75rem; font-weight: 700; color: #697483; margin-bottom: 5px; text-transform: uppercase; }
        .summary-main { font-size: 1.08rem; font-weight: 800; margin-bottom: 8px; }
        .summary-sub { font-size: 0.82rem; color: #596474; line-height: 1.45; }
        .state-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin-bottom:12px; }
        .state-metric { border:1px solid rgba(118,128,145,.16); border-radius:8px; padding:10px 12px; background:#f7f9fc; min-height:72px; }
        .state-label { font-size:0.73rem; color:#6b7685; text-transform:uppercase; margin-bottom:4px; font-weight:700; }
        .state-value { font-size:0.98rem; font-weight:800; line-height:1.2; }
        .state-read { border:1px solid rgba(118,128,145,.16); border-radius:8px; padding:12px 14px; background:#f7f9fc; min-height:118px; }
        .state-read-title { font-size:0.73rem; color:#6b7685; text-transform:uppercase; margin-bottom:6px; font-weight:700; }
        .state-read-main { font-size:1rem; font-weight:800; margin-bottom:6px; color:#243047; }
        .state-read-copy { font-size:0.86rem; color:#596474; line-height:1.5; }
        .light-strip { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin: 8px 0 14px; }
        .light-card { border:1px solid rgba(118,128,145,.16); border-radius:8px; padding:10px 12px; background:#f7f9fc; min-height:78px; }
        .light-top { display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:7px; }
        .light-name { font-size:0.72rem; text-transform:uppercase; color:#6b7685; font-weight:700; }
        .light-dot { width:10px; height:10px; border-radius:50%; display:inline-block; }
        .light-value { font-size:1rem; font-weight:800; color:#243047; margin-bottom:4px; }
        .light-copy { font-size:0.82rem; color:#596474; line-height:1.35; }
        .mini-list { margin: 0; padding-left: 18px; color: #1f2937; font-size: 0.88rem; }
        .brief-card { border:1px solid rgba(118,128,145,.18); border-radius:8px; background:#f7f9fc; padding:12px 14px; min-height:132px; }
        .brief-head { display:flex; justify-content:space-between; gap:10px; align-items:flex-start; margin-bottom:8px; }
        .brief-title { font-size:0.78rem; font-weight:800; color:#243047; }
        .brief-bias { font-size:0.76rem; font-weight:700; color:#647080; text-transform:uppercase; }
        .brief-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; margin-bottom:8px; }
        .brief-kpi { background:#fff; border:1px solid rgba(118,128,145,.14); border-radius:8px; padding:8px 10px; }
        .brief-kpi-label { font-size:0.7rem; color:#6b7685; text-transform:uppercase; margin-bottom:3px; font-weight:700; }
        .brief-kpi-value { font-size:0.95rem; font-weight:800; color:#243047; }
        .brief-copy { font-size:0.84rem; color:#596474; line-height:1.45; }
        .rank-card { border:1px solid rgba(118,128,145,.18); border-radius:8px; background:#fff; padding:12px 14px; min-height:240px; }
        .rank-item { display:flex; justify-content:space-between; gap:10px; align-items:flex-start; padding:8px 0; border-bottom:1px solid rgba(118,128,145,.1); }
        .rank-item:last-child { border-bottom:none; }
        .rank-left { min-width:0; }
        .rank-name { font-size:0.86rem; font-weight:800; color:#243047; margin-bottom:2px; }
        .rank-meta { font-size:0.78rem; color:#647080; line-height:1.35; }
        .rank-score { font-size:0.9rem; font-weight:800; color:#243047; white-space:nowrap; }
        .decision-card { padding: 14px; margin-bottom: 10px; }
        .decision-head { display:flex; justify-content:space-between; gap:10px; align-items:flex-start; margin-bottom:10px; }
        .decision-ticker { font-size: 0.98rem; font-weight: 800; }
        .decision-meta { font-size: 0.8rem; color: #5f6977; }
        .decision-pill { display:inline-block; border: 1px solid rgba(95,105,119,.18); border-radius:999px; padding: 2px 8px; font-size:0.74rem; margin-right:6px; margin-bottom:6px; }
        .decision-label { font-size: 0.75rem; font-weight: 700; color: #647080; margin: 8px 0 4px; text-transform: uppercase; }
        .decision-list { margin: 0; padding-left: 18px; color: #1f2937; font-size: 0.88rem; }
        div[data-testid="stMetric"] { background:#f7f9fc; border:1px solid rgba(118,128,145,.18); border-radius:8px; padding:10px 12px; }
        div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
        @media (max-width: 1200px) {
            section[data-testid="stSidebar"] { min-width: 290px !important; max-width: 290px !important; }
            .page-title { font-size: 1.55rem; }
            .block-container { padding-top: 2.4rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_analysis_summary(summary: AnalysisRunSummary) -> str:
    if LANG == "zh-TW":
        return (
            f"掃描 {summary.scanned_tickers} 檔 | "
            f"有資料 {summary.data_ready_tickers} 檔 | "
            f"資料不足 {summary.skipped_data_tickers} 檔 | "
            f"未入選 {summary.no_signal_tickers} 檔 | "
            f"寫入 {summary.signal_count} 筆"
        )
    return (
        f"Scanned {summary.scanned_tickers} | "
        f"Data-ready {summary.data_ready_tickers} | "
        f"Missing {summary.skipped_data_tickers} | "
        f"No-signal {summary.no_signal_tickers} | "
        f"Written {summary.signal_count}"
    )


def format_skip_reasons(reason_counts: dict[str, int]) -> str:
    if not reason_counts:
        return ""
    labels = {
        "no_market_data": "查無市場資料" if LANG == "zh-TW" else "no market data",
        "incomplete_history": "歷史資料不足" if LANG == "zh-TW" else "incomplete history",
        "request_timeout": "來源逾時" if LANG == "zh-TW" else "request timeout",
        "provider_error": "來源異常" if LANG == "zh-TW" else "provider error",
    }
    ordered = sorted(reason_counts.items(), key=lambda item: item[1], reverse=True)
    return " | ".join(f"{labels.get(key, key)} {count}" for key, count in ordered)


def format_no_signal_reasons(reason_counts: dict[str, int]) -> str:
    if not reason_counts:
        return ""
    labels = {
        "core_below_60ma": "核心池跌破 60MA" if LANG == "zh-TW" else "core below 60MA",
        "core_60ma_not_rising": "核心池 60MA 未上彎" if LANG == "zh-TW" else "core 60MA not rising",
        "explore_below_60ma": "觀察池跌破 60MA" if LANG == "zh-TW" else "explore below 60MA",
        "explore_growth_missing": "觀察池營收 / EPS 未過底線" if LANG == "zh-TW" else "explore growth baseline failed",
        "no_institutional_buy_streak": "近 3 日法人淨買超未轉正" if LANG == "zh-TW" else "3-day institutional flow not positive",
        "below_20ma": "收盤仍在 20MA 下方" if LANG == "zh-TW" else "price still below 20MA",
        "volume_below_5d_avg": "量能未高於 5 日均量" if LANG == "zh-TW" else "volume below the 5-day average",
        "explore_waiting_for_trigger": "觀察池已過底線，但尚未觸發型態" if LANG == "zh-TW" else "explore passed baseline but has no trigger",
        "no_strategy_trigger": "未觸發任一進場型態" if LANG == "zh-TW" else "no trigger",
        "market_risk_off": "大盤 Risk-Off，轉入防守觀察" if LANG == "zh-TW" else "market risk-off",
        "wait_pullback_to_20ma": "分數夠高，但乖離過大，等回測 20MA" if LANG == "zh-TW" else "wait for pullback to 20MA",
        "wait_for_institutional_confirmation": "VCP 已到位，但法人尚未明確跟進" if LANG == "zh-TW" else "wait for institutional confirmation",
        "score_borderline_65_74": "已觸發型態，但綜合分數落在 65-74" if LANG == "zh-TW" else "score between 65 and 74",
        "triggered_but_low_score": "已觸發型態，但健康分數仍偏弱" if LANG == "zh-TW" else "triggered but score too low",
    }
    ordered = sorted(reason_counts.items(), key=lambda item: item[1], reverse=True)
    return " | ".join(f"{labels.get(key, key)} {count}" for key, count in ordered)


def _stage_name_label(stage: str) -> str:
    mapping = {
        "baseline_reject": "第一階段淘汰" if LANG == "zh-TW" else "Baseline Reject",
        "watch": "觀察" if LANG == "zh-TW" else "Watch",
        "candidate": "差臨門一腳" if LANG == "zh-TW" else "Candidate",
        "actionable": "今日可執行" if LANG == "zh-TW" else "Actionable",
    }
    return mapping.get(stage, stage)


def _stage_reason_label(reason: str) -> str:
    mapping = {
        "core_below_60ma": "核心池跌破 60MA" if LANG == "zh-TW" else "core below 60MA",
        "core_60ma_not_rising": "核心池 60MA 未上彎" if LANG == "zh-TW" else "core 60MA not rising",
        "explore_below_60ma": "觀察池跌破 60MA" if LANG == "zh-TW" else "explore below 60MA",
        "explore_growth_missing": "觀察池營收 / EPS 未過底線" if LANG == "zh-TW" else "explore growth baseline failed",
        "panic_exception_baseline_ok": "恐慌極端反轉例外" if LANG == "zh-TW" else "panic reversal exception",
        "core_trend_template_ok": "核心池底線通過" if LANG == "zh-TW" else "core baseline passed",
        "explore_baseline_ok": "觀察池底線通過" if LANG == "zh-TW" else "explore baseline passed",
        "no_institutional_buy_streak": "近 3 日法人淨買超未轉正" if LANG == "zh-TW" else "3-day institutional flow not positive",
        "below_20ma": "收盤仍在 20MA 下方" if LANG == "zh-TW" else "below 20MA",
        "volume_below_5d_avg": "量能未高於 5 日均量" if LANG == "zh-TW" else "volume below the 5-day average",
        "explore_waiting_for_trigger": "觀察池已過底線，但未出現進場型態" if LANG == "zh-TW" else "explore waiting for trigger",
        "no_strategy_trigger": "未觸發任一進場型態" if LANG == "zh-TW" else "no trigger",
        "market_risk_off": "大盤偏 Risk-Off，先以防守為主" if LANG == "zh-TW" else "market risk-off",
        "ready_now": "條件完整，可直接執行" if LANG == "zh-TW" else "ready now",
        "wait_pullback_to_20ma": "乖離過大，等量縮回測 20MA" if LANG == "zh-TW" else "wait pullback to 20MA",
        "wait_for_institutional_confirmation": "VCP 已到位，等待法人跟單" if LANG == "zh-TW" else "wait for institutional confirmation",
        "score_borderline_65_74": "分數落在 65-74，差臨門一腳" if LANG == "zh-TW" else "score borderline 65-74",
        "triggered_but_low_score": "型態出現，但整體健康度仍不足" if LANG == "zh-TW" else "triggered but low score",
    }
    return mapping.get(reason, reason)


def _trigger_label_list(values: list[str]) -> str:
    mapping = {
        "SMART_MONEY_TREND": "法人順勢動能" if LANG == "zh-TW" else "Smart Money Trend",
        "VCP_BREAKOUT": "VCP 量縮突破" if LANG == "zh-TW" else "VCP Breakout",
        "PANIC_REVERSAL": "恐慌極端反轉" if LANG == "zh-TW" else "Panic Reversal",
    }
    if not values:
        return "—"
    return " / ".join(mapping.get(value, value) for value in values)


def _format_stage_counts(stage_counts: dict[str, int]) -> str:
    if not stage_counts:
        return ""
    parts: list[str] = []
    for key in ["baseline_reject", "watch", "candidate", "actionable"]:
        if key in stage_counts:
            parts.append(f"{_stage_name_label(key)} {stage_counts[key]}")
    return " | ".join(parts)


def render_funnel_stage_table(summary: AnalysisRunSummary) -> None:
    stage_rows = getattr(summary, "stage_rows", None) or []
    if not stage_rows:
        return
    frame = pd.DataFrame(stage_rows)
    if frame.empty:
        return
    frame = enrich_with_company_metadata(frame)
    frame["stage_label"] = frame["stage"].map(_stage_name_label)
    frame["reason_label"] = frame["reason"].map(_stage_reason_label)
    frame["triggers_label"] = frame["triggers"].apply(lambda values: _trigger_label_list(list(values) if isinstance(values, list) else []))
    frame["fundamental_snapshot"] = frame.apply(
        lambda row: (
            f"營收 YoY {float(row['revenue_yoy']):.1f}% / EPS {float(row['eps_ttm']):.2f}"
            if LANG == "zh-TW" and pd.notna(row.get("revenue_yoy")) and pd.notna(row.get("eps_ttm"))
            else (
                f"Revenue YoY {float(row['revenue_yoy']):.1f}% / EPS {float(row['eps_ttm']):.2f}"
                if pd.notna(row.get("revenue_yoy")) and pd.notna(row.get("eps_ttm"))
                else "—"
            )
        ),
        axis=1,
    )
    display = frame[
        [
            "ticker",
            "company",
            "sector",
            "universe_bucket",
            "stage_label",
            "triggers_label",
            "composite_signal_score",
            "relative_strength_score",
            "institutional_buy_streak",
            "fundamental_snapshot",
            "reason_label",
        ]
    ].rename(
        columns={
            "ticker": "代號" if LANG == "zh-TW" else "Ticker",
            "company": "公司" if LANG == "zh-TW" else "Company",
            "sector": "類股" if LANG == "zh-TW" else "Sector",
            "universe_bucket": "池別" if LANG == "zh-TW" else "Pool",
            "stage_label": "漏斗階段" if LANG == "zh-TW" else "Stage",
            "triggers_label": "觸發型態" if LANG == "zh-TW" else "Trigger",
            "composite_signal_score": "綜合分數" if LANG == "zh-TW" else "Score",
            "relative_strength_score": "相對強度" if LANG == "zh-TW" else "RS",
            "institutional_buy_streak": "法人連買天數" if LANG == "zh-TW" else "Buy Streak",
            "fundamental_snapshot": "基本面快照" if LANG == "zh-TW" else "Fundamental Snapshot",
            "reason_label": "未入選 / 歸類原因" if LANG == "zh-TW" else "Reason",
        }
    )
    display = display.fillna("")
    for column in display.columns:
        display[column] = display[column].map(lambda value: "" if value is None else str(value))
    st.markdown(f'<div class="section-label">{"漏斗過程" if LANG == "zh-TW" else "Funnel Trail"}</div>', unsafe_allow_html=True)
    st.dataframe(display, use_container_width=True, hide_index=True)


def _analysis_cooldown_key(market_type: str) -> str:
    return f"analysis_last_run_{market_type}"


def should_skip_recent_analysis(market_type: str, force_refresh: bool, cooldown_minutes: int = 20) -> bool:
    if force_refresh:
        return False
    last_run = st.session_state.get(_analysis_cooldown_key(market_type))
    if not isinstance(last_run, datetime):
        return False
    return datetime.now() - last_run < timedelta(minutes=cooldown_minutes)


def run_market_analysis(
    market_type: str,
    progress_bar: Any | None = None,
    status_box: Any | None = None,
    force_refresh: bool = False,
) -> AnalysisRunSummary | None:
    if should_skip_recent_analysis(market_type, force_refresh=force_refresh):
        _set_analysis_feedback("info", t("cooldown_skip"))
        return None
    universe = UniverseBuilder(runtime_settings).build(market_type)
    engine = AnalysisEngine(
        event_risk_service=EventRiskService(high_risk_event_dates=runtime_settings.high_risk_event_dates)
    )

    def on_progress(stage: str, current: int, total: int, detail: str) -> None:
        if progress_bar is not None:
            if stage == "done":
                progress_bar.progress(100)
            else:
                pct = 5 if total <= 0 else min(95, max(5, int((current / max(total, 1)) * 100)))
                progress_bar.progress(pct)
        if status_box is not None:
            status_box.info(f"{t('analysis_progress')} | {detail}")

    summary = engine.run_with_summary(universe.to_analysis_universe(), progress_callback=on_progress)
    if progress_bar is not None:
        progress_bar.progress(100)
    st.session_state[_analysis_cooldown_key(market_type)] = datetime.now()
    return summary


def _set_analysis_feedback(kind: str, message: str) -> None:
    st.session_state["analysis_feedback"] = {"kind": kind, "message": message}


def render_analysis_feedback() -> None:
    feedback = st.session_state.pop("analysis_feedback", None)
    if not feedback:
        return
    kind = feedback.get("kind", "info")
    message = str(feedback.get("message", ""))
    if kind == "success":
        st.success(message)
    elif kind == "warning":
        st.warning(message)
    elif kind == "error":
        st.error(message)
    else:
        st.info(message)


def render_analysis_summary(summary: AnalysisRunSummary) -> None:
    st.markdown(f'<div class="section-label">{t("analysis_summary")}</div>', unsafe_allow_html=True)
    scanned_tickers = int(getattr(summary, "scanned_tickers", 0) or 0)
    data_ready_tickers = int(getattr(summary, "data_ready_tickers", 0) or 0)
    skipped_data_tickers = int(getattr(summary, "skipped_data_tickers", 0) or 0)
    no_signal_tickers = int(getattr(summary, "no_signal_tickers", 0) or 0)
    signal_count = int(getattr(summary, "signal_count", 0) or 0)
    skipped_reason_counts = getattr(summary, "skipped_reason_counts", {}) or {}
    no_signal_reason_counts = getattr(summary, "no_signal_reason_counts", {}) or {}
    core_ticker_count = int(getattr(summary, "core_ticker_count", 0) or 0)
    explore_ticker_count = int(getattr(summary, "explore_ticker_count", 0) or 0)
    stage_counts = getattr(summary, "stage_counts", {}) or {}

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("掃描" if LANG == "zh-TW" else "Scanned", scanned_tickers)
    c2.metric("有資料" if LANG == "zh-TW" else "Data Ready", data_ready_tickers)
    c3.metric("資料不足" if LANG == "zh-TW" else "Missing", skipped_data_tickers)
    c4.metric("未入選" if LANG == "zh-TW" else "No Signal", no_signal_tickers)
    c5.metric(t("records"), signal_count)
    summary_at = str(st.session_state.get("analysis_summary_at") or "")
    if summary_at:
        _render_data_caption(f'{t("page_rendered_at")}: {summary_at}')
    if core_ticker_count or explore_ticker_count:
        if LANG == "zh-TW":
            st.caption(f"核心池 {core_ticker_count} 檔、觀察池 {explore_ticker_count} 檔。這些是掃描宇宙，不是保證最後會入選。")
        else:
            st.caption(
                f"Scanned {core_ticker_count} core names and {explore_ticker_count} explore names. "
                f"These lists define the universe, not guaranteed outputs."
            )
    if stage_counts:
        st.caption(("漏斗分佈：" if LANG == "zh-TW" else "Funnel counts: ") + _format_stage_counts(stage_counts))
    if skipped_reason_counts:
        st.caption(("資料不足原因：" if LANG == "zh-TW" else "Missing-data reasons: ") + format_skip_reasons(skipped_reason_counts))
    if no_signal_reason_counts:
        st.caption(("未入選主因：" if LANG == "zh-TW" else "Main no-signal reasons: ") + format_no_signal_reasons(no_signal_reason_counts))
    if signal_count == 0:
        if data_ready_tickers == 0:
            st.warning("流程有跑完，但沒有拿到足夠可用資料。" if LANG == "zh-TW" else "Execution completed, but no usable market data was available.")
        else:
            st.info(
                "流程有跑完，但目前沒有股票同時通過底線、型態、分數與風險檢查。"
                if LANG == "zh-TW"
                else "Execution completed, but no names passed the baseline, trigger, score, and risk filters together."
            )
    else:
        pass_rate = (signal_count / scanned_tickers * 100) if scanned_tickers else 0.0
        st.info(
            (
                f"最後只有 {signal_count} 檔進入結果，不代表偏好池失效，而是只有 {pass_rate:.1f}% 同時通過底線、觸發、分數與風險門檻。"
                if LANG == "zh-TW"
                else f"Only {signal_count} names survived. That means {pass_rate:.1f}% cleared baseline, trigger, score, and risk checks."
            )
        )
    render_funnel_stage_table(summary)


def load_candidate_frame(limit: int = 220) -> pd.DataFrame:
    frame = pd.DataFrame(repo.fetch_recent_candidates(limit=limit))
    if frame.empty:
        return frame
    frame = pd.DataFrame(decision_support.enrich_rows(frame.to_dict("records")))
    defaults = {
        "recommendation_bucket": "Watchlist",
        "universe_bucket": "core",
        "market_regime": "Unknown",
        "event_risk_note": "clear",
        "institutional_buy_streak": 0,
        "composite_signal_score": 0.0,
        "relative_strength_score": 0.0,
        "entry_quality_score": 0.0,
    }
    for column, default in defaults.items():
        if column not in frame.columns:
            frame[column] = default
        else:
            frame[column] = frame[column].fillna(default)
    return frame


def render_run_controls() -> None:
    st.markdown(f'<div class="section-label">{t("run_analysis")}</div>', unsafe_allow_html=True)
    st.caption(t("cooldown_force_hint"))
    force_refresh = st.checkbox(t("force_refresh"), value=False, key="force_refresh_history")
    left, right = st.columns(2)
    if left.button(t("run_tw"), use_container_width=True):
        try:
            progress_bar = st.progress(0)
            status_box = st.empty()
            summary = run_market_analysis("tw", progress_bar=progress_bar, status_box=status_box, force_refresh=force_refresh)
            status_box.empty()
            progress_bar.empty()
            if summary is None:
                st.rerun()
            if summary.signal_count > 0:
                _set_analysis_feedback("success", f'{t("analysis_done")} | {format_analysis_summary(summary)}')
            else:
                _set_analysis_feedback("warning", f'{t("analysis_done")} | {format_analysis_summary(summary)}')
            st.session_state["analysis_summary"] = summary
            st.session_state["analysis_summary_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.rerun()
        except Exception as exc:
            _set_analysis_feedback("error", f'{t("analysis_failed")}: {exc}')
            st.rerun()
    if right.button(t("run_us"), use_container_width=True):
        try:
            progress_bar = st.progress(0)
            status_box = st.empty()
            summary = run_market_analysis("us", progress_bar=progress_bar, status_box=status_box, force_refresh=force_refresh)
            status_box.empty()
            progress_bar.empty()
            if summary is None:
                st.rerun()
            if summary.signal_count > 0:
                _set_analysis_feedback("success", f'{t("analysis_done")} | {format_analysis_summary(summary)}')
            else:
                _set_analysis_feedback("warning", f'{t("analysis_done")} | {format_analysis_summary(summary)}')
            st.session_state["analysis_summary"] = summary
            st.session_state["analysis_summary_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.rerun()
        except Exception as exc:
            _set_analysis_feedback("error", f'{t("analysis_failed")}: {exc}')
            st.rerun()


def render_runtime_settings_panel() -> None:
    with st.sidebar.expander(t("settings_panel")):
        with st.form("runtime_settings_form"):
            app_language = st.selectbox(
                t("language"),
                options=["zh-TW", "en"],
                index=0 if runtime_settings.app_language == "zh-TW" else 1,
            )
            tw_core_tickers = st.text_area("TW Core", value=str(runtime_settings.tw_core_tickers), height=90)
            us_core_tickers = st.text_area("US Core", value=str(runtime_settings.us_core_tickers), height=80)
            tw_explore_tickers = st.text_area("TW Explore", value=str(runtime_settings.tw_explore_tickers), height=70)
            us_explore_tickers = st.text_area("US Explore", value=str(runtime_settings.us_explore_tickers), height=70)
            tw_explore_limit = st.number_input(
                "TW Explore Limit", min_value=1, max_value=30, value=int(runtime_settings.tw_explore_limit), step=1
            )
            us_explore_limit = st.number_input(
                "US Explore Limit", min_value=1, max_value=30, value=int(runtime_settings.us_explore_limit), step=1
            )
            st.caption("FMP economic calendar is used first. This field is only for manual fallback or custom override dates.")
            high_risk_event_dates = st.text_input(t("high_risk_dates"), value=str(runtime_settings.high_risk_event_dates))
            submitted = st.form_submit_button(t("save_settings"), use_container_width=True)
        if submitted:
            user_settings_service.update_runtime_preferences(
                chat_id,
                {
                    "app_language": app_language,
                    "tw_core_tickers": tw_core_tickers,
                    "us_core_tickers": us_core_tickers,
                    "tw_explore_tickers": tw_explore_tickers,
                    "us_explore_tickers": us_explore_tickers,
                    "tw_explore_limit": int(tw_explore_limit),
                    "us_explore_limit": int(us_explore_limit),
                    "high_risk_event_dates": high_risk_event_dates,
                },
            )
            st.success(t("settings_saved"))
            st.rerun()


def render_market_state() -> None:
    overview = overview_service.build()
    vix_value = market_data.get_vix_value()
    render_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tw_summary = summary_service.build_market_summary("tw")
    us_summary = summary_service.build_market_summary("us")
    vix_zone, vix_copy = describe_vix(vix_value)
    fear_greed_label, fear_greed_copy, _ = describe_fear_greed(overview.fear_greed_score)
    fear_greed_source = getattr(overview, "fear_greed_source", "CNN Fear & Greed Index")
    fear_greed_updated_at = getattr(overview, "fear_greed_updated_at", "")

    def _format_detail_time(value: str) -> str:
        if not value:
            return "—"
        try:
            parsed = pd.to_datetime(value)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return value

    st.markdown(f'<div class="section-label">{t("market_state")}</div>', unsafe_allow_html=True)
    freshness_bits = [f'{t("page_rendered_at")}: {render_time}', t("intraday_source_note")]
    for summary in (tw_summary, us_summary):
        if summary is not None:
            freshness_bits.append(f'{summary.market_type.upper()}: {_format_snapshot_date(summary.summary_date)}')
    _render_data_caption(*freshness_bits)

    left_card, right_card = st.columns(2)
    with left_card:
        with st.container(border=True):
            st.markdown(f"**{t('fear_greed')}**")
            _render_data_caption(
                f"{'來源' if LANG == 'zh-TW' else 'Source'}: {fear_greed_source}",
                f"{'更新時間' if LANG == 'zh-TW' else 'Updated'}: {_format_detail_time(fear_greed_updated_at)}",
            )
            st.plotly_chart(build_fear_greed_gauge(overview.fear_greed_score), use_container_width=True, config={"displayModeBar": False}, key="market_state_fear_greed_gauge")
            st.markdown(
                f"""
                <div class="state-read">
                    <div class="state-read-title">{'情緒解讀' if LANG == 'zh-TW' else 'Sentiment Read'}</div>
                    <div class="state-read-main">{fear_greed_label} / {localize_value(overview.sentiment_label)}</div>
                    <div class="state-read-copy">{fear_greed_copy}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with right_card:
        with st.container(border=True):
            st.markdown("**VIX**")
            _render_data_caption(
                "來源: CBOE / Yahoo Finance" if LANG == "zh-TW" else "Source: CBOE / Yahoo Finance",
                f"{'抓取時間' if LANG == 'zh-TW' else 'Fetched'}: {render_time}",
            )
            st.plotly_chart(build_vix_gauge(vix_value), use_container_width=True, config={"displayModeBar": False}, key="market_state_vix_gauge")
            st.markdown(
                f"""
                <div class="state-read">
                    <div class="state-read-title">{'VIX 解讀' if LANG == 'zh-TW' else 'VIX Read'}</div>
                    <div class="state-read-main">{vix_zone}</div>
                    <div class="state-read-copy">{vix_copy}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        f"""
        <div class="terminal-card">
            <div class="state-grid">
                <div class="state-metric">
                    <div class="state-label">{t("overall_trend")}</div>
                    <div class="state-value">{localize_value(overview.overall_trend)}</div>
                </div>
                <div class="state-metric">
                    <div class="state-label">{t("sentiment")}</div>
                    <div class="state-value">{localize_value(overview.sentiment_label)}</div>
                </div>
                <div class="state-metric">
                    <div class="state-label">{t("fear_greed")}</div>
                    <div class="state-value">{overview.fear_greed_score:.0f}/100</div>
                </div>
                <div class="state-metric">
                    <div class="state-label">{t("breadth")}</div>
                    <div class="state-value">{overview.breadth_snapshot:.2f}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    details_left, details_right = st.columns((1.2, 1))
    with details_left:
        st.markdown(f'<div class="section-label">{t("momentum_zones")}</div>', unsafe_allow_html=True)
        if overview.momentum_zones:
            st.markdown("\n".join(f'- {maybe_translate_text(item)}' for item in overview.momentum_zones))
        else:
            st.info(t("no_data"))
        st.markdown(f'<div class="section-label">{t("macro_calendar")}</div>', unsafe_allow_html=True)
        if overview.upcoming_macro_events:
            st.markdown("\n".join(f'- {maybe_translate_text(item)}' for item in overview.upcoming_macro_events[:6]))
        else:
            st.info(t("no_data"))
    with details_right:
        st.markdown(f'<div class="section-label">{t("cautions")}</div>', unsafe_allow_html=True)
        if overview.caution_items:
            st.markdown("\n".join(f'- {maybe_translate_text(item)}' for item in overview.caution_items))
        else:
            st.info("目前沒有明顯的市場級風險提醒。" if LANG == "zh-TW" else "No major market-wide warnings are active right now.")


def render_summary_band(label: str, summary: Any) -> None:
    if summary is None:
        st.info(t("no_data"))
        return
    _render_data_caption(f'{t("snapshot_as_of")}: {_format_snapshot_date(getattr(summary, "summary_date", ""))}')
    st.markdown(
        f"""
        <div class="summary-band">
            <div class="summary-title">{label}</div>
            <div class="summary-main">{localize_value(summary.regime)}</div>
            <div class="summary-sub">
                {t("breadth")} {summary.average_breadth:.2f} |
                {t("candidates")} {summary.candidate_count} |
                {t("actionable")} {summary.actionable_count} |
                {t("safer")} {summary.safer_count}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_market_overview() -> None:
    st.markdown(f'<div class="section-label">{t("market_overview")}</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        render_summary_band(t("taiwan"), summary_service.build_market_summary("tw"))
    with right:
        render_summary_band(t("us"), summary_service.build_market_summary("us"))


def render_market_terminal_header(snapshot: Any, overview: Any) -> str:
    selected_market = _render_segmented_control(
        t("dashboard_market_view"),
        [t("taiwan"), t("us")],
        format_func=lambda value: value,
        key="dashboard_market_view",
    )
    market_key = "tw" if selected_market == t("taiwan") else "us"
    selected_range_key = _render_segmented_control(
        t("benchmark_range"),
        [key for key, _ in BENCHMARK_RANGE_OPTIONS],
        format_func=lambda key: t(dict(BENCHMARK_RANGE_OPTIONS)[key]),
        key=f"benchmark_range_{market_key}",
    )
    summary = summary_service.build_market_summary(market_key)
    benchmark_pairs = BENCHMARK_SETS[market_key]
    benchmark_snapshots = load_benchmark_snapshots(benchmark_pairs, selected_range_key)
    now_label = datetime.now().strftime("%m/%d %H:%M")
    summary_text = _market_bias_copy(summary) if summary else t("no_data")
    summary_date = _format_snapshot_date(getattr(summary, "summary_date", "")) if summary else "—"
    summary_breadth = f"{float(summary.average_breadth):.2f}" if summary is not None else "—"
    summary_candidates = str(int(getattr(summary, "candidate_count", 0))) if summary is not None else "—"
    summary_actionable = str(int(getattr(summary, "actionable_count", 0))) if summary is not None else "—"
    summary_safer = str(int(getattr(summary, "safer_count", 0))) if summary is not None else "—"

    st.markdown(
        f"""
        <div class="hero-shell">
            <div style="display:flex;justify-content:space-between;align-items:flex-end;gap:16px;">
                <div>
                    <div class="hero-title">{selected_market}</div>
                    <div class="hero-sub">{t("market_terminal")} | {localize_value(overview.overall_trend)}</div>
                </div>
                <div class="hero-time">{now_label} ({selected_market})</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    card_columns = st.columns(3)
    for column, (symbol, label_key) in zip(card_columns, benchmark_pairs):
        benchmark = benchmark_snapshots.get(
            symbol,
            {
                "label_key": label_key,
                "latest": None,
                "delta": None,
                "pct": None,
                "trend": [],
                "trend_window": 0,
                "range_key": selected_range_key,
                "has_data": False,
                "start_at": None,
                "end_at": None,
            },
        )
        positive = float(benchmark["delta"] or 0) >= 0
        change_color = "#16a34a" if positive else "#ef4444"
        delta_prefix = "+" if float(benchmark["delta"] or 0) >= 0 else ""
        with column:
            if benchmark.get("has_data"):
                st.markdown(
                    f"""
                    <div class="benchmark-card">
                        <div class="benchmark-name">{t(str(benchmark['label_key']))}</div>
                        <div class="benchmark-price">{float(benchmark['latest']):,.2f}</div>
                        <div class="benchmark-change" style="color:{change_color};">{delta_prefix}{float(benchmark['delta']):.2f}  {delta_prefix}{float(benchmark['pct']):.2f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.plotly_chart(build_benchmark_chart(benchmark["trend"], positive), use_container_width=True, config={"displayModeBar": False})
                st.caption(_benchmark_range_caption(str(benchmark.get("range_key", "1d")), int(benchmark.get("trend_window", 0) or 0)))
                start_at = str(benchmark.get("start_at") or "")
                end_at = str(benchmark.get("end_at") or "")
                if start_at and end_at:
                    st.caption(f"{start_at} -> {end_at}")
            else:
                st.markdown(
                    f"""
                    <div class="benchmark-card">
                        <div class="benchmark-name">{t(str(benchmark['label_key']))}</div>
                        <div class="benchmark-price">N/A</div>
                        <div class="benchmark-change" style="color:#94a3b8;">{t("benchmark_no_data")}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with st.container(border=True):
        left, right = st.columns((1.35, 1))
        with left:
            st.markdown(f'<div class="summary-title">{t("analysis_summary")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="summary-main">{localize_value(overview.sentiment_label)} / {overview.fear_greed_score:.0f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="summary-sub">{summary_text}</div>', unsafe_allow_html=True)
            _render_data_caption(f'{t("latest_analysis_date")}: {summary_date}')
        with right:
            k1, k2, k3, k4 = st.columns(4)
            k1.metric(t("breadth"), summary_breadth)
            k2.metric("候選" if LANG == "zh-TW" else "Candidates", summary_candidates)
            k3.metric(t("actionable"), summary_actionable)
            k4.metric("相對安全延續" if LANG == "zh-TW" else "Safer", summary_safer)

    return market_key


def render_session_briefs() -> None:
    tw_summary = summary_service.build_market_summary("tw")
    us_summary = summary_service.build_market_summary("us")
    st.markdown(f'<div class="section-label">{t("session_brief")}</div>', unsafe_allow_html=True)
    dates = []
    for summary in (tw_summary, us_summary):
        if summary is not None:
            dates.append(f'{summary.market_type.upper()}: {_format_snapshot_date(summary.summary_date)}')
    if dates:
        _render_data_caption(*dates)
    left, right = st.columns(2)
    for column, title, summary in (
        (left, t("tw_brief"), tw_summary),
        (right, t("us_brief"), us_summary),
    ):
        with column:
            if summary is None:
                st.info(t("no_data"))
                continue
            best_score = max((float(row.get("composite_signal_score", 0)) for row in summary.top_rows), default=0.0)
            avg_signal_score = (
                sum(float(row.get("composite_signal_score", 0)) for row in summary.top_rows) / len(summary.top_rows)
                if summary.top_rows
                else 0.0
            )
            st.markdown(
                f"""
                <div class="brief-card">
                    <div class="brief-head">
                        <div class="brief-title">{title}</div>
                        <div class="brief-bias">{localize_value(summary.regime)}</div>
                    </div>
                    <div class="brief-grid">
                        <div class="brief-kpi">
                            <div class="brief-kpi-label">{t("avg_score")}</div>
                            <div class="brief-kpi-value">{avg_signal_score:.1f}</div>
                        </div>
                        <div class="brief-kpi">
                            <div class="brief-kpi-label">{t("actionable")}</div>
                            <div class="brief-kpi-value">{summary.actionable_count}</div>
                        </div>
                        <div class="brief-kpi">
                            <div class="brief-kpi-label">{t("best_score")}</div>
                            <div class="brief-kpi-value">{best_score:.1f}</div>
                        </div>
                    </div>
                    <div class="brief-copy">{_market_bias_copy(summary)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_visual_scan(candidate_frame: pd.DataFrame, snapshot: Any, overview: Any) -> None:
    st.markdown(f'<div class="section-label">{t("visual_scan")}</div>', unsafe_allow_html=True)
    latest_date = _format_snapshot_date(candidate_frame["date"].max()) if not candidate_frame.empty and "date" in candidate_frame.columns else ""
    if latest_date:
        _render_data_caption(f'{t("snapshot_as_of")}: {latest_date}')
    lights = [
        (t("overall_trend"), localize_value(overview.overall_trend), *(_signal_tone(float(overview.fear_greed_score))), "總體盤勢" if LANG == "zh-TW" else "Macro tape"),
        (t("fear_greed"), f"{overview.fear_greed_score}/100", *(_signal_tone(float(overview.fear_greed_score))), "分數越高代表風險偏好越強" if LANG == "zh-TW" else "Higher means more risk appetite"),
        (t("breadth"), f"{overview.breadth_snapshot:.0f}/100", *(_signal_tone(float(overview.breadth_snapshot))), "分數越高代表參與面越廣" if LANG == "zh-TW" else "Higher breadth means broader participation"),
        ("VIX", f"{snapshot.vix:.2f}" if snapshot.vix is not None else "N/A", *(_signal_tone(_vix_comfort_score(snapshot.vix))), "VIX 越低通常越容易順勢操作" if LANG == "zh-TW" else "Lower VIX is usually easier"),
    ]
    light_columns = st.columns(4)
    for column, (name, value, color, tone, copy) in zip(light_columns, lights):
        with column:
            st.markdown(
                f"""
                <div class="light-card">
                    <div class="light-top">
                        <div class="light-name">{name}</div>
                        <span class="light-dot" style="background:{color}"></span>
                    </div>
                    <div class="light-value">{value}</div>
                    <div class="light-copy">{tone} | {copy}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    left, middle, right = st.columns((1, 1.1, 1))
    with left:
        st.markdown(f'<div class="section-label">{t("market_pulse")}</div>', unsafe_allow_html=True)
        st.plotly_chart(
            build_market_pulse_chart(snapshot, overview, candidate_frame),
            use_container_width=True,
            config={"displayModeBar": False},
            key="scan_visual_market_pulse_active",
        )
    with middle:
        st.markdown(f'<div class="section-label">{t("sector_heatmap")}</div>', unsafe_allow_html=True)
        st.plotly_chart(
            build_sector_heatmap(candidate_frame),
            use_container_width=True,
            config={"displayModeBar": False},
            key="scan_visual_sector_heatmap_active",
        )
    with right:
        st.markdown(f'<div class="section-label">{t("setup_distribution")}</div>', unsafe_allow_html=True)
        st.plotly_chart(
            build_setup_distribution_chart(candidate_frame),
            use_container_width=True,
            config={"displayModeBar": False},
            key="scan_visual_setup_distribution_active",
        )


def _render_rank_items(rows: list[dict[str, object]], score_key: str = "composite_signal_score", meta_mode: str = "leader") -> None:
    if not rows:
        st.info(t("no_data"))
        return
    for row in rows[:6]:
        company, sector = _display_name_for_row(pd.Series(row))
        score = float(row.get(score_key, 0) or 0)
        trend = get_ticker_score_trend_cached(str(row.get("ticker", "")))
        delta = ""
        if len(trend) >= 2:
            change = trend[-1] - trend[-2]
            delta = f" | {'+' if change >= 0 else ''}{change:.1f}"
        meta = (
            f"{sector} | {localize_value(row.get('recommendation_bucket', 'Watchlist'))}"
            if meta_mode == "leader"
            else f"{sector} | {localize_value(row.get('event_risk_note', 'clear'))}"
        )
        st.markdown(
            f"""
            <div class="rank-item">
                <div class="rank-left">
                    <div class="rank-name">{company}</div>
                    <div class="rank-meta">{row.get('ticker', '')} | {meta}</div>
                </div>
                <div class="rank-score">{score:.1f}{delta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_rank_boards(market_key: str | None = None) -> None:
    if market_key in {"tw", "us"}:
        summaries = [summary_service.build_market_summary(market_key)]
    else:
        summaries = [summary_service.build_market_summary("tw"), summary_service.build_market_summary("us")]
    leader_rows: list[dict[str, object]] = []
    risk_rows: list[dict[str, object]] = []
    for summary in summaries:
        if summary is None:
            continue
        leader_rows.extend(summary.top_rows)
        risk_rows.extend(summary.risk_rows)
    leader_rows = sorted(leader_rows, key=lambda row: float(row.get("composite_signal_score", 0) or 0), reverse=True)[:6]
    leader_tickers = {str(row.get("ticker", "")) for row in leader_rows}
    risk_rows = sorted(
        [row for row in risk_rows if str(row.get("ticker", "")) not in leader_tickers],
        key=lambda row: (float(row.get("event_risk_score", 50) or 50), float(row.get("composite_signal_score", 0) or 0)),
    )[:6]
    st.markdown(f'<div class="section-label">{t("rank_board")}</div>', unsafe_allow_html=True)
    dates = []
    for summary in summaries:
        if summary is not None:
            dates.append(f'{summary.market_type.upper()}: {_format_snapshot_date(summary.summary_date)}')
    if dates:
        _render_data_caption(*dates)
    left, right = st.columns(2)
    with left:
        st.markdown(f'<div class="section-label">{t("leader_board")}</div>', unsafe_allow_html=True)
        st.caption(t("leader_board_help"))
        with st.container(border=True):
            _render_rank_items(leader_rows, meta_mode="leader")
    with right:
        st.markdown(f'<div class="section-label">{t("risk_board")}</div>', unsafe_allow_html=True)
        st.caption(t("risk_board_help"))
        with st.container(border=True):
            if risk_rows:
                _render_rank_items(risk_rows, meta_mode="risk")
            else:
                st.info("目前沒有與領先名單明顯不同的高風險標的。" if LANG == "zh-TW" else "No distinct risk names beyond the current leaders.")


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
        chart_config[t("trend_mini")] = st.column_config.LineChartColumn(
            t("trend_mini"),
            width="medium",
            y_min=-12,
            y_max=12,
        )
    if t("score_trend") in table.columns:
        chart_config[t("score_trend")] = st.column_config.LineChartColumn(
            t("score_trend"),
            width="medium",
            y_min=0,
            y_max=100,
        )
    if t("score") in table.columns:
        chart_config[t("score")] = st.column_config.NumberColumn(
            t("score"),
            format="%.2f",
            width="small",
        )
    streak_label = "\u6cd5\u4eba\u9023\u8cb7\u5929\u6578" if LANG == "zh-TW" else "Institutional Buy Streak"
    if streak_label in table.columns:
        chart_config[streak_label] = st.column_config.NumberColumn(
            streak_label,
            format="%d",
            width="small",
        )
    if t("suggested_action") in table.columns:
        chart_config[t("suggested_action")] = st.column_config.TextColumn(
            t("suggested_action"),
            width="large",
        )
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config=chart_config or None,
    )


def render_focus_lists(candidate_frame: pd.DataFrame) -> None:
    st.markdown(f'<div class="section-label">{t("focus_lists")}</div>', unsafe_allow_html=True)
    if candidate_frame.empty:
        st.info(t("no_data"))
        return
    latest_date = candidate_frame["date"].max()
    _render_data_caption(f'{t("snapshot_as_of")}: {_format_snapshot_date(latest_date)}')
    latest = candidate_frame[candidate_frame["date"] == latest_date].copy()
    core_count = int((latest["universe_bucket"] == "core").sum()) if "universe_bucket" in latest.columns else 0
    explore_count = int((latest["universe_bucket"] == "explore").sum()) if "universe_bucket" in latest.columns else 0
    risk_count = int((latest["event_risk_note"] != "clear").sum()) if "event_risk_note" in latest.columns else 0
    core_label = f'{t("core_tab")} ({core_count})'
    explore_label = f'{t("explore_tab")} ({explore_count})'
    risk_label = f'{t("risk_tab")} ({risk_count})'
    core_tab, explore_tab, risk_tab = st.tabs([core_label, explore_label, risk_label])
    with core_tab:
        render_terminal_table(
            latest[latest["universe_bucket"] == "core"]
            .sort_values(by=["composite_signal_score", "institutional_buy_streak"], ascending=[False, False])
            .head(12),
            ["ticker", "company", "sector", "trend_mini", "score_trend", "recommendation_bucket", "composite_signal_score", "institutional_buy_streak", "suggested_action"],
        )
    with explore_tab:
        render_terminal_table(
            latest[latest["universe_bucket"] == "explore"]
            .sort_values(by=["composite_signal_score"], ascending=[False])
            .head(12),
            ["ticker", "company", "sector", "trend_mini", "score_trend", "recommendation_bucket", "composite_signal_score", "risk_level", "suggested_action"],
        )
    with risk_tab:
        render_terminal_table(
            latest[latest["event_risk_note"] != "clear"]
            .sort_values(by=["composite_signal_score"], ascending=[True])
            .head(12),
            ["ticker", "company", "sector", "trend_mini", "score_trend", "recommendation_bucket", "event_risk_note", "next_event_date", "risk_level"],
        )

    core_tab, explore_tab, risk_tab = st.tabs([t("core_tab"), t("explore_tab"), t("risk_tab")])
    with core_tab:
        render_terminal_table(
            latest[latest["universe_bucket"] == "core"]
            .sort_values(by=["composite_signal_score", "institutional_buy_streak"], ascending=[False, False])
            .head(12),
            ["ticker", "company", "sector", "trend_mini", "score_trend", "recommendation_bucket", "composite_signal_score", "institutional_buy_streak", "suggested_action"],
        )
    with explore_tab:
        render_terminal_table(
            latest[latest["universe_bucket"] == "explore"]
            .sort_values(by=["composite_signal_score"], ascending=[False])
            .head(12),
            ["ticker", "company", "sector", "trend_mini", "score_trend", "recommendation_bucket", "composite_signal_score", "risk_level", "suggested_action"],
        )
    with risk_tab:
        render_terminal_table(
            latest[latest["event_risk_note"] != "clear"]
            .sort_values(by=["composite_signal_score"], ascending=[True])
            .head(12),
            ["ticker", "company", "sector", "trend_mini", "score_trend", "recommendation_bucket", "event_risk_note", "next_event_date", "risk_level"],
        )


def render_decision_cards(candidate_frame: pd.DataFrame) -> None:
    st.markdown(f'<div class="section-label">{t("decision_cards")}</div>', unsafe_allow_html=True)
    st.caption(
        "綜合分數越高，代表越接近可執行。75 分以上通常進入可執行或候選，65-74 分代表差臨門一腳。"
        if LANG == "zh-TW"
        else f'{t("decision_score_label")}: {t("decision_score_help")}'
    )
    if candidate_frame.empty:
        st.info(t("no_data"))
        return
    latest_date = candidate_frame["date"].max()
    _render_data_caption(f'{t("snapshot_as_of")}: {_format_snapshot_date(latest_date)}')
    latest = (
        candidate_frame[candidate_frame["date"] == latest_date]
        .sort_values(by=["composite_signal_score", "institutional_buy_streak"], ascending=[False, False])
        .head(8)
    )
    for _, row in latest.iterrows():
        company_name, sector_name = _display_name_for_row(row)
        verdict_label, verdict_color = _decision_verdict(row)
        rationale = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in row.get("rationale", []))
        risks = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in row.get("risks", []))
        suggestion = maybe_translate_text(str(row.get("suggested_action", "")))
        level = maybe_translate_text(str(row.get("recommendation_level", "")))
        win_label = maybe_translate_text(str(row.get("win_rate_label", "")))
        risk_label = maybe_translate_text(str(row.get("risk_level", "")))
        reward_risk = maybe_translate_text(str(row.get("reward_risk_label", "")))
        forward_score = float(row.get("forward_score", 0))
        forward_notes = "".join(f"<li>{maybe_translate_text(item)}</li>" for item in row.get("forward_notes", []))
        if LANG == "zh-TW":
            verdict_copy = {
                t("verdict_buy"): "條件完整，可直接依風控計畫執行。",
                t("verdict_probe"): "先用小部位試單，確認延續後再加碼。",
                t("verdict_wait"): "先觀察，等條件更完整再出手。",
                t("verdict_avoid"): "目前風險偏高，暫時不要出手。",
            }.get(verdict_label, "")
        else:
            verdict_copy = ""
        st.markdown(
            f"""
            <div class="decision-card">
                <div class="decision-head">
                    <div>
                        <div class="decision-ticker">{row["ticker"]}</div>
                        <div class="decision-meta">
                            {company_name} | {t("sector")} {sector_name} <br/>
                            {t("signal_type")} {localize_value(row.get("signal_type", ""))} |
                            {localize_value(row.get("universe_bucket", "core"))} |
                            {localize_value(row.get("recommendation_bucket", "Watchlist"))}
                        </div>
                    </div>
                    <div class="decision-meta">{'綜合分數' if LANG == 'zh-TW' else t("decision_score_label")} {float(row.get("composite_signal_score", 0)):.2f}</div>
                </div>
                <div class="decision-meta" style="margin-bottom:8px;">
                    {'結論' if LANG == 'zh-TW' else t("decision_verdict")}：
                    <span style="color:{verdict_color};font-weight:800;">{verdict_label}</span>
                    {verdict_copy}
                </div>
                <span class="decision-pill">{level}</span>
                <span class="decision-pill">{t("win_label")}: {win_label}</span>
                <span class="decision-pill">{t("risk_label")}: {risk_label}</span>
                <span class="decision-pill">{t("reward_risk")}: {reward_risk}</span>
                <span class="decision-pill">{t("forward_score")}: {forward_score:.2f}</span>
                <span class="decision-pill">{t("event_risk")}: {localize_value(row.get("event_risk_note", "clear"))}</span>
                <div class="decision-label">{t("suggested_action")}</div>
                <div>{suggestion}</div>
                <div class="decision-label">{t("forward_notes")}</div>
                <ul class="decision-list">{forward_notes}</ul>
                <div class="decision-label">{t("rationale")}</div>
                <ul class="decision-list">{rationale}</ul>
                <div class="decision-label">{t("risks")}</div>
                <ul class="decision-list">{risks}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )



COPY["zh-TW"].update(
    {
        "decision_score_label": "綜合判讀分數",
        "decision_score_help": "80 分以上偏強，可正常看待；70-79 分可先小部位試單；60-69 分先觀察；60 分以下先避開。",
        "decision_verdict": "結論",
        "verdict_buy": "可買",
        "verdict_probe": "可試單",
        "verdict_wait": "先觀察",
        "verdict_avoid": "先避開",
        "leader_board_help": "這裡放的是目前最強、最接近可執行的標的。",
        "risk_board_help": "這裡放的是事件風險較高、容易影響勝率或不適合追價的標的。",
        "trend_mini": "短線走勢",
        "score_trend": "分數節奏",
        "rank_board": "熱度榜",
        "leader_board": "領先名單",
        "risk_board": "風險名單",
        "market_pulse": "市場脈搏",
        "sector_heatmap": "類股熱區",
        "setup_distribution": "訊號分布",
    }
)
TEXT = COPY["zh-TW"] | COPY.get(LANG, {})

ZH_DECISION_TEXT.update(
    {
        "Institutional buying has just turned positive.": "法人買盤剛轉正。",
        "Institutional buying is building into a second session.": "法人買盤延續到第 2 天。",
        "Relative strength is decisively above the market benchmark.": "相對強度明顯優於市場基準。",
        "Relative strength is supportive versus the benchmark.": "相對強度仍比市場基準健康。",
        "Price location is constructive and not excessively extended.": "價位位置健康，且未過度乖離。",
        "Entry quality is acceptable if execution stays disciplined.": "進場品質尚可，前提是執行紀律要嚴格。",
        "The market regime is supportive for trend-following entries.": "市場環境偏向有利順勢操作。",
        "The broader market is neutral, so follow-through may be slower.": "大盤偏中性，延續力可能較慢。",
        "The broader market is risk-off, so hit rates can fall quickly.": "大盤偏防守，勝率容易快速下降。",
        "This idea is in the Explore pool, so it should not outrank core large-cap names.": "這檔屬於觀察池，不應高於核心大型股的優先順序。",
        "This name belongs to the core monitoring pool.": "此標的屬於核心追蹤池。",
        "Event risk is manageable but still worth monitoring.": "事件風險可控，但仍值得持續追蹤。",
        "No major risk flags are active right now, but standard stop discipline still applies.": "目前沒有重大風險警示，但停損紀律仍要保留。",
        "The current signal does not yet have enough stacked evidence.": "目前訊號還沒有堆出足夠證據。",
        "Normal position sizing or staged entries on minor pullbacks.": "可用正常部位，或等待小拉回分批進場。",
        "Pilot size first, then add if confirmation holds.": "先用試單部位，確認延續後再加碼。",
        "Observe only until the odds improve.": "先觀察，等勝率提升再行動。",
        "Small trial size only; keep core capital focused on large caps.": "僅適合小部位試單，核心資金仍應聚焦大型股。",
        "High Conviction Core": "核心可買",
        "Actionable Setup": "可試單",
        "Watch and Wait": "先觀察",
        "High": "高",
        "Medium-High": "中高",
        "Medium-Low": "中低",
        "Medium": "中",
        "Favorable": "報酬優勢",
        "Balanced": "風報平衡",
        "Unclear": "風報不明",
    }
)


def _translate_macro_event_label(label: str) -> str:
    cleaned = str(label or "").strip().replace("_", " ").lower()
    if not cleaned:
        return ""
    if LANG != "zh-TW":
        return cleaned
    direct_map = {
        "cftc eur speculative net positions": "CFTC 歐元投機淨部位",
        "cftc eur speculative net position": "CFTC 歐元投機淨部位",
        "annual report": "年報",
        "ecb cipollone speech": "ECB Cipollone 談話",
        "ecb de guindos speech": "ECB De Guindos 談話",
        "ecb survey of monetary analysts": "ECB 貨幣分析師調查",
        "ecb survey of professional forecasters": "ECB 專業預測調查",
    }
    if cleaned in direct_map:
        return direct_map[cleaned]
    replacements = {
        "cftc": "CFTC",
        "eur": "歐元",
        "usd": "美元",
        "jpy": "日圓",
        "gbp": "英鎊",
        "speculative": "投機",
        "net": "淨",
        "position": "部位",
        "positions": "部位",
        "survey": "調查",
        "speech": "談話",
        "annual": "年度",
        "report": "報告",
        "earnings": "財報",
        "inflation": "通膨",
        "payrolls": "非農就業",
        "minutes": "會議紀要",
    }
    translated = cleaned
    for source, target in replacements.items():
        translated = translated.replace(source, target)
    return translated


def localize_value(value: object) -> str:
    text_value = str(value)
    mapping = {
        "Unknown": "未知" if LANG == "zh-TW" else "Unknown",
        "Calm": "平穩" if LANG == "zh-TW" else "Calm",
        "Neutral": "中性" if LANG == "zh-TW" else "Neutral",
        "Risk-Off": "Risk-Off / 防守" if LANG == "zh-TW" else "Risk-Off",
        "Risk-On": "偏多" if LANG == "zh-TW" else "Risk-On",
        "Risk-On Uptrend": "偏多上升趨勢" if LANG == "zh-TW" else "Risk-On Uptrend",
        "Balanced / Selective": "平衡 / 選擇性出手" if LANG == "zh-TW" else "Balanced / Selective",
        "Defensive / Risk-Off": "防守 / Risk-Off" if LANG == "zh-TW" else "Defensive / Risk-Off",
        "Greed": "貪婪" if LANG == "zh-TW" else "Greed",
        "Constructive": "建設性偏多" if LANG == "zh-TW" else "Constructive",
        "Cautious": "謹慎" if LANG == "zh-TW" else "Cautious",
        "Fear": "恐懼" if LANG == "zh-TW" else "Fear",
        "Watchlist": "觀察" if LANG == "zh-TW" else "Watchlist",
        "Actionable": "今日可執行" if LANG == "zh-TW" else "Actionable",
        "Candidate": "差臨門一腳" if LANG == "zh-TW" else "Candidate",
        "Safer Follow-Through": "相對安全延續" if LANG == "zh-TW" else "Safer Follow-Through",
        "core": "核心池" if LANG == "zh-TW" else "Core",
        "explore": "觀察池" if LANG == "zh-TW" else "Explore",
        "clear": "目前無明顯事件風險" if LANG == "zh-TW" else "clear",
        "DAY_1_EARLY": "第 1 天 / 起步" if LANG == "zh-TW" else "Day 1 Early",
        "DAY_2_BUILDING": "第 2 天 / 建倉中" if LANG == "zh-TW" else "Day 2 Building",
        "DAY_3_PLUS_SAFER": "第 3 天以上 / 相對更穩" if LANG == "zh-TW" else "Day 3+ Safer",
        "Institutional Accumulation": "法人順勢動能" if LANG == "zh-TW" else "Institutional Accumulation",
        "Panic Reversal": "恐慌極端反轉" if LANG == "zh-TW" else "Panic Reversal",
        "High": "高" if LANG == "zh-TW" else "High",
        "Medium": "中" if LANG == "zh-TW" else "Medium",
        "Medium-High": "中高" if LANG == "zh-TW" else "Medium-High",
        "Medium-Low": "中低" if LANG == "zh-TW" else "Medium-Low",
        "Favorable": "風報比偏佳" if LANG == "zh-TW" else "Favorable",
        "Balanced": "風報比平衡" if LANG == "zh-TW" else "Balanced",
        "Unclear": "風報比不明" if LANG == "zh-TW" else "Unclear",
        "High Conviction Core": "高信念核心" if LANG == "zh-TW" else "High Conviction Core",
        "Actionable Setup": "可執行設定" if LANG == "zh-TW" else "Actionable Setup",
        "Watch and Wait": "先觀察" if LANG == "zh-TW" else "Watch and Wait",
    }
    if text_value in mapping:
        return mapping[text_value]
    if text_value.startswith("macro_event_imminent:") or text_value.startswith("macro_event_near:"):
        prefix, label = text_value.split(":", 1)
        prefix_label = "總經事件臨近" if prefix == "macro_event_imminent" and LANG == "zh-TW" else "Macro imminent"
        if prefix == "macro_event_near":
            prefix_label = "總經事件接近" if LANG == "zh-TW" else "Macro near"
        return f"{prefix_label}: {_translate_macro_event_label(label)}"
    if LANG == "zh-TW" and text_value in ZH_DECISION_TEXT:
        return ZH_DECISION_TEXT[text_value]
    return text_value


def maybe_translate_text(text_value: str) -> str:
    if LANG != "zh-TW":
        return text_value
    if text_value.startswith("Institutional buying has persisted for ") and text_value.endswith(" sessions."):
        days = text_value.replace("Institutional buying has persisted for ", "").replace(" sessions.", "").strip()
        return f"法人買盤已連續 {days} 天。"
    if text_value.startswith("Event risk is elevated:"):
        detail = text_value.replace("Event risk is elevated:", "").strip()
        return f"事件風險偏高：{_translate_macro_event_label(detail)}"
    if text_value.startswith("macro_event_imminent ("):
        inner = text_value.replace("macro_event_imminent (", "").rstrip(")")
        return f"總經事件臨近：{_translate_macro_event_label(inner)}"
    if text_value.startswith("macro_event_near ("):
        inner = text_value.replace("macro_event_near (", "").rstrip(")")
        return f"總經事件接近：{_translate_macro_event_label(inner)}"
    if text_value.startswith("Volatility is elevated; position sizing should stay conservative."):
        return "波動偏高，部位大小要保守。"
    if text_value.startswith("Breadth is weak, so single-name breakouts may fail more often."):
        return "市場廣度偏弱，單一個股突破的失敗率會提高。"
    if text_value.endswith(" names are carrying event-risk flags."):
        count = text_value.split(" ", 1)[0]
        return f"{count} 檔股票目前帶有事件風險標記。"
    if text_value.startswith("No major market-wide warnings are flashing right now."):
        return "目前沒有明顯的市場級風險警報。"
    if text_value.startswith("Theme support:"):
        return text_value.replace("Theme support:", "主題支撐：")
    if text_value.startswith("Institutional flow persistence supports the forward setup."):
        return "法人資金的延續性，支撐這筆前瞻設定。"
    if text_value.startswith("Relative strength confirms demand leadership."):
        return "相對強度確認了資金需求領先。"
    if text_value.startswith("Forward demand narrative is strong enough for a starter position."):
        return "前瞻需求敘事夠強，可以先用試單部位介入。"
    if " | " in text_value and len(text_value.split(" | ")) == 3:
        dt, region, title = text_value.split(" | ", 2)
        region_map = {"US": "美國", "EU": "歐洲", "JP": "日本", "CN": "中國", "TW": "台灣"}
        return f"{dt} | {region_map.get(region, region)} | {_translate_macro_event_label(title)}"
    return ZH_DECISION_TEXT.get(text_value, text_value)


def build_market_pulse_chart(snapshot: Any, overview: Any, candidate_frame: pd.DataFrame) -> go.Figure:
    latest = _latest_candidates(candidate_frame)
    setup_quality = 50.0
    if not latest.empty and "composite_signal_score" in latest.columns:
        setup_quality = float(latest["composite_signal_score"].fillna(0).mean())
    pulse = pd.DataFrame(
        [
            {"metric": "VIX 舒適度" if LANG == "zh-TW" else "VIX Comfort", "score": _vix_comfort_score(snapshot.vix)},
            {"metric": t("fear_greed"), "score": float(overview.fear_greed_score)},
            {"metric": t("breadth"), "score": float(overview.breadth_snapshot)},
            {"metric": "個股品質" if LANG == "zh-TW" else "Setup Quality", "score": setup_quality},
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
        texttemplate="%{label}<br>%{value} 檔<br>%{color:.0f}",
        hovertemplate="%{label}<br>" + ("檔數" if LANG == "zh-TW" else "Names") + ": %{value}<br>" + ("平均分數" if LANG == "zh-TW" else "Avg Score") + ": %{color:.1f}<extra></extra>",
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
    fallback_sector = "未知" if LANG == "zh-TW" else "Unknown"
    if market_type == "tw":
        return name_zh or name_en or ticker, sector or fallback_sector
    if LANG == "zh-TW":
        if name_en and name_zh:
            return f"{name_en} / {name_zh}", sector or fallback_sector
        return name_zh or name_en or ticker, sector or fallback_sector
    return name_en or name_zh or ticker, sector or fallback_sector


def _signal_tone(score: float) -> tuple[str, str]:
    if score >= 75:
        return ("#2fbf71", "偏多" if LANG == "zh-TW" else "Risk-on")
    if score >= 60:
        return ("#8bd36c", "建設性" if LANG == "zh-TW" else "Constructive")
    if score >= 45:
        return ("#f6c84c", "中性" if LANG == "zh-TW" else "Neutral")
    if score >= 30:
        return ("#ff8a4c", "轉弱" if LANG == "zh-TW" else "Weakening")
    return ("#ff5a6b", "防守" if LANG == "zh-TW" else "Defensive")


def _market_bias_copy(summary: Any) -> str:
    if summary is None:
        return t("no_data")
    regime = localize_value(summary.regime)
    if LANG == "zh-TW":
        return f"{regime}，候選 {summary.candidate_count} 檔，可行動 {summary.actionable_count} 檔，相對安全延續 {summary.safer_count} 檔。"
    return f"{regime}, {summary.candidate_count} candidates, {summary.actionable_count} actionable, {summary.safer_count} safer follow-through names."


def render_visual_scan(candidate_frame: pd.DataFrame, snapshot: Any, overview: Any) -> None:
    st.markdown(f'<div class="section-label">{t("visual_scan")}</div>', unsafe_allow_html=True)
    latest_date = _format_snapshot_date(candidate_frame["date"].max()) if not candidate_frame.empty and "date" in candidate_frame.columns else ""
    if latest_date:
        _render_data_caption(f'{t("snapshot_as_of")}: {latest_date}')
    lights = [
        (t("overall_trend"), localize_value(overview.overall_trend), *(_signal_tone(float(overview.fear_greed_score))), "看整體市場是否順風" if LANG == "zh-TW" else "Macro tape"),
        (t("fear_greed"), f"{overview.fear_greed_score}/100", *(_signal_tone(float(overview.fear_greed_score))), "分數越高代表越敢冒險" if LANG == "zh-TW" else "Higher means more risk appetite"),
        (t("breadth"), f"{overview.breadth_snapshot:.0f}/100", *(_signal_tone(float(overview.breadth_snapshot))), "越高代表上漲參與面越廣" if LANG == "zh-TW" else "Higher breadth means broader participation"),
        ("VIX", f"{snapshot.vix:.2f}" if snapshot.vix is not None else "N/A", *(_signal_tone(_vix_comfort_score(snapshot.vix))), "VIX 越低通常越適合順勢" if LANG == "zh-TW" else "Lower VIX is usually easier"),
    ]
    light_columns = st.columns(4)
    for column, (name, value, color, tone, copy) in zip(light_columns, lights):
        with column:
            st.markdown(
                f"""
                <div class="light-card">
                    <div class="light-top">
                        <div class="light-name">{name}</div>
                        <span class="light-dot" style="background:{color}"></span>
                    </div>
                    <div class="light-value">{value}</div>
                    <div class="light-copy">{tone} | {copy}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    left, middle, right = st.columns((1, 1.1, 1))
    with left:
        st.markdown(f'<div class="section-label">{t("market_pulse")}</div>', unsafe_allow_html=True)
        st.plotly_chart(build_market_pulse_chart(snapshot, overview, candidate_frame), use_container_width=True, config={"displayModeBar": False})
    with middle:
        st.markdown(f'<div class="section-label">{t("sector_heatmap")}</div>', unsafe_allow_html=True)
        st.plotly_chart(build_sector_heatmap(candidate_frame), use_container_width=True, config={"displayModeBar": False})
    with right:
        st.markdown(f'<div class="section-label">{t("setup_distribution")}</div>', unsafe_allow_html=True)
        st.plotly_chart(build_setup_distribution_chart(candidate_frame), use_container_width=True, config={"displayModeBar": False})


def render_rank_boards(market_key: str | None = None) -> None:
    if market_key in {"tw", "us"}:
        summaries = [summary_service.build_market_summary(market_key)]
    else:
        summaries = [summary_service.build_market_summary("tw"), summary_service.build_market_summary("us")]
    leader_rows: list[dict[str, object]] = []
    risk_rows: list[dict[str, object]] = []
    for summary in summaries:
        if summary is None:
            continue
        leader_rows.extend(summary.top_rows)
        risk_rows.extend(summary.risk_rows)
    leader_rows = sorted(leader_rows, key=lambda row: float(row.get("composite_signal_score", 0) or 0), reverse=True)[:6]
    leader_tickers = {str(row.get("ticker", "")) for row in leader_rows}
    risk_rows = sorted(
        [row for row in risk_rows if str(row.get("ticker", "")) not in leader_tickers],
        key=lambda row: (float(row.get("event_risk_score", 50) or 50), float(row.get("composite_signal_score", 0) or 0)),
    )[:6]
    st.markdown(f'<div class="section-label">{t("rank_board")}</div>', unsafe_allow_html=True)
    dates = []
    for summary in summaries:
        if summary is not None:
            dates.append(f'{summary.market_type.upper()}: {_format_snapshot_date(summary.summary_date)}')
    if dates:
        _render_data_caption(*dates)
    left, right = st.columns(2)
    with left:
        st.markdown(f'<div class="section-label">{t("leader_board")}</div>', unsafe_allow_html=True)
        st.caption(t("leader_board_help"))
        with st.container(border=True):
            _render_rank_items(leader_rows, meta_mode="leader")
    with right:
        st.markdown(f'<div class="section-label">{t("risk_board")}</div>', unsafe_allow_html=True)
        st.caption(t("risk_board_help"))
        with st.container(border=True):
            if risk_rows:
                _render_rank_items(risk_rows, meta_mode="risk")
            else:
                st.info("目前沒有與領先名單明顯不同的高風險標的。" if LANG == "zh-TW" else "No distinct risk names beyond the current leaders.")


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
        "institutional_buy_streak": "法人連買天數" if LANG == "zh-TW" else "Institutional Buy Streak",
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
    streak_label = "法人連買天數" if LANG == "zh-TW" else "Institutional Buy Streak"
    if streak_label in table.columns:
        chart_config[streak_label] = st.column_config.NumberColumn(streak_label, format="%d")
    if t("suggested_action") in table.columns:
        chart_config[t("suggested_action")] = st.column_config.TextColumn(t("suggested_action"), width="large")
    st.dataframe(table, use_container_width=True, hide_index=True, column_config=chart_config or None)


def render_decision_cards(candidate_frame: pd.DataFrame) -> None:
    st.markdown(f'<div class="section-label">{t("decision_cards")}</div>', unsafe_allow_html=True)
    st.caption("80 分以上偏積極，70-79 分偏試單，60-69 分先觀察，低於 60 分先避開。" if LANG == "zh-TW" else f'{t("decision_score_label")}: {t("decision_score_help")}')
    if candidate_frame.empty:
        st.info(t("no_data"))
        return
    latest_date = candidate_frame["date"].max()
    _render_data_caption(f'{t("snapshot_as_of")}: {_format_snapshot_date(latest_date)}')
    latest = (
        candidate_frame[candidate_frame["date"] == latest_date]
        .sort_values(by=["composite_signal_score", "institutional_buy_streak"], ascending=[False, False])
        .head(8)
    )
    verdicts = [_decision_verdict(row)[0] for _, row in latest.iterrows()]
    summary_cols = st.columns(4)
    labels = [t("verdict_buy"), t("verdict_probe"), t("verdict_wait"), t("verdict_avoid")]
    for column, label in zip(summary_cols, labels):
        column.metric(label, verdicts.count(label))
    for idx, (_, row) in enumerate(latest.iterrows()):
        company_name, sector_name = _display_name_for_row(row)
        verdict_label, verdict_color = _decision_verdict(row)
        score = float(row.get("composite_signal_score", 0) or 0)
        level = maybe_translate_text(str(row.get("recommendation_level", "")))
        suggestion = maybe_translate_text(str(row.get("suggested_action", "")))
        win_label = maybe_translate_text(str(row.get("win_rate_label", "")))
        risk_label = maybe_translate_text(str(row.get("risk_level", "")))
        reward_risk = maybe_translate_text(str(row.get("reward_risk_label", "")))
        forward_score = float(row.get("forward_score", 0) or 0)
        risk_note = localize_value(row.get("event_risk_note", "clear"))
        rationale_items = [maybe_translate_text(item) for item in row.get("rationale", []) if item]
        forward_items = [maybe_translate_text(item) for item in row.get("forward_notes", []) if item]
        risk_items = [maybe_translate_text(item) for item in row.get("risks", []) if item]
        title = f'{row["ticker"]} | {company_name} | {verdict_label} | {score:.1f}'
        with st.expander(title, expanded=(idx == 0)):
            top_left, top_right = st.columns((1.2, 1))
            with top_left:
                st.markdown(f'**{company_name}**')
                bucket_label = localize_value(row.get("recommendation_bucket", "Watchlist"))
                signal_label = localize_value(row.get("signal_type", ""))
                universe_label = localize_value(row.get("universe_bucket", "core"))
                st.caption(f'{t("sector")} {sector_name} | {t("signal_type")} {signal_label} | {universe_label} | {bucket_label}')
            with top_right:
                st.markdown(f'<div style="text-align:right;color:{verdict_color};font-weight:800;">{verdict_label}</div>', unsafe_allow_html=True)
                st.caption(f'{t("decision_score_label")}: {score:.2f}')
            metric_cols = st.columns(5)
            metric_cols[0].metric(level or ("結論" if LANG == "zh-TW" else "Verdict"), f'{score:.1f}')
            metric_cols[1].metric(t("win_label"), win_label)
            metric_cols[2].metric(t("risk_label"), risk_label)
            metric_cols[3].metric(t("reward_risk"), reward_risk)
            metric_cols[4].metric(t("forward_score"), f'{forward_score:.1f}')
            st.markdown(f'**{t("suggested_action")}**')
            st.write(suggestion or "-")
            if risk_note:
                st.caption(f'{t("event_risk")}: {risk_note}')
            notes_left, notes_right = st.columns(2)
            with notes_left:
                st.markdown(f'**{t("rationale")}**')
                st.markdown("\n".join(f'- {item}' for item in rationale_items) if rationale_items else '-')
                st.markdown(f'**{t("forward_notes")}**')
                st.markdown("\n".join(f'- {item}' for item in forward_items) if forward_items else '-')
            with notes_right:
                st.markdown(f'**{t("risks")}**')
                st.markdown("\n".join(f'- {item}' for item in risk_items) if risk_items else '-')


def render_dashboard(candidate_frame: pd.DataFrame) -> None:
    snapshot = dashboard_service.build_snapshot()
    overview = overview_service.build()
    st.title(t("app_title"))
    st.caption(t("app_caption"))
    render_analysis_feedback()
    latest_summary = st.session_state.get("analysis_summary")
    if latest_summary:
        render_analysis_summary(latest_summary)
    selected_market_key = render_market_terminal_header(snapshot, overview)
    market_candidate_frame = filter_candidate_frame_for_market(candidate_frame, selected_market_key)

    top_metrics = st.columns(4)
    vix_zone, _ = describe_vix(snapshot.vix)
    top_metrics[0].metric(t("vix"), f"{snapshot.vix:.2f}" if snapshot.vix is not None else "N/A", delta=vix_zone if snapshot.vix is not None else None)
    top_metrics[1].metric(t("sentiment"), localize_value(snapshot.market_sentiment), delta=describe_fear_greed(overview.fear_greed_score)[0])
    top_metrics[2].metric(t("open_pnl"), f"{snapshot.total_open_pnl:.2f}%")
    top_metrics[3].metric(t("win_rate"), f"{snapshot.win_rate:.2f}%")

    render_run_controls()
    overview_tab, scan_tab, names_tab = st.tabs(
        [
            "市場總覽" if LANG == "zh-TW" else "Market Overview",
            "視覺掃盤" if LANG == "zh-TW" else "Visual Scan",
            "名單與決策" if LANG == "zh-TW" else "Lists & Decisions",
        ]
    )
    with overview_tab:
        render_market_state()
        render_session_briefs()
        render_market_overview()
    with scan_tab:
        scan_pulse_tab, scan_heat_tab, scan_dist_tab, scan_rank_tab = st.tabs(
            [
                "市場脈搏" if LANG == "zh-TW" else "Pulse",
                "類股熱區" if LANG == "zh-TW" else "Heatmap",
                "建議分佈" if LANG == "zh-TW" else "Distribution",
                "榜單" if LANG == "zh-TW" else "Boards",
            ]
        )
        with scan_pulse_tab:
            render_visual_scan(market_candidate_frame, snapshot, overview)
        with scan_heat_tab:
            st.markdown(f'<div class="section-label">{t("sector_heatmap")}</div>', unsafe_allow_html=True)
            st.plotly_chart(build_sector_heatmap(market_candidate_frame), use_container_width=True, config={"displayModeBar": False}, key="scan_tab_sector_heatmap")
        with scan_dist_tab:
            st.markdown(f'<div class="section-label">{t("setup_distribution")}</div>', unsafe_allow_html=True)
            st.plotly_chart(build_setup_distribution_chart(market_candidate_frame), use_container_width=True, config={"displayModeBar": False}, key="scan_tab_setup_distribution")
        with scan_rank_tab:
            render_rank_boards(selected_market_key)
    with names_tab:
        manual_tab, focus_tab, decision_tab = st.tabs(
            [
                "手動追蹤" if LANG == "zh-TW" else "Manual Tracking",
                t("focus_lists"),
                t("decision_cards"),
            ]
        )
        with manual_tab:
            render_manual_tracking(market_candidate_frame)
        with focus_tab:
            render_focus_lists(market_candidate_frame)
        with decision_tab:
            left, right = st.columns((1.12, 0.88))
            with left:
                render_decision_cards(market_candidate_frame)
            with right:
                render_rank_boards(selected_market_key)

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
    selected_market = c1.selectbox(t("market"), [t("all"), "tw", "us"])
    selected_bucket = c2.selectbox(t("bucket"), [t("all"), "Safer Follow-Through", "Actionable", "Watchlist"])
    min_score = c3.slider(t("min_score"), min_value=0, max_value=100, value=60)
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
                    "recommendation_level": "建議等級" if LANG == "zh-TW" else "Recommendation Level",
                    "win_rate_label": t("win_label"),
                    "risk_level": t("risk_label"),
                    "forward_score": t("forward_score"),
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    with right:
        ticker = st.text_input(t("ticker"), value="2330.TW")
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
        with why_tab:
            st.markdown(f"**{t('suggested_action')}**  \n{maybe_translate_text(str(latest_row.get('suggested_action', '')))}")
            st.markdown(f"**{t('rationale')}**")
            for item in latest_row.get("rationale", []):
                st.write(f"- {maybe_translate_text(item)}")
            st.markdown(f"**{t('risks')}**")
            for item in latest_row.get("risks", []):
                st.write(f"- {maybe_translate_text(item)}")


def render_health_check() -> None:
    st.markdown(f'<div class="page-title">{t("health")}</div>', unsafe_allow_html=True)
    if st.button("Run Source Diagnostics", use_container_width=True):
        with st.spinner("Checking market-data sources..."):
            rows = market_data.diagnose_providers()
        frame = pd.DataFrame(rows)
        if LANG == "zh-TW":
            frame = frame.rename(columns={"source": "來源", "status": "狀態", "latency_ms": "延遲(ms)", "note": "說明"})
            frame["狀態"] = frame["狀態"].map(lambda s: "正常" if s == "ok" else "失敗")
        st.dataframe(frame, use_container_width=True, hide_index=True)


inject_styles()

language_options = {"繁體中文": "zh-TW", "English": "en"}
selected_label = st.sidebar.selectbox(
    f'Language / {COPY["zh-TW"]["language"]}',
    options=list(language_options.keys()),
    index=0 if LANG == "zh-TW" else 1,
)
TEXT = COPY["zh-TW"] | COPY[language_options[selected_label]]
render_runtime_settings_panel()

candidate_frame = load_candidate_frame()
nav = st.sidebar.radio(t("view"), [t("dashboard"), t("portfolio"), t("screener"), t("health")], index=0)

if nav == t("dashboard"):
    render_dashboard(candidate_frame)
elif nav == t("portfolio"):
    render_portfolio()
elif nav == t("health"):
    render_health_check()
else:
    render_screener(candidate_frame)
