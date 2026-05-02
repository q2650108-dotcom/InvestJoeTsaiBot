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
    institutional_buy_streak integer,
    entry_timing text,
    created_at timestamptz not null default now(),
    unique (date, ticker, signal_type)
);

alter table daily_analysis
    add column if not exists institutional_buy_streak integer;

alter table daily_analysis
    add column if not exists entry_timing text;

create index if not exists idx_daily_analysis_ticker_date
    on daily_analysis (ticker, date desc);

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
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table user_settings
    add column if not exists min_institutional_buy_streak integer not null default 3;

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
