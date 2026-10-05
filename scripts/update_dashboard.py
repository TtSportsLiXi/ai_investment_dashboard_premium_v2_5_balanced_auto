from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ARCHIVE_DIR = DATA_DIR / "archive"
CONFIG = ROOT / "config" / "watchlist.json"
RESEARCH = DATA_DIR / "research.json"
TAIPEI = ZoneInfo("Asia/Taipei")

MARKET_TICKERS = {
    "^GSPC": "S&P 500",
    "^IXIC": "Nasdaq",
    "^DJI": "Dow",
    "^SOX": "SOX",
    "^TNX": "US 10Y",
    "DX-Y.NYB": "DXY",
    "CL=F": "WTI",
    "^VIX": "VIX",
}

def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default

def last_two_closes(ticker):
    hist = yf.Ticker(ticker).history(period="7d", auto_adjust=False)
    if hist.empty:
        return None, None, None
    closes = hist["Close"].dropna()
    if len(closes) < 1:
        return None, None, None
    last = float(closes.iloc[-1])
    prev = float(closes.iloc[-2]) if len(closes) >= 2 else None
    change = ((last / prev) - 1) * 100 if prev else None
    date = closes.index[-1].date().isoformat()
    return last, change, date

def safe_info(ticker):
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception:
        info = {}
    keys = [
        "forwardEps", "forwardPE", "marketCap", "freeCashflow",
        "totalCash", "totalDebt", "grossMargins", "revenueGrowth",
        "earningsGrowth", "operatingMargins"
    ]
    return {k: info.get(k) for k in keys}

def status_from_price(price, fair_low, fair_high, entry, attractive):
    if price is None:
        return "資料待更新"
    if price <= attractive:
        return "很有吸引力"
    if price <= entry:
        return "可布局"
    if price <= fair_low * 1.03:
        return "接近買點"
    if fair_low <= price <= fair_high:
        return "合理"
    if price <= fair_high * 1.10:
        return "合理偏上"
    if price <= fair_high * 1.25:
        return "偏貴"
    return "明顯偏貴"

def research_company_map(research):
    rows = research.get("companies", {})
    if isinstance(rows, list):
        return {x.get("ticker"): x for x in rows if x.get("ticker")}
    return rows if isinstance(rows, dict) else {}

def merge_company(base, previous_row, research_row, live_price, info):
    # Priority:
    # manual research.json > previous current.json > config/watchlist.json
    c = dict(base)
    if previous_row:
        for k in [
            "fair_low", "fair_high", "entry", "attractive", "method", "risk",
            "why", "valuation_mode", "normalized_eps", "multiple_low",
            "multiple_high", "sources", "thesis_change", "thesis_change_reason"
        ]:
            if previous_row.get(k) is not None:
                c[k] = previous_row[k]

    if research_row:
        for k in [
            "fair_low", "fair_high", "entry", "attractive", "method", "risk",
            "why", "valuation_mode", "normalized_eps", "multiple_low",
            "multiple_high", "sources", "thesis_change", "thesis_change_reason"
        ]:
            if research_row.get(k) is not None:
                c[k] = research_row[k]

    if live_price is not None:
        c["price"] = round(live_price, 2)

    c["market_data"] = info or {}
    c["status"] = status_from_price(
        c.get("price"),
        float(c["fair_low"]),
        float(c["fair_high"]),
        float(c["entry"]),
        float(c["attractive"]),
    )
    return c

def build_market():
    indices, macro = [], []
    data_date = None

    for ticker, name in MARKET_TICKERS.items():
        try:
            last, change, date = last_two_closes(ticker)
            if date and (data_date is None or date > data_date):
                data_date = date

            if ticker in ["^GSPC", "^IXIC", "^DJI", "^SOX"]:
                indices.append({
                    "symbol": name,
                    "ticker": ticker,
                    "price": round(last, 2) if last is not None else None,
                    "change_pct": round(change, 2) if change is not None else None,
                })
            else:
                unit = "%" if ticker == "^TNX" else ("USD" if ticker == "CL=F" else "")
                macro.append({
                    "name": name,
                    "ticker": ticker,
                    "value": round(last, 3) if last is not None else None,
                    "change_pct": round(change, 2) if change is not None else None,
                    "unit": unit,
                })
        except Exception as exc:
            print("market fetch failed:", ticker, exc)

    return indices, macro, data_date

def main():
    DATA_DIR.mkdir(exist_ok=True)
    ARCHIVE_DIR.mkdir(exist_ok=True)

    cfg = load_json(CONFIG, [])
    previous = load_json(DATA_DIR / "current.json", {})
    research = load_json(RESEARCH, {})

    prev_by_ticker = {
        x.get("ticker"): x
        for x in previous.get("companies", [])
        if x.get("ticker")
    }
    manual_by_ticker = research_company_map(research)

    indices, macro, data_date = build_market()

    companies = []
    for row in cfg:
        ticker = row["ticker"]
        live_price = None
        info = {}
        try:
            live_price, _, date = last_two_closes(ticker)
            info = safe_info(ticker)
            if date and (data_date is None or date > data_date):
                data_date = date
        except Exception as exc:
            print("company fetch failed:", ticker, exc)

        companies.append(
            merge_company(
                row,
                prev_by_ticker.get(ticker, {}),
                manual_by_ticker.get(ticker, {}),
                live_price,
                info,
            )
        )

    # Preserve the user's SHV share count; update SHV market price for free.
    prev_cap = previous.get("capital", {})
    shv_shares = research.get("capital", {}).get(
        "shv_shares",
        prev_cap.get("shv_shares", 70)
    )
    shv_ref = prev_cap.get("shv_reference_price", 110.09)
    try:
        shv_price, _, _ = last_two_closes("SHV")
        if shv_price is not None:
            shv_ref = round(shv_price, 2)
    except Exception as exc:
        print("SHV fetch failed:", exc)

    manual_market = research.get("market", {})
    now = datetime.now(TAIPEI)

    out = {
        "updated_at": now.isoformat(timespec="seconds"),
        "data_date": data_date or now.date().isoformat(),
        "mode": "free_data_manual_ai",
        "market": {
            "summary": manual_market.get(
                "summary",
                "市場行情會每日免費自動更新；AI 晨報目前採手動同步，不會呼叫付費 OpenAI API。"
            ),
            "indices": indices,
            "macro": macro,
            "fed": manual_market.get(
                "fed",
                "Fed 分析尚未同步。之後可由 ChatGPT 產生分析後更新 research.json。"
            ),
            "drivers": manual_market.get("drivers", []),
            "sources": manual_market.get("sources", []),
        },
        "capital": {
            "shv_shares": shv_shares,
            "shv_reference_price": shv_ref,
            "estimated_cash": round(float(shv_shares) * float(shv_ref), 2),
        },
        "companies": companies,
        "thesis_changes": research.get("thesis_changes", []),
        "fair_value_changes": research.get("fair_value_changes", []),
        "research_updated_at": research.get("updated_at"),
        "notes": (
            "FREE MODE: prices and market data update automatically via yfinance. "
            "AI research / fair-value revisions are read only from data/research.json. "
            "This workflow makes no OpenAI API calls."
        ),
    }

    (DATA_DIR / "current.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    datekey = now.date().isoformat()
    (ARCHIVE_DIR / f"{datekey}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    history = load_json(DATA_DIR / "history.json", [])
    snap = {
        "date": datekey,
        "data_date": out["data_date"],
        "companies": [
            {
                "ticker": c["ticker"],
                "price": c["price"],
                "fair_low": c["fair_low"],
                "fair_high": c["fair_high"],
                "entry": c["entry"],
                "attractive": c["attractive"],
                "status": c["status"],
            }
            for c in companies
        ],
    }
    history = [x for x in history if x.get("date") != datekey]
    history.append(snap)
    history = history[-730:]

    (DATA_DIR / "history.json").write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        "Updated",
        out["updated_at"],
        "mode=FREE_DATA_MANUAL_AI",
        "companies=",
        len(companies),
    )

if __name__ == "__main__":
    main()
