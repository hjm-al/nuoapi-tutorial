<!-- seo-meta
  title: NuoAPI 接続ガイド：Codex / Claude Code / Gemini CLI
  description: よく使う AI クライアントの Base URL を設定し、課金前のドライランとモデル判定の三つの結果を確認する実用手順。
-->

# NuoAPI 接続スターターとモデル検証ツール

> **法的通知と商標について**
>
> 1. 本リポジトリは独立した技術ガイドと診断ツールです。API サービスを提供・再販しません。OpenAI、Anthropic、Google、xAI その他のモデル提供者と提携していません。
> 2. 各製品名・会社名は各所有者の商標です。プロトコル互換性と設定を説明する目的でのみ記載します。
> 3. サンプルはプレースホルダーのみです。利用前に各サービスの規約、プライバシーポリシー、価格、可用性を確認してください。

Codex、Claude Code、Gemini CLI などをサードパーティ製 AI ゲートウェイへ接続し、**課金された応答が表示上のモデルと一致するか**を再現可能な手順で確認するためのリポジトリです。

[简体中文](README.md) · [English](README.en.md) · 日本語 · [繁體中文](README.zh-Hant.md)

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

接続先の例は [`nuoapi.net`](https://nuoapi.net) です。モデル ID、グループ、倍率、可用性は変わるため、[モデル広場](https://nuoapi.net/model-plaza)で現在値を確認し、管理画面の表示を優先してください。

## エラー別ガイド

- [Gemini CLI: platform is not gemini](docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.ja.md)
- [Codex が Reconnecting を繰り返す](docs/Codex-一直Reconnecting-2026-10-18.ja.md)
- [Claude Code の 404: /v1 を付けない](docs/Claude-Code-不要加v1-2026-10-18.ja.md)

## 判定の読み方

- **一致**：観測した証拠が主張されたモデルとプロトコルに整合する。
- **不一致**：判別力のある証拠が主張と矛盾する。
- **証拠不足**：サンプル、フィールド、取得期間では判定できない。

モデルの自己紹介、応答速度、公開クイズ一回だけでは真偽を決められません。結果には証拠取得期間と正確なエンドポイントを残してください。

## 安全上の注意

自分のテストキーでローカル実行し、用が済んだら無効化してください。表示されるキーはマスクされます。UTM、アフィリエイト転送、独自トラッキングは使用しません。

本リポジトリは API アクセスを提供・再販せず、投資や購入の推奨でもありません。
