<!-- seo-meta
  title: Claude Code の 404：Base URL に /v1 を付けない
  description: Claude Code は /v1/messages を自分で組み立てます。ANTHROPIC_BASE_URL はルートを指定し、AUTH_TOKEN と新しいターミナルを確認します。
-->

# Claude Code の 404：/v1 を付けない

> **法的通知と商標について**
>
> 1. 本記事は独立した設定ガイドです。Anthropic その他のモデル提供者と提携していません。名称は互換性の説明だけに使います。
> 2. 本リポジトリは API アクセスを提供・再販しません。
> 3. 利用前に各サービスの規約、プライバシーポリシー、価格、可用性を確認してください。

接続先の例は [`nuoapi.net`](https://nuoapi.net) です。現在のモデル ID を同じグループからコピーし、[モデル広場](https://nuoapi.net/model-plaza)と管理画面で確認してください。

## 症状

`401` ではなく、平文の `404 page not found` が返ります。よくある原因は `ANTHROPIC_BASE_URL` への `/v1` 追加です。Claude Code がそこへ `/v1/messages` を足すため、経路が一致しません。

変数名も重要です。`ANTHROPIC_API_KEY` ではなく `ANTHROPIC_AUTH_TOKEN` を使います。

## 一つの設定

```text
ANTHROPIC_BASE_URL=https://nuoapi.net
ANTHROPIC_AUTH_TOKEN=YOUR_NUOAPI_API_KEY
```

現在の PowerShell ターミナル：

```powershell
$env:ANTHROPIC_BASE_URL = "https://nuoapi.net"
$env:ANTHROPIC_AUTH_TOKEN = "YOUR_NUOAPI_API_KEY"
```

恒久設定は OS の環境変数画面などを使います。既に起動しているプロセスは、変更後の値を自動では読みません。

## 確認

新しいターミナルで Claude Code を起動し、短い固定文を一回送ります。管理画面でモデル名と時刻を確認してください。古い `/v1` 付きの値が残る場合は、前のプロセスが旧環境を使っています。

各 OS の設定は[サードパーティ製ツールガイド](接入第三方工具教程-2026-09-26.md#51-claude-code-与-claude-类工具)にあります。
