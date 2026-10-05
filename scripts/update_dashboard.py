from __future__ import annotations
import json, os, time, math, traceback
from pathlib import Path
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ARCHIVE_DIR = DATA_DIR / "archive"
CONFIG = ROOT / "config" / "watchlist.json"
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
    keys = ["forwardEps","forwardPE","marketCap","freeCashflow","totalCash","totalDebt",
            "grossMargins","revenueGrowth","earningsGrowth","operatingMargins"]
    return {k: info.get(k) for k in keys}

def status_from_price(price, fair_low, fair_high, entry, attractive):
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

def baseline_company(row, live_price=None, info=None):
    c = dict(row)
    if live_price is not None:
        c["price"] = round(live_price, 2)
    if info:
        c["market_data"] = info
    c["status"] = status_from_price(c["price"], c["fair_low"], c["fair_high"], c["entry"], c["attractive"])
    return c

def build_market():
    indices, macro = [], []
    data_date = None
    for t, name in MARKET_TICKERS.items():
        try:
            last, ch, d = last_two_closes(t)
            if d and (data_date is None or d > data_date):
                data_date = d
            if t in ["^GSPC","^IXIC","^DJI","^SOX"]:
                indices.append({"symbol":name,"ticker":t,"price":round(last,2) if last is not None else None,
                                "change_pct":round(ch,2) if ch is not None else None})
            else:
                unit = "%" if t == "^TNX" else ("USD" if t == "CL=F" else "")
                macro.append({"name":name,"ticker":t,"value":round(last,3) if last is not None else None,
                              "change_pct":round(ch,2) if ch is not None else None,"unit":unit})
        except Exception as e:
            print("market fetch failed", t, e)
    return indices, macro, data_date

def make_ai_prompt(previous, companies, market):
    compact = []
    for c in companies:
        md = c.get("market_data") or {}
        compact.append({
            "ticker":c["ticker"], "name":c["name"], "sector":c["sector"], "what":c["what"], "why":c["why"],
            "price":c["price"], "previous_fair_low":c["fair_low"], "previous_fair_high":c["fair_high"],
            "previous_entry":c["entry"], "previous_attractive":c["attractive"],
            "valuation_mode":c.get("valuation_mode"), "normalized_eps_anchor":c.get("normalized_eps"),
            "multiple_low_anchor":c.get("multiple_low"), "multiple_high_anchor":c.get("multiple_high"),
            "forwardEps_market":md.get("forwardEps"), "forwardPE_market":md.get("forwardPE"),
            "freeCashflow":md.get("freeCashflow"), "marketCap":md.get("marketCap"),
            "grossMargins":md.get("grossMargins"), "revenueGrowth":md.get("revenueGrowth")
        })
    return f"""
你是極長線價值投資研究員。今天是 {datetime.now(TAIPEI).date().isoformat()}，使用 web search 查詢上一個完整美股交易日與週末/今晨的新資訊。
使用繁體中文。研究重點不是追逐股價，而是判斷企業正常化現金流與 thesis 是否有實質變化。

重要規則：
1. 優先使用公司 Investor Relations、SEC、Reuters、官方經濟資料。不要因為股價上漲/下跌而自動調高/調低合理價。
2. 只有最新財報、正式 guidance、長期正常化 EPS/FCF、產業結構、競爭力或資本成本有實質變化，才調整合理價。
3. MU、SNDK、LRCX、ASX 等週期股不可直接拿高峰 EPS 估值，必須考慮正常化獲利。
4. 對高成長股 ALAB、AMD、ANET、VRT、MRVL，要把成長持續性和估值壓縮風險納入。
5. 若無足夠證據重估，沿用上一版合理價與買點。
6. 「開始布局價」應保留約 5~15% 安全邊際；「很有吸引力價」通常應有約 15~30% 安全邊際，但依公司品質/週期調整。
7. 每家公司必須列 1~4 個可點擊來源 URL；市場摘要也列來源。
8. 不要杜撰數字；無法可靠驗證時，沿用 anchor 並明確說明。
9. 股票價格資料以下方本地市場抓取值為準，不要用搜尋到的不同時間價格覆蓋。

市場資料：
{json.dumps(market, ensure_ascii=False)}

上一版與本地市場資料：
{json.dumps(compact, ensure_ascii=False)}

請輸出 JSON，包含：
- market_summary：200~450 字，解釋主要指數、經濟數據、Fed 預期、美債、美元、油價、主要新聞與輪動。
- fed：Fed 利率預期白話摘要。
- drivers：3~7 個短句。
- market_sources：來源陣列，每項 title/url。
- companies：每個 ticker 一筆：
  ticker, fair_low, fair_high, entry, attractive, method, risk, thesis_change(boolean),
  thesis_change_reason, valuation_changed(boolean), valuation_change_reason, sources(title/url)。
- 若沒有實質 thesis change，thesis_change 必須 false。
"""

def call_openai(prompt):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    from openai import OpenAI
    client = OpenAI(api_key=key)
    model = os.getenv("OPENAI_MODEL", "gpt-5.5")
    # JSON mode is deliberately used with explicit instructions because web search + rigid large schemas
    # can be brittle across SDK versions. We validate before applying.
    resp = client.responses.create(
        model=model,
        tools=[{"type":"web_search","search_context_size":"medium"}],
        tool_choice="auto",
        include=["web_search_call.action.sources"],
        input=prompt + "\n只輸出有效 JSON，不要 Markdown。",
        text={"format":{"type":"json_object"}},
    )
    text = resp.output_text.strip()
    data = json.loads(text)

    # Fallback source list from the API's web-search tool output.
    try:
        dumped = resp.model_dump()
        urls = []
        for item in dumped.get("output", []):
            if item.get("type") != "web_search_call":
                continue
            action = item.get("action") or {}
            for src in action.get("sources") or []:
                url = src.get("url")
                if url and url not in urls:
                    urls.append(url)
        if not data.get("market_sources") and urls:
            data["market_sources"] = [{"title": "Web source", "url": u} for u in urls[:12]]
    except Exception:
        pass
    return data

def apply_ai(companies, ai):
    by_ticker = {x.get("ticker"): x for x in (ai or {}).get("companies", []) if x.get("ticker")}
    fair_changes, thesis_changes = [], []
    for c in companies:
        a = by_ticker.get(c["ticker"])
        if not a:
            continue
        old_mid = (c["fair_low"] + c["fair_high"]) / 2
        try:
            for k in ["fair_low","fair_high","entry","attractive"]:
                if a.get(k) is not None:
                    c[k] = round(float(a[k]), 2)
            if a.get("method"): c["method"] = a["method"]
            if a.get("risk"): c["risk"] = a["risk"]
            if a.get("sources"): c["sources"] = a["sources"]
            c["thesis_change"] = bool(a.get("thesis_change", False))
            c["thesis_change_reason"] = a.get("thesis_change_reason","")
            c["status"] = status_from_price(c["price"], c["fair_low"], c["fair_high"], c["entry"], c["attractive"])
            new_mid = (c["fair_low"] + c["fair_high"]) / 2
            delta = ((new_mid/old_mid)-1)*100 if old_mid else 0
            if bool(a.get("valuation_changed")) or abs(delta) >= 2.0:
                fair_changes.append({"ticker":c["ticker"],"change_pct":round(delta,1),
                                     "text":a.get("valuation_change_reason") or f"合理價中值調整 {delta:+.1f}%"})
            if c["thesis_change"]:
                thesis_changes.append({"ticker":c["ticker"],"text":c["thesis_change_reason"] or "偵測到實質 thesis change"})
        except Exception as e:
            print("AI row apply failed", c["ticker"], e)
    return fair_changes, thesis_changes

def main():
    DATA_DIR.mkdir(exist_ok=True); ARCHIVE_DIR.mkdir(exist_ok=True)
    cfg = load_json(CONFIG, [])
    previous = load_json(DATA_DIR/"current.json", {})
    indices, macro, data_date = build_market()

    companies=[]
    for row in cfg:
        try:
            p, _, d = last_two_closes(row["ticker"])
            info = safe_info(row["ticker"])
            companies.append(baseline_company(row, p, info))
            if d and (data_date is None or d > data_date): data_date=d
        except Exception as e:
            print("company fetch failed", row["ticker"], e)
            companies.append(baseline_company(row))

    market = {"indices":indices,"macro":macro}
    ai = None
    mode = "market_only"
    try:
        ai = call_openai(make_ai_prompt(previous, companies, market))
        if ai: mode="ai_web_search"
    except Exception as e:
        print("OpenAI analysis failed; using prices + previous valuation anchors.")
        traceback.print_exc()

    fair_changes=[]; thesis_changes=[]
    if ai:
        fair_changes, thesis_changes = apply_ai(companies, ai)

    # Capital assumptions are editable in data/current.json; preserve user's settings.
    prev_cap = previous.get("capital", {})
    shv_shares = prev_cap.get("shv_shares", 70)
    shv_ref = prev_cap.get("shv_reference_price", 110.09)
    # Try fresh SHV price.
    try:
        shv_price,_,_=last_two_closes("SHV")
        if shv_price: shv_ref=round(shv_price,2)
    except Exception: pass

    now = datetime.now(TAIPEI)
    out = {
        "updated_at": now.isoformat(timespec="seconds"),
        "data_date": data_date or now.date().isoformat(),
        "mode": mode,
        "market": {
            "summary": (ai or {}).get("market_summary","市場數字已更新；AI 晨報尚未啟用或本次搜尋失敗。"),
            "indices": indices, "macro": macro,
            "fed": (ai or {}).get("fed","需要 OPENAI_API_KEY 才會自動研究 Fed 利率預期。"),
            "drivers": (ai or {}).get("drivers",[]),
            "sources": (ai or {}).get("market_sources",[])
        },
        "capital": {
            "shv_shares": shv_shares,
            "shv_reference_price": shv_ref,
            "estimated_cash": round(shv_shares*shv_ref,2)
        },
        "companies": companies,
        "thesis_changes": thesis_changes,
        "fair_value_changes": fair_changes,
        "notes":"Daily automated build. Fair value should move only on fundamental evidence, not ordinary price action."
    }
    (DATA_DIR/"current.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")

    datekey=now.date().isoformat()
    (ARCHIVE_DIR/f"{datekey}.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    history=load_json(DATA_DIR/"history.json",[])
    snap={"date":datekey,"data_date":out["data_date"],"companies":[
        {"ticker":c["ticker"],"price":c["price"],"fair_low":c["fair_low"],"fair_high":c["fair_high"],
         "entry":c["entry"],"attractive":c["attractive"],"status":c["status"]} for c in companies]}
    history=[x for x in history if x.get("date")!=datekey]
    history.append(snap); history=history[-730:]
    (DATA_DIR/"history.json").write_text(json.dumps(history,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Updated", out["updated_at"], "mode=",mode, "companies=",len(companies))

if __name__ == "__main__":
    main()
