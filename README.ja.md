<!-- seo-meta
  title: NuoAPI 接続ガイド：Codex / Claude Code / Gemini CLI
  description: Codex、Claude Code、Gemini CLI を AI ゲートウェイへ接続し、Base URL 設定、課金前のドライラン、モデル真偽の三態判定を確認する実用手順と費用計算への入口。
-->

# [NuoAPI](https://nuoapi.net/model-plaza) 接続スターターとモデル検証ツール

> **法的通知と商標について**
>
> 1. 本リポジトリは個人開発者が維持する独立した技術研究、設定用スキャフォールド、診断テストスイートです。API サービスを提供・再販しません。OpenAI、Anthropic、Google、xAI、ByteDance（バイトダンス）、DeepSeek、MiniMax その他のモデル提供者と公式な提携、投資、スポンサー、協力関係はありません。
> 2. 各製品名・会社名は各所有者の商標です。プロトコル互換性と設定を説明する目的でのみ記載します。
> 3. すべてのサンプルはプレースホルダー（`YOUR_NUOAPI_API_KEY`）のみです。本リポジトリは誰の API キーも収集しません。利用前に各サービスの規約、プライバシーポリシー、価格、可用性を確認してください。

Codex、Claude Code、Gemini CLI などをサードパーティ製 AI ゲートウェイへ接続し、**課金された応答が表示上のモデルと一致するか**を再現可能な手順で確認するためのリポジトリです。判定の根拠と三状態の書き方は[モデル検証の方法論](docs/MODEL_VERIFICATION_METHODS.md)にまとめています。

[简体中文](README.md) · [English](README.en.md) · 日本語 · [Español](README.es.md) · [繁體中文](README.zh-Hant.md)

## 言語別の検証入口

- [English: LLM gateway checklist](docs/llm-gateway-checklist.en.md)：モデルの一貫性、データ所在、BYOK、監査、フェイルオーバー。
- [日本語：最低チャージと料金](docs/minimum-charge-and-pricing.ja.md)：最低入金額、クレジット換算、公開価格と実効価格。
- [日本語：1M Token あたりの実費](docs/cost-per-1m-tokens.ja.md)：入力、出力、キャッシュ、最低入金を含む総コストをブラウザ内で計算。

## よくあるエラー早見表

- [Gemini CLI: platform is not gemini](docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.ja.md)
- [Codex が Reconnecting を繰り返す](docs/Codex-一直Reconnecting-2026-10-18.ja.md)
- [Claude Code の 404: /v1 を付けない](docs/Claude-Code-不要加v1-2026-10-18.ja.md)
- [401 invalid_api_key](docs/401-invalid-api-key.md)
- [400 invalid_request_error](docs/400-invalid-request-error.md)
- [404 model_not_found](docs/model_not_found.md)

## 課金せずに確認する

最初のコマンドはローカル検証です。二つ目は課金リクエストを送らず、実行計画だけを表示します。

```bash
python examples/model_verify.py --selftest
python examples/model_verify.py
```

`--run` を付けない限り、モデルへの課金リクエストは送られません。判定は「一致」「不一致」「証拠不足」の三種類だけです。

## Base URL 早見表

| クライアント | Base URL | よくある誤り |
|---|---|---|
| Codex | `https://nuoapi.net/v1`、`wire_api = "responses"` | WebSocket を有効のままにする |
| Claude Code | `https://nuoapi.net` | `/v1` を重複して付ける |
| Gemini CLI | `https://nuoapi.net` | `/v1beta` を付ける |

テスト前に[アカウント登録](https://nuoapi.net/register)と[キー管理](https://nuoapi.net/keys)から専用 Key を作成してください。接続先の例は nuoapi.net です。モデル ID、グループ、倍率、可用性は変わるため、現在値はモデル広場からコピーし、管理画面の表示を優先してください。

## 判定の読み方

- **一致**：観測した証拠が主張されたモデルとプロトコルに整合する。
- **不一致**：判別力のある証拠が主張と矛盾する。
- **証拠不足**：サンプル、フィールド、取得期間では判定できない。

モデルの自己紹介、応答速度、公開クイズ一回だけでは真偽を決められません。結果には証拠取得期間と正確なエンドポイントを残してください。

## 安全上の注意

自分のテストキーでローカル実行し、用が済んだら無効化してください。表示されるキーはマスクされます。UTM、アフィリエイト転送、独自トラッキングは使用しません。

本リポジトリは API アクセスを提供・再販せず、投資や購入の推奨でもありません。
