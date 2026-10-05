# AI Capital Intelligence — Premium v2.5 FREE

Premium v2.4 的視覺與互動保留，資料架構改成 **免費自動行情 + 手動 AI 研究**。

## 這個版本不會呼叫 OpenAI API

`daily-update.yml` 沒有 `OPENAI_API_KEY`、沒有 OpenAI SDK、沒有 Responses API、沒有 web_search。

因此網站每天自行運作時，不會產生 OpenAI API 使用費。

## 每日免費自動更新
- Watchlist 股價
- S&P 500 / Nasdaq / Dow / SOX
- 10Y / DXY / WTI / VIX
- SHV 參考價格
- 買點距離與估值狀態
- 股價 vs 合理價歷史資料

資料來源由 `yfinance` 取得，屬非官方 Yahoo Finance wrapper，適合個人研究，不是交易所級即時行情。

## AI 研究
AI 晨報、Fed 解讀、合理價調整、Thesis Change 都放在：

`data/research.json`

請參考 `MANUAL_AI_SYNC.md`。

## 成本
- OpenAI API：**$0（本專案完全不呼叫）**
- GitHub Pages：公開 repository 一般可免費使用
- GitHub Actions：公開 repository 的標準 hosted runner 一般可免費使用；若改成 private repository，請依 GitHub 帳戶方案注意 Actions minutes / storage 額度

## 安全
這個版本不需要 GitHub Secret `OPENAI_API_KEY`。
如果你不打算做其他 API 專案，可以從 GitHub Repository Secrets 移除該 Secret。
