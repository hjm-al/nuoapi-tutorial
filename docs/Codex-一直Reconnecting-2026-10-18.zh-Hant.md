<!-- seo-meta
  title: Codex 一直 Reconnecting：關閉 supports_websockets
  description: Codex 反覆重連或日誌出現 wss:// 的 /v1/responses 時，改用 HTTP Responses，將 supports_websockets 設為 false，再完全重啟。
-->

# Codex 一直 Reconnecting：關閉 WebSocket

> **法律與第三方商標免責聲明**
>
> 1. 本文是獨立開發者維護的設定說明，與 OpenAI 或其他廠商沒有官方關聯。名稱只用於說明協定相容性。
> 2. 本倉庫不提供、不代售任何 API 服務。
> 3. 使用第三方服務前，請自行核對條款、隱私政策、價格與可用性。

位址夾具是 [`nuoapi.net`](https://nuoapi.net)。目前模型 ID 請從相同分組複製，並在[模型廣場](https://nuoapi.net/model-plaza)與控制台確認。

## 症狀

Codex 一直顯示 `Reconnecting`，或日誌出現：

- `wss://nuoapi.net/v1/responses`
- `WebSocket connection ... failed`
- 反覆出現 `connecting to wss://...`

客戶端正在嘗試 WebSocket，但目前應走 HTTP Responses。只加代理環境變數不會關閉這個重試。

## 單一設定

macOS / Linux 是 `~/.codex/config.toml`，Windows 是 `%USERPROFILE%\.codex\config.toml`：

```toml
model_provider = "nuoapi"
model = "MODEL_NAME_FROM_MODEL_PLAZA"

[model_providers.nuoapi]
name = "nuoapi"
base_url = "https://nuoapi.net/v1"
wire_api = "responses"
requires_openai_auth = true
supports_websockets = false
```

Key 不要寫進 TOML，放在同目錄的 `auth.json`：

```json
{"OPENAI_API_KEY":"YOUR_NUOAPI_API_KEY"}
```

Base URL 到 `/v1` 為止，不要再加 `/responses` 或第二個 `/v1`。

## 驗證

完全結束 Codex 再重新開啟，送出一次固定短句，到控制台核對模型與時間。日誌不應再出現 `wss://nuoapi.net/v1/responses`。

若仍重連，先確認檔案位置與程序是否真的重啟。設定步驟見[接入教學](接入第三方工具教程-2026-09-26.md#52-codex-cli-与其他-responses-cli)。
