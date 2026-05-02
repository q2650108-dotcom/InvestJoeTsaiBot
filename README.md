# Smart Swing Agent

Smart Swing Agent is a Python-based swing trading assistant for Taiwan and US equities.  
This repository includes:

- a scheduled backend analysis engine
- Telegram bot commands for paper trading workflows
- Supabase/PostgreSQL schema
- a Streamlit dashboard for portfolio and screener views
- unit tests for the core signal and risk logic

## Product Scope

The current implementation follows the specification in [gemini-code-1777685860630.md](C:/Users/MAN/Desktop/Codex/InvestBot/gemini-code-1777685860630.md) and focuses on:

- post-market screening
- defensive risk monitoring
- paper trade lifecycle tracking
- visual inspection of open trades and historical signals

## Project Structure

```text
db/                    Supabase schema
frontend/              Streamlit application
investbot/             Backend application package
tests/                 Unit tests
```

## Environment Setup

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Fill in Supabase and Telegram credentials.
5. Run `db/schema.sql` in Supabase SQL editor.

## Run the Backend

```bash
python -m investbot.main
```

This starts:

- Telegram bot polling
- scheduled TW market analysis
- scheduled US market analysis
- interval-based defense monitoring

## Run the Frontend

```bash
streamlit run frontend/streamlit_app.py
```

## Test

```bash
python -m unittest discover -s tests -v
```

## Current Product Notes

- `investbot/data_sources/twse.py` is still a production placeholder and should be connected to real TWSE OpenAPI responses.
- `investbot/data_sources/market_data.py` uses `yfinance` for price history and VIX.
- Core logic is covered by deterministic unit tests so refactors can continue safely.
