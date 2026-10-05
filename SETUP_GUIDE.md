# Premium v2.5 FREE — GitHub 上線步驟

## 1. 上傳專案
把本 ZIP 解壓後的「內容」上傳到 GitHub repository 根目錄。

根目錄應直接看到：
- `index.html`
- `assets/`
- `data/`
- `config/`
- `scripts/`
- `.github/`
- `requirements.txt`

## 2. 不需要 OpenAI API Key
這一版沒有任何 OpenAI API 呼叫。

你之前建立的：
`OPENAI_API_KEY`

可以從：
Settings → Secrets and variables → Actions → Secrets

刪除，避免之後混淆。

如果你也完全不打算使用 OpenAI API，可以另外到 OpenAI API 平台撤銷那把 API Key。

## 3. GitHub Actions 權限
Repository → Settings → Actions → General

找到：
Workflow permissions

選：
`Read and write permissions`

Save。

原因：每天更新後需要把 `data/current.json`、`data/history.json` 和 archive commit 回 repository。

## 4. GitHub Pages
Repository → Settings → Pages

Build and deployment → Source：

`GitHub Actions`

## 5. 第一次手動測試
Repository → Actions → `Daily FREE market data update`

按：
Run workflow

成功後應看到綠色勾勾，並且 repository 裡的 `data/current.json` 更新。

## 6. 網站部署
`Deploy GitHub Pages` workflow 會在 push 後執行。

成功後，到：
Settings → Pages

即可看到公開網址。

## 7. 之後
每天 Asia/Taipei 08:00：
- 免費更新行情
- 不呼叫 OpenAI API
- 不自動修改合理價研究

要更新 AI 晨報 / 合理價時，請看：
`MANUAL_AI_SYNC.md`
