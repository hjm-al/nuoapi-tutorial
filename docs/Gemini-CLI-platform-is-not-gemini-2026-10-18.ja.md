<!-- seo-meta
  title: Gemini CLI platform is not gemini：Base URL はルートだけ
  description: 400 platform is not gemini や無応答はプロトコル経路の誤りがよくあります。Base URL から /v1beta を外し、モデル ID と再起動を確認します。
-->

# Gemini CLI: platform is not gemini

> **法的通知と商標について**
>
> 1. 本記事は独立した設定ガイドです。Google、OpenAI、Anthropic その他の提供者と提携していません。名称は互換性の説明だけに使います。
> 2. 本リポジトリは API アクセスを提供・再販しません。
> 3. 利用前に各サービスの規約、プライバシーポリシー、価格、可用性を確認してください。

接続先の例は [`nuoapi.net`](https://nuoapi.net) です。現在のモデル ID は同じグループからコピーし、[モデル広場](https://nuoapi.net/model-plaza)と管理画面で確認してください。

## 症状

- `400 platform is not gemini`：リクエストが Gemini のプロトコル経路に入っていません。
- Gemini CLI が応答しない、またはパスが不正：`GOOGLE_GEMINI_BASE_URL` に `/v1beta` が付いている可能性があります。

`API_KEY_INVALID` や `API key not valid` は認証情報の問題で、上の二つとは別です。経路の考え方は[プロトコル解説](AI模型API协议科普-2026-10-12.md#6-gemini-原生协议)にあります。

## 一つの設定

`~/.gemini/.env`：

```env
GOOGLE_GEMINI_BASE_URL=https://nuoapi.net
GEMINI_API_KEY=YOUR_NUOAPI_API_KEY
GEMINI_MODEL=MODEL_NAME_FROM_MODEL_PLAZA
```

Base URL の末尾に `/v1` や `/v1beta` を追加しません。モデル ID は日付サフィックスを含め、現在のグループ表示と完全に一致させます。

## 確認

Gemini CLI を終了し、新しいターミナルで起動し直します。短い固定文を一回送り、管理画面で同じモデル名と時刻を確認してください。詳しい設定は[サードパーティ製ツールガイド](接入第三方工具教程-2026-09-26.md#53-gemini-cli)にあります。

`API_KEY_INVALID` の場合は経路を変えず、[401 ガイド](401-invalid-api-key.md)へ進みます。
