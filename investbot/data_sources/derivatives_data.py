from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from io import StringIO
import re
import time

import pandas as pd


@dataclass(slots=True)
class TaifexInstitutionRow:
    trade_date: date
    foreign_net_oi: int
    trust_net_oi: int
    dealer_net_oi: int


@dataclass(slots=True)
class TaifexInstitutionSnapshot:
    latest_date: date
    source: str
    fetched_at: datetime
    rows: list[TaifexInstitutionRow]

    @property
    def latest_row(self) -> TaifexInstitutionRow:
        return self.rows[0]

    @property
    def weekly_change_foreign(self) -> int:
        if len(self.rows) < 2:
            return 0
        return self.rows[0].foreign_net_oi - self.rows[-1].foreign_net_oi

    @property
    def weekly_change_trust(self) -> int:
        if len(self.rows) < 2:
            return 0
        return self.rows[0].trust_net_oi - self.rows[-1].trust_net_oi

    @property
    def weekly_change_dealer(self) -> int:
        if len(self.rows) < 2:
            return 0
        return self.rows[0].dealer_net_oi - self.rows[-1].dealer_net_oi


class TaifexDerivativesClient:
    QUERY_URL = "https://www.taifex.com.tw/cht/3/futContractsDate"
    SOURCE_LABEL = "TAIFEX institutional futures positions"

    def __init__(self) -> None:
        self._snapshot_cache: TaifexInstitutionSnapshot | None = None
        self._snapshot_cache_at: float = 0.0

    def get_tw_tx_institution_snapshot(
        self,
        lookback_rows: int = 5,
        max_age_seconds: int = 1800,
    ) -> TaifexInstitutionSnapshot | None:
        if self._snapshot_cache is not None and (time.monotonic() - self._snapshot_cache_at) < max_age_seconds:
            return self._snapshot_cache

        rows: list[TaifexInstitutionRow] = []
        latest_row = self._fetch_latest_snapshot_page()
        if latest_row is not None:
            rows.append(latest_row)
            probe_date = latest_row.trade_date - timedelta(days=1)
        else:
            probe_date = date.today()
        attempts = 0
        while len(rows) < lookback_rows and attempts < 14:
            parsed = self._fetch_day_snapshot(probe_date)
            if parsed is not None and all(existing.trade_date != parsed.trade_date for existing in rows):
                rows.append(parsed)
            probe_date -= timedelta(days=1)
            attempts += 1

        if not rows:
            return self._snapshot_cache

        snapshot = TaifexInstitutionSnapshot(
            latest_date=rows[0].trade_date,
            source=self.SOURCE_LABEL,
            fetched_at=datetime.now(),
            rows=rows,
        )
        self._snapshot_cache = snapshot
        self._snapshot_cache_at = time.monotonic()
        return snapshot

    def _fetch_latest_snapshot_page(self) -> TaifexInstitutionRow | None:
        import requests

        response = requests.get(
            self.QUERY_URL,
            timeout=12,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        query_date = self._extract_page_date(response.text)
        if query_date is None:
            return None
        return self._parse_day_snapshot(response.text, query_date)

    def _fetch_day_snapshot(self, query_date: date) -> TaifexInstitutionRow | None:
        import requests

        response = requests.get(
            self.QUERY_URL,
            params={
                "queryType": "1",
                "doQuery": "1",
                "queryDate": query_date.strftime("%Y/%m/%d"),
            },
            timeout=12,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        return self._parse_day_snapshot(response.text, query_date)

    @staticmethod
    def _extract_page_date(html: str) -> date | None:
        match = re.search(r"日期\s*(\d{4})/(\d{2})/(\d{2})", html)
        if not match:
            return None
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None

    def _parse_day_snapshot(self, html: str, query_date: date) -> TaifexInstitutionRow | None:
        try:
            tables = pd.read_html(StringIO(html))
        except ValueError:
            return None
        if not tables:
            return None

        for raw in tables:
            frame = self._normalize_table(raw)
            if frame.empty:
                continue
            parsed = self._extract_tx_net_oi(frame, query_date)
            if parsed is not None:
                return parsed
        return None

    @staticmethod
    def _normalize_table(frame: pd.DataFrame) -> pd.DataFrame:
        normalized = frame.copy()
        normalized.columns = [TaifexDerivativesClient._flatten_column_name(col) for col in normalized.columns]

        product_col = next((col for col in normalized.columns if "商品" in col), "")
        identity_col = next((col for col in normalized.columns if "身份別" in col), "")
        if not product_col or not identity_col:
            return pd.DataFrame()

        normalized = normalized.rename(columns={product_col: "product", identity_col: "identity"})
        normalized["product"] = normalized["product"].astype(str).replace({"nan": ""}).ffill()
        normalized["identity"] = normalized["identity"].astype(str).replace({"nan": ""}).ffill()
        return normalized

    @staticmethod
    def _flatten_column_name(column: object) -> str:
        if isinstance(column, tuple):
            parts = [str(part).strip() for part in column if str(part).strip() and "Unnamed" not in str(part)]
            return " ".join(parts)
        return str(column).strip()

    @staticmethod
    def _extract_tx_net_oi(frame: pd.DataFrame, query_date: date) -> TaifexInstitutionRow | None:
        target_rows = frame[frame["product"].astype(str).str.contains("臺股期貨|台股期貨", na=False)].copy()
        if target_rows.empty:
            return None

        net_col = next(
            (
                col
                for col in target_rows.columns
                if "未平倉" in col and "多空淨額" in col and "口數" in col
            ),
            "",
        )
        if not net_col:
            return None

        def _net_for(identity_keyword: str) -> int:
            matched = target_rows[target_rows["identity"].astype(str).str.contains(identity_keyword, na=False)]
            if matched.empty:
                return 0
            raw = str(matched.iloc[0][net_col]).replace(",", "").strip()
            try:
                return int(float(raw))
            except ValueError:
                return 0

        return TaifexInstitutionRow(
            trade_date=query_date,
            foreign_net_oi=_net_for("外資"),
            trust_net_oi=_net_for("投信"),
            dealer_net_oi=_net_for("自營商"),
        )
