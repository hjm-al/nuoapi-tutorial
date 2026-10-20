<!-- seo-meta
  title: Codex が Reconnecting を繰り返す：WebSocket を無効化
  description: Codex の再接続や wss:// の /v1/responses ログは WebSocket 試行が原因です。Responses の HTTP 経路を設定し、完全に再起動します。
-->

# Codex が Reconnecting を繰り返す：WebSocket を無効化

> **法的通知と商標について**
>
> 1. 本記事は独立した設定ガイドです。OpenAI その他のモデル提供者と提携していません。名称は互換性の説明だけに使います。
> 2. 本リポジトリは API アクセスを提供・再販しません。
> 3. 利用前に各サービスの規約、プライバシーポリシー、価格、可用性を確認してください。

接続先の例は [`nuoapi.net`](https://nuoapi.net) です。現在のモデル ID を同じグループからコピーし、[モデル広場](https://nuoapi.net/model-plaza)と管理画面で確認してください。

## 症状

Codex が `Reconnecting` を繰り返す、またはログに次のいずれかが出ます。

- `wss://nuoapi.net/v1/responses`
- `WebSocket connection ... failed`
- `connecting to wss://...` の繰り返し

HTTP Responses を使うべき経路で WebSocket を試しています。代理設定の環境変数だけでは、この試行は止まりません。

## 一つの設定

macOS / Linux は `~/.codex/config.toml`、Windows は `%USERPROFILE%\.codex\config.toml`：

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

API キーは TOML に書かず、同じディレクトリの `auth.json` に置きます。

```json
{"OPENAI_API_KEY":"YOUR_NUOAPI_API_KEY"}
```

Base URL は `/v1` までです。`/responses` や二つ目の `/v1` を追加しません。

## 確認

Codex を完全に終了して起動し直し、短い固定文を一回送ります。管理画面でモデル名と時刻を確認し、ログから `wss://nuoapi.net/v1/responses` が消えたことを確認してください。

続く場合は設定ファイルの場所とプロセス再起動を確認します。詳細は[設定ガイド](接入第三方工具教程-2026-09-26.md#52-codex-cli-与其他-responses-cli)にあります。
