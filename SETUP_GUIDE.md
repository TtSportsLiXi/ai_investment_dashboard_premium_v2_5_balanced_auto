# AI Investment Dashboard — 回家後照這份做

這個版本已經包含：

- GitHub Pages 靜態網站
- 每天 **08:00 Asia/Taipei** 自動執行
- 自動更新股價 / 指數 / 10Y / DXY / WTI / VIX
- OpenAI Responses API + Web Search：自動研究「昨晚為什麼漲跌」、Fed 預期、公司最新財報/指引/Thesis
- 自動維護合理價、開始布局價、很有吸引力價
- `data/archive/YYYY-MM-DD.json` 每日快照
- `data/history.json` 歷史紀錄
- GitHub Pages 自動部署

---

## 1. 建立 GitHub Repository

GitHub → New repository

建議名稱：

`ai-investment-dashboard`

選 **Public** 或 **Private** 都可以，但 GitHub Pages 的可用範圍會依你的 GitHub 方案而異。

建立後，把這個 ZIP 解壓縮，**整包內容上傳到 repository 根目錄**。

最重要的是 `.github/workflows/` 也要一起上傳。

---

## 2. 設定 OpenAI API Key

> ChatGPT Plus 與 OpenAI API 是分開的服務與計費。  
> 不要把 API Key 寫在程式碼、README 或 data.json 裡。

Repository：

**Settings → Secrets and variables → Actions → New repository secret**

名稱：

`OPENAI_API_KEY`

Value：

貼上你的 OpenAI API Key。

預設模型在 workflow 是 `gpt-5.5`。  
如果之後要改，可到：

**Settings → Secrets and variables → Actions → Variables**

新增：

`OPENAI_MODEL`

例如設成你想使用的可用模型。

---

## 3. 啟用 GitHub Pages

Repository：

**Settings → Pages**

Build and deployment 的 Source 選：

**GitHub Actions**

存檔即可。

第一次 push 後，`Deploy GitHub Pages` workflow 會發布網站。

網站網址通常是：

`https://你的GitHub帳號.github.io/ai-investment-dashboard/`

---

## 4. 讓 Daily Update 可以寫回 repository

Repository：

**Settings → Actions → General → Workflow permissions**

選：

**Read and write permissions**

Save。

`Daily investment dashboard update` 才能把更新後的 `data/*.json` commit 回 repository。

---

## 5. 第一次先手動測試

Repository → **Actions**

選：

`Daily investment dashboard update`

按：

**Run workflow**

成功後：

- `data/current.json` 會變成最新資料
- `data/archive/日期.json` 會產生
- `data/history.json` 會新增一筆
- GitHub Pages 會因 push 自動重新部署

---

## 6. 之後每天不用手動更新

GitHub Actions 排程：

**每天 08:00，Asia/Taipei**

會自動：

1. 抓上一交易日股價與市場數據
2. 使用 OpenAI Web Search 查最新總經與公司資料
3. 重算 / 檢查合理價
4. 更新 `data/current.json`
5. 保存歷史快照
6. commit / push
7. GitHub Pages 自動更新

---

## 估值設計原則

這版故意不做「股價漲 → 合理價跟著漲」。

AI prompt 有明確規則：

- 只有最新財報 / guidance / FCF / 正常化 EPS / 產業結構 / Thesis 有實質變化才重估
- MU、SNDK、LRCX、ASX 等週期股不可直接用高峰 EPS
- 高成長股要考慮估值壓縮
- 無足夠證據時沿用舊合理價
- 每次研究要盡量使用公司 IR / SEC / Reuters / 官方經濟資料

---

## 修改 SHV 股數

打開：

`data/current.json`

找到：

```json
"capital": {
  "shv_shares": 70
}
```

改成你當下實際股數即可。

每日程式會保留這個數字，並自動更新 SHV 參考價及可部署金額。

---

## 本機預覽

因為網站會 `fetch("data/current.json")`，直接雙擊 `index.html` 某些瀏覽器會阻擋。

在專案資料夾開 PowerShell：

```powershell
python -m http.server 8000
```

再開：

`http://localhost:8000`

上傳 GitHub Pages 後不需要這一步。

---

## 注意

1. `yfinance` 是非官方行情來源，適合作為個人研究 Dashboard 的每日收盤資料，但不是交易所級即時行情。
2. OpenAI Web Search 會產生 API 費用；使用量與模型價格取決於你的 API 帳戶與當時定價。
3. GitHub Actions 排程可能有少量延遲，不保證精準在 08:00:00 開始。
4. 合理價仍是研究模型，不是保證報酬或買賣指令。
