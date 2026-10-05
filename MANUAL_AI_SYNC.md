# 手動同步 AI 分析（0 OpenAI API 費用）

這個版本的網站每天會自動更新行情，但 **不會呼叫 OpenAI API**。

## 每天自動做的事
- 追蹤股票最新收盤價
- S&P 500 / Nasdaq / Dow / SOX
- US 10Y / DXY / WTI / VIX
- SHV 參考價格與可部署資金
- 自動重算「距開始布局價」
- 自動更新估值狀態
- 累積 `data/history.json`
- 產生每日 archive

## 不會自動做的事
- AI 新聞研究
- 昨晚漲跌原因分析
- Fed 文字解讀
- 合理價重新估值
- Thesis change 判斷

這些內容放在：

`data/research.json`

GitHub Action **不會修改這個檔案**。

## 之後要更新 AI 分析時

最簡單的流程：

1. 把目前 GitHub 裡的 `data/research.json` 下載或直接丟給 ChatGPT。
2. 說：「幫我更新網站 AI 晨報與合理價研究，維持 research.json 格式。」
3. ChatGPT 研究完後產生新的 `research.json`。
4. 到 GitHub 打開 `data/research.json`，上傳／替換成新版。
5. GitHub Pages 會重新部署。
6. 下一次每日行情更新時，新的研究內容仍會保留。

這樣 OpenAI 的分析是在你的 ChatGPT 對話裡完成，而不是 GitHub 在背景呼叫付費 API。
