<!-- seo-meta
  title: NuoAPI 接入腳手架：Codex / Claude Code / Gemini 設定
  description: 設定常見 AI 用戶端，先用不計費的試跑檢查，再以三態結果核對付費回應是否來自你指定的模型。
-->

# NuoAPI 接入腳手架與防摻水取證工具箱

> **法律與第三方商標免責聲明**
>
> 1. 本專案是獨立開發者維護的技術研究、設定腳手架與診斷工具，不提供、不代售任何 API 服務，與 OpenAI、Anthropic、Google、xAI 等廠商沒有官方關聯、投資、贊助或合作關係。
> 2. 文中產品與公司名稱屬於各自所有者商標，只用於說明協定相容性與設定方式。
> 3. 範例只含佔位符；使用第三方服務前，請自行核對服務條款、隱私政策、價格與可用性。

這個倉庫協助你把 Codex、Claude Code、Gemini CLI 等用戶端接到第三方 AI 閘道，並用可重現的檢查回答一個更窄的問題：**付費收到的回應，是否真的來自服務聲稱的模型？**

[简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md) · 繁體中文

## 先看計畫，不花錢

第一條命令只在本機驗證探針；第二條只列請求計畫，不送出計費模型請求。

```bash
python examples/model_verify.py --selftest
python examples/model_verify.py
```

不加 `--run` 就不會產生付費模型請求。結果只有三態：吻合、不吻合、證據不足。

## Base URL 速查

| 用戶端 | Base URL | 常見錯誤 |
|---|---|---|
| Codex | `https://nuoapi.net/v1`，並設 `wire_api = "responses"` | 沒有關閉 WebSocket |
| Claude Code | `https://nuoapi.net` | 重複加上 `/v1` |
| Gemini CLI | `https://nuoapi.net` | 誤加 `/v1beta` |

本文以 [`nuoapi.net`](https://nuoapi.net) 作為位址夾具。模型 ID、分組、倍率與可用性會變動，請從[模型廣場](https://nuoapi.net/model-plaza)複製目前值，再以控制台即時顯示為準。

## 錯誤短頁

- [Gemini CLI 報 platform is not gemini](docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.zh-Hant.md)
- [Codex 一直 Reconnecting](docs/Codex-一直Reconnecting-2026-10-18.zh-Hant.md)
- [Claude Code 報 404：不要加 /v1](docs/Claude-Code-不要加v1-2026-10-18.zh-Hant.md)

## 如何解讀結果

- **吻合**：觀測證據與聲稱的模型及協定相容。
- **不吻合**：具有判別力的證據與聲稱矛盾。
- **證據不足**：樣本、欄位或取證窗口不足以支持結論。

模型自述、回應速度或單一公開謎題都不能單獨證明真偽。結果應保留取證窗口與實際端點。

## 安全收尾

使用自己的測試 Key 在本機執行，用完即撤銷。輸出的 Key 會遮罩。本專案不使用 UTM、聯盟追蹤或自建追蹤腳本。

本倉庫不提供、不代售 API 服務，也不構成投資或購買建議。
