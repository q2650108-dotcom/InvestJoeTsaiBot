from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ThemeCard:
    title: str
    focus: str
    tags: tuple[str, ...]
    symbols: tuple[dict[str, str], ...]


class MarketPanoramaService:
    def get_config(self, market_key: str) -> dict[str, Any]:
        normalized = "us" if str(market_key).lower() == "us" else "tw"
        return {
            "market_key": normalized,
            "ticker_tape": self._ticker_tape(normalized),
            "market_overview": self._market_overview(normalized),
            "heatmap": self._heatmap(normalized),
            "symbol_overview": self._symbol_overview(normalized),
            "theme_cards": [self._serialize_card(card) for card in self._theme_cards(normalized)],
        }

    def _ticker_tape(self, market_key: str) -> dict[str, Any]:
        if market_key == "tw":
            symbols = [
                {"proName": "TVC:TWII", "title": "加權指數"},
                {"proName": "TWSE:0050", "title": "台灣 50"},
                {"proName": "TWSE:2330", "title": "台積電"},
                {"proName": "TWSE:2454", "title": "聯發科"},
                {"proName": "TVC:US10Y", "title": "美債 10Y"},
                {"proName": "OANDA:USDTWD", "title": "美元 / 台幣"},
                {"proName": "TVC:VIX", "title": "VIX"},
            ]
        else:
            symbols = [
                {"proName": "SP:SPX", "title": "S&P 500"},
                {"proName": "NASDAQ:NDX", "title": "Nasdaq 100"},
                {"proName": "DJ:DJI", "title": "Dow"},
                {"proName": "NASDAQ:NVDA", "title": "NVIDIA"},
                {"proName": "NASDAQ:MSFT", "title": "Microsoft"},
                {"proName": "AMEX:SMH", "title": "半導體 ETF"},
                {"proName": "TVC:VIX", "title": "VIX"},
            ]
        return {
            "symbols": symbols,
            "showSymbolLogo": True,
            "isTransparent": True,
            "displayMode": "adaptive",
            "colorTheme": "light",
            "locale": "zh_TW",
        }

    def _market_overview(self, market_key: str) -> dict[str, Any]:
        if market_key == "tw":
            tabs = [
                {
                    "title": "台股市場",
                    "symbols": [
                        {"s": "TVC:TWII", "d": "加權指數"},
                        {"s": "TWSE:0050", "d": "台灣 50"},
                        {"s": "TWSE:2330", "d": "台積電"},
                        {"s": "TWSE:2317", "d": "鴻海"},
                        {"s": "TWSE:2454", "d": "聯發科"},
                        {"s": "TWSE:2308", "d": "台達電"},
                    ],
                },
                {
                    "title": "宏觀變數",
                    "symbols": [
                        {"s": "OANDA:USDTWD", "d": "美元 / 台幣"},
                        {"s": "TVC:VIX", "d": "VIX"},
                        {"s": "TVC:US10Y", "d": "美債 10Y"},
                        {"s": "COMEX:GC1!", "d": "黃金"},
                        {"s": "NYMEX:CL1!", "d": "原油"},
                    ],
                },
            ]
        else:
            tabs = [
                {
                    "title": "美股市場",
                    "symbols": [
                        {"s": "SP:SPX", "d": "S&P 500"},
                        {"s": "NASDAQ:NDX", "d": "Nasdaq 100"},
                        {"s": "DJ:DJI", "d": "Dow"},
                        {"s": "NASDAQ:NVDA", "d": "NVIDIA"},
                        {"s": "NASDAQ:MSFT", "d": "Microsoft"},
                        {"s": "NASDAQ:AAPL", "d": "Apple"},
                    ],
                },
                {
                    "title": "風格與ETF",
                    "symbols": [
                        {"s": "AMEX:SMH", "d": "半導體 ETF"},
                        {"s": "AMEX:QQQ", "d": "QQQ"},
                        {"s": "AMEX:SPY", "d": "SPY"},
                        {"s": "TVC:VIX", "d": "VIX"},
                        {"s": "COMEX:GC1!", "d": "黃金"},
                    ],
                },
            ]
        return {
            "colorTheme": "light",
            "dateRange": "1D",
            "showChart": True,
            "locale": "zh_TW",
            "isTransparent": True,
            "showSymbolLogo": True,
            "showFloatingTooltip": True,
            "width": "100%",
            "height": "520",
            "tabs": tabs,
        }

    def _heatmap(self, market_key: str) -> dict[str, Any]:
        return {
            "dataSource": "TWSE" if market_key == "tw" else "SPX500",
            "blockSize": "market_cap_basic",
            "blockColor": "change",
            "grouping": "sector",
            "locale": "zh_TW",
            "symbolUrl": "",
            "colorTheme": "light",
            "hasTopBar": False,
            "isDataSetEnabled": True,
            "isZoomEnabled": True,
            "isMonoSize": False,
            "width": "100%",
            "height": "560",
        }

    def _symbol_overview(self, market_key: str) -> dict[str, Any]:
        if market_key == "tw":
            symbols = [
                ["台指期", "TAIFEX:TXF1!|1D"],
                ["台積電", "TWSE:2330|1D"],
                ["0050", "TWSE:0050|1D"],
                ["美元 / 台幣", "OANDA:USDTWD|1D"],
            ]
        else:
            symbols = [
                ["S&P 500", "SP:SPX|1D"],
                ["Nasdaq 100", "NASDAQ:NDX|1D"],
                ["NVIDIA", "NASDAQ:NVDA|1D"],
                ["SMH", "AMEX:SMH|1D"],
            ]
        return {
            "lineWidth": 2,
            "lineType": 0,
            "chartType": "area",
            "fontColor": "rgb(93, 104, 120)",
            "gridLineColor": "rgba(216, 224, 220, 0.55)",
            "backgroundColor": "#ffffff",
            "widgetFontColor": "#111827",
            "upColor": "#087f5b",
            "downColor": "#c2410c",
            "colorTheme": "light",
            "isTransparent": True,
            "locale": "zh_TW",
            "chartOnly": False,
            "scalePosition": "right",
            "scaleMode": "Normal",
            "changeMode": "price-and-percent",
            "symbols": symbols,
            "dateRanges": ["1d|1", "5d|15", "1m|30", "3m|60", "12m|1D", "60m|1W", "all|1M"],
            "fontSize": "10",
            "autosize": True,
            "width": "100%",
            "height": "420",
        }

    def _theme_cards(self, market_key: str) -> tuple[ThemeCard, ...]:
        if market_key == "tw":
            return (
                ThemeCard(
                    title="AI 供應鏈",
                    focus="觀察台積電、聯發科、鴻海等 AI 與伺服器供應鏈是否維持強勢，並留意資金是否擴散到設備、散熱與網通。",
                    tags=("AI", "半導體", "伺服器"),
                    symbols=(
                        {"ticker": "2330.TW", "label": "台積電"},
                        {"ticker": "2454.TW", "label": "聯發科"},
                        {"ticker": "2317.TW", "label": "鴻海"},
                        {"ticker": "2382.TW", "label": "廣達"},
                    ),
                ),
                ThemeCard(
                    title="金融 / 高股息",
                    focus="觀察金融股與高股息 ETF 是否持續吸引資金，特別留意壽險、金控與高股息 ETF 的輪動。",
                    tags=("金融", "高股息 ETF", "防禦"),
                    symbols=(
                        {"ticker": "2881.TW", "label": "富邦金"},
                        {"ticker": "2882.TW", "label": "國泰金"},
                        {"ticker": "2891.TW", "label": "中信金"},
                        {"ticker": "0056.TW", "label": "元大高股息"},
                    ),
                ),
            )
        return (
            ThemeCard(
                title="AI 基礎建設",
                focus="觀察 AI 算力、網通與半導體供應鏈是否延續趨勢，留意 NVIDIA、Broadcom、AMD 與半導體 ETF。",
                tags=("AI", "Semis", "Infra"),
                symbols=(
                    {"ticker": "NVDA", "label": "NVIDIA"},
                    {"ticker": "AVGO", "label": "Broadcom"},
                    {"ticker": "AMD", "label": "AMD"},
                    {"ticker": "SMH", "label": "SMH ETF"},
                ),
            ),
            ThemeCard(
                title="雲端與平台",
                focus="觀察雲端平台與大型軟體是否維持資金集中，留意 Microsoft、Amazon、Meta 與 Alphabet。",
                tags=("Cloud", "Platform", "Software"),
                symbols=(
                    {"ticker": "MSFT", "label": "Microsoft"},
                    {"ticker": "AMZN", "label": "Amazon"},
                    {"ticker": "META", "label": "Meta"},
                    {"ticker": "GOOGL", "label": "Alphabet"},
                ),
            ),
        )

    def _serialize_card(self, card: ThemeCard) -> dict[str, Any]:
        return {
            "title": card.title,
            "focus": card.focus,
            "tags": list(card.tags),
            "symbols": [dict(item) for item in card.symbols],
        }
