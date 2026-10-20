<!-- seo-meta
  title: Gemini CLI platform is not gemini：Base URL 只填根位址
  description: 出現 400 platform is not gemini 或 CLI 無回應時，先確認 GOOGLE_GEMINI_BASE_URL 沒有多加 /v1beta，模型 ID 與目前分組一致。
-->

# Gemini CLI：platform is not gemini

> **法律與第三方商標免責聲明**
>
> 1. 本文是獨立開發者維護的設定說明，與 Google、OpenAI、Anthropic 或其他廠商沒有官方關聯。名稱只用於說明協定相容性。
> 2. 本倉庫不提供、不代售任何 API 服務。
> 3. 使用第三方服務前，請自行核對條款、隱私政策、價格與可用性。

位址夾具是 [`nuoapi.net`](https://nuoapi.net)。目前的模型 ID 請從相同分組複製，並在[模型廣場](https://nuoapi.net/model-plaza)與控制台確認。

## 症狀

- `400 platform is not gemini`：請求沒有進入 Gemini 協定路徑。
- Gemini CLI 沒有回應或路徑異常：`GOOGLE_GEMINI_BASE_URL` 可能誤加了 `/v1beta`。

`API_KEY_INVALID` 或 `API key not valid` 是憑證問題，和上面兩種不同。協定背景見[API 協定科普](AI模型API协议科普-2026-10-12.md#6-gemini-原生协议)。

## 單一設定

`~/.gemini/.env`：

```env
GOOGLE_GEMINI_BASE_URL=https://nuoapi.net
GEMINI_API_KEY=YOUR_NUOAPI_API_KEY
GEMINI_MODEL=MODEL_NAME_FROM_MODEL_PLAZA
```

Base URL 結尾不要加 `/v1` 或 `/v1beta`。模型 ID 必須和目前分組完全一致，包含日期後綴。

## 驗證

結束 Gemini CLI，重新開一個終端再啟動。送出一次固定短句，到控制台核對模型名稱與時間。完整設定見[第三方工具教學](接入第三方工具教程-2026-09-26.md#53-gemini-cli)。

若正文是 `API_KEY_INVALID`，先看[401 排查頁](401-invalid-api-key.md)，不要改協定路徑。
