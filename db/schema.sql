create extension if not exists "pgcrypto";

create table if not exists daily_analysis (
    id uuid primary key default gen_random_uuid(),
    date date not null,
    ticker text not null,
    type text not null check (type in ('tw', 'us')),
    close_price double precision not null,
    volume bigint not null,
    ma_20 double precision,
    ma_60 double precision,
    institutional_net_buy bigint not null default 0,
    signal_type text not null,
    is_large_cap boolean not null default true,
    universe_bucket text not null default 'core',
    institutional_buy_streak integer,
    entry_timing text,
    market_regime text,
    market_regime_score double precision,
    breadth_score double precision,
    relative_strength_score double precision,
    institutional_conviction_score double precision,
    event_risk_score double precision,
    next_event_date date,
    event_risk_note text,
    entry_quality_score double precision,
    composite_signal_score double precision,
    recommendation_bucket text,
    confluence_score double precision,
    confluence_classification text,
    strategy_scores jsonb,
    confluence_reasons jsonb,
    stop_loss_price double precision,
    created_at timestamptz not null default now(),
    unique (date, ticker, signal_type)
);

alter table daily_analysis
    add column if not exists universe_bucket text not null default 'core';

alter table daily_analysis
    add column if not exists institutional_buy_streak integer;

alter table daily_analysis
    add column if not exists entry_timing text;

alter table daily_analysis
    add column if not exists market_regime text;

alter table daily_analysis
    add column if not exists market_regime_score double precision;

alter table daily_analysis
    add column if not exists breadth_score double precision;

alter table daily_analysis
    add column if not exists relative_strength_score double precision;

alter table daily_analysis
    add column if not exists institutional_conviction_score double precision;

alter table daily_analysis
    add column if not exists event_risk_score double precision;

alter table daily_analysis
    add column if not exists next_event_date date;

alter table daily_analysis
    add column if not exists event_risk_note text;

alter table daily_analysis
    add column if not exists entry_quality_score double precision;

alter table daily_analysis
    add column if not exists composite_signal_score double precision;

alter table daily_analysis
    add column if not exists recommendation_bucket text;

alter table daily_analysis
    add column if not exists confluence_score double precision;

alter table daily_analysis
    add column if not exists confluence_classification text;

alter table daily_analysis
    add column if not exists strategy_scores jsonb;

alter table daily_analysis
    add column if not exists confluence_reasons jsonb;

alter table daily_analysis
    add column if not exists stop_loss_price double precision;

create index if not exists idx_daily_analysis_ticker_date
    on daily_analysis (ticker, date desc);

create table if not exists analysis_runs (
    id uuid primary key default gen_random_uuid(),
    market_type text not null check (market_type in ('tw', 'us')),
    trade_date date not null,
    scanned_tickers integer not null default 0,
    data_ready_tickers integer not null default 0,
    skipped_data_tickers integer not null default 0,
    no_signal_tickers integer not null default 0,
    signal_count integer not null default 0,
    skipped_reason_counts jsonb not null default '{}'::jsonb,
    no_signal_reason_counts jsonb not null default '{}'::jsonb,
    core_ticker_count integer not null default 0,
    explore_ticker_count integer not null default 0,
    stage_counts jsonb not null default '{}'::jsonb,
    stage_rows jsonb not null default '[]'::jsonb,
    run_at timestamptz not null default now(),
    unique (market_type, trade_date)
);

create index if not exists idx_analysis_runs_market_trade_date
    on analysis_runs (market_type, trade_date desc);

create table if not exists paper_trades (
    id uuid primary key default gen_random_uuid(),
    ticker text not null,
    buy_date date not null,
    buy_price double precision not null,
    stop_loss_price double precision not null,
    status text not null check (status in ('OPEN', 'CLOSED')),
    sell_date date,
    sell_price double precision,
    pnl_percent double precision,
    created_at timestamptz not null default now()
);

create index if not exists idx_paper_trades_status_ticker
    on paper_trades (status, ticker);

create table if not exists user_settings (
    telegram_chat_id text primary key,
    large_cap_only boolean not null default true,
    risk_tolerance_percent double precision not null default 5.0,
    min_institutional_buy_streak integer not null default 3,
    app_language text not null default 'zh-TW',
    high_risk_event_dates text not null default '',
    tw_core_tickers text not null default '',
    us_core_tickers text not null default '',
    tw_explore_tickers text not null default '',
    us_explore_tickers text not null default '',
    tw_explore_limit integer not null default 12,
    us_explore_limit integer not null default 8,
    tw_manual_watch_tickers text not null default '',
    us_manual_watch_tickers text not null default '',
    tw_manual_hot_tickers text not null default '',
    us_manual_hot_tickers text not null default '',
    tw_excluded_tickers text not null default '',
    us_excluded_tickers text not null default '',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table user_settings
    add column if not exists min_institutional_buy_streak integer not null default 3;

alter table user_settings
    add column if not exists app_language text not null default 'zh-TW';

alter table user_settings
    add column if not exists high_risk_event_dates text not null default '';

alter table user_settings
    add column if not exists tw_core_tickers text not null default '';

alter table user_settings
    add column if not exists us_core_tickers text not null default '';

alter table user_settings
    add column if not exists tw_explore_tickers text not null default '';

alter table user_settings
    add column if not exists us_explore_tickers text not null default '';

alter table user_settings
    add column if not exists tw_explore_limit integer not null default 12;

alter table user_settings
    add column if not exists us_explore_limit integer not null default 8;

alter table user_settings
    add column if not exists tw_manual_watch_tickers text not null default '';

alter table user_settings
    add column if not exists us_manual_watch_tickers text not null default '';

alter table user_settings
    add column if not exists tw_manual_hot_tickers text not null default '';

alter table user_settings
    add column if not exists us_manual_hot_tickers text not null default '';

alter table user_settings
    add column if not exists tw_excluded_tickers text not null default '';

alter table user_settings
    add column if not exists us_excluded_tickers text not null default '';

create or replace function set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_user_settings_updated_at on user_settings;
create trigger trg_user_settings_updated_at
before update on user_settings
for each row
execute procedure set_updated_at();
