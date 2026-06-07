from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_key: str = Field(default="", alias="SUPABASE_KEY")
    supabase_service_key: str = Field(default="", alias="SUPABASE_SERVICE_KEY")
    supabase_anon_key: str = Field(default="", alias="SUPABASE_ANON_KEY")
    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_allowed_chat_id: str = Field(alias="TELEGRAM_ALLOWED_CHAT_ID")
    finnhub_api_key: str = Field(default="", alias="FINNHUB_API_KEY")
    finnhub_api_keys: str = Field(default="", alias="FINNHUB_API_KEYS")
    fmp_api_keys: str = Field(default="", alias="FMP_API_KEYS")
    finmind_api_token: str = Field(default="", alias="FINMIND_API_TOKEN")
    app_language: str = Field(default="zh-TW", alias="APP_LANGUAGE")
    app_timezone: str = Field(default="Asia/Taipei", alias="APP_TIMEZONE")
    tw_market_analysis_hour: int = Field(default=17, alias="TW_MARKET_ANALYSIS_HOUR")
    us_market_analysis_hour: int = Field(default=8, alias="US_MARKET_ANALYSIS_HOUR")
    defense_check_interval_minutes: int = Field(default=30, alias="DEFENSE_CHECK_INTERVAL_MINUTES")
    enable_defense_monitor: bool = Field(default=False, alias="ENABLE_DEFENSE_MONITOR")
    default_large_cap_only: bool = Field(default=True, alias="DEFAULT_LARGE_CAP_ONLY")
    default_risk_tolerance_percent: float = Field(default=5.0, alias="DEFAULT_RISK_TOLERANCE_PERCENT")
    default_min_institutional_buy_streak: int = Field(default=3, alias="DEFAULT_MIN_INSTITUTIONAL_BUY_STREAK")
    high_risk_event_dates: str = Field(default="", alias="HIGH_RISK_EVENT_DATES")
    tw_core_tickers: str = Field(default="", alias="TW_CORE_TICKERS")
    us_core_tickers: str = Field(default="", alias="US_CORE_TICKERS")
    tw_explore_tickers: str = Field(default="", alias="TW_EXPLORE_TICKERS")
    us_explore_tickers: str = Field(default="", alias="US_EXPLORE_TICKERS")
    tw_explore_limit: int = Field(default=12, alias="TW_EXPLORE_LIMIT")
    us_explore_limit: int = Field(default=12, alias="US_EXPLORE_LIMIT")
    tw_manual_watch_tickers: str = Field(default="", alias="TW_MANUAL_WATCH_TICKERS")
    us_manual_watch_tickers: str = Field(default="", alias="US_MANUAL_WATCH_TICKERS")
    tw_manual_hot_tickers: str = Field(default="", alias="TW_MANUAL_HOT_TICKERS")
    us_manual_hot_tickers: str = Field(default="", alias="US_MANUAL_HOT_TICKERS")
    tw_excluded_tickers: str = Field(default="", alias="TW_EXCLUDED_TICKERS")
    us_excluded_tickers: str = Field(default="", alias="US_EXCLUDED_TICKERS")
    enable_live_forward_signals: bool = Field(default=False, alias="ENABLE_LIVE_FORWARD_SIGNALS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
