# Smart Swing Agent

依據 `gemini-code-1777685860630.md` 規格書建立的 Python 後端 + Supabase Schema + Streamlit 前端骨架。

## 啟動方式

1. 建立虛擬環境並安裝套件
2. 複製 `.env.example` 成 `.env`
3. 先到 Supabase 執行 `db/schema.sql`
4. 啟動後端排程與 Telegram Bot：
   `python -m investbot.main`
5. 啟動前端：
   `streamlit run frontend/streamlit_app.py`
