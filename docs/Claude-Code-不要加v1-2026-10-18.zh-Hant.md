<!-- seo-meta
  title: Claude Code 報 404：Base URL 不要加 /v1
  description: Claude Code 會自行拼接 /v1/messages。ANTHROPIC_BASE_URL 要填根位址，憑證使用 ANTHROPIC_AUTH_TOKEN，改完後另開終端。
-->

# Claude Code 報 404：不要加 /v1

> **法律與第三方商標免責聲明**
>
> 1. 本文是獨立開發者維護的設定說明，與 Anthropic 或其他廠商沒有官方關聯。名稱只用於說明協定相容性。
> 2. 本倉庫不提供、不代售任何 API 服務。
> 3. 使用第三方服務前，請自行核對條款、隱私政策、價格與可用性。

位址夾具是 [`nuoapi.net`](https://nuoapi.net)。目前模型 ID 請從相同分組複製，並在[模型廣場](https://nuoapi.net/model-plaza)與控制台確認。

## 症狀

請求回傳純文字 `404 page not found`，而不是 `401`。常見原因是 `ANTHROPIC_BASE_URL` 多加了 `/v1`；Claude Code 又會再接 `/v1/messages`，路徑因此對不上。

變數名稱也要正確：使用 `ANTHROPIC_AUTH_TOKEN`，不是 `ANTHROPIC_API_KEY`。

## 單一設定

```text
ANTHROPIC_BASE_URL=https://nuoapi.net
ANTHROPIC_AUTH_TOKEN=YOUR_NUOAPI_API_KEY
```

目前 PowerShell 終端：

```powershell
$env:ANTHROPIC_BASE_URL = "https://nuoapi.net"
$env:ANTHROPIC_AUTH_TOKEN = "YOUR_NUOAPI_API_KEY"
```

需要永久生效時，使用系統環境變數介面。已開啟的程式不會自動讀到新值。

## 驗證

另開終端啟動 Claude Code，送出一次固定短句，到控制台核對模型與時間。若仍使用帶 `/v1` 的舊值，通常是前一個程序沒有完全結束。

其他系統的設定見[第三方工具教學](接入第三方工具教程-2026-09-26.md#51-claude-code-与-claude-类工具)。
