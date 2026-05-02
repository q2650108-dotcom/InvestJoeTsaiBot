from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_key: str = Field(alias="SUPABASE_KEY")
    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_allowed_chat_id: str = Field(alias="TELEGRAM_ALLOWED_CHAT_ID")
    finnhub_api_key: str = Field(default="", alias="FINNHUB_API_KEY")
    app_timezone: str = Field(default="Asia/Taipei", alias="APP_TIMEZONE")
    tw_market_analysis_hour: int = Field(default=17, alias="TW_MARKET_ANALYSIS_HOUR")
    us_market_analysis_hour: int = Field(default=8, alias="US_MARKET_ANALYSIS_HOUR")
    defense_check_interval_minutes: int = Field(default=30, alias="DEFENSE_CHECK_INTERVAL_MINUTES")
    default_large_cap_only: bool = Field(default=True, alias="DEFAULT_LARGE_CAP_ONLY")
    default_risk_tolerance_percent: float = Field(default=5.0, alias="DEFAULT_RISK_TOLERANCE_PERCENT")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
