<!-- seo-meta
  title: AI API の 1M Token 実費計算：入力・出力・キャッシュ
  description: 入力、出力、キャッシュ読取・書込、最低入金、付与クレジットから 1M Token あたりの実費と月額をブラウザ内で計算します。入力データは送信しません。
-->

# AI API の 1M Token あたりの実費：入力・出力・キャッシュ

1M Token あたりの表示単価は比較の出発点にすぎません。実際の請求額は、課金対象の入力、出力、キャッシュ読取・書込、長い文脈、最低入金額、実際に付与されるクレジットによって変わります。

> **主な操作**：1 回の Token 使用量と 4 種類の 1M Token 単価を入力し、1 リクエスト料金、月額、実効単価、最低入金の必要回数を確認します。

<section class="cost-calculator" data-cost-calculator data-cost-locale="ja-JP" aria-labelledby="cost-calculator-title">
  <div class="cost-calculator-head">
    <p class="cost-kicker">ローカル計算機</p>
    <h2 id="cost-calculator-title">入金前に実際の費用を計算</h2>
    <p id="cost-calculator-help">使用量と価格の 8 項目は必須です。最低入金と月間リクエスト数は任意です。計算はブラウザ内だけで実行され、入力内容は送信・保存されません。</p>
  </div>
  <form class="cost-form" data-cost-form novalidate
    aria-describedby="cost-calculator-help"
    data-msg-ready="ローカル計算が完了しました。データは送信されていません。"
    data-msg-missing="必須の使用量・価格 8 項目をすべて入力してください。"
    data-msg-invalid="印を付けた項目を確認してください。0 または正の数を使い、月間リクエスト数は 0 以上の整数にしてください。"
    data-msg-overflow="結果が処理可能な数値範囲を超えました。入力値を小さくして再試行してください。">
    <fieldset class="cost-fieldset">
      <legend>1. 1 リクエストの使用量</legend>
      <div class="cost-fields">
        <label class="cost-field" for="cost-input-tokens">
          <span>課金対象の入力 Token</span>
          <span class="cost-input-wrap">
            <input id="cost-input-tokens" name="input_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-output-tokens">
          <span>出力 Token</span>
          <span class="cost-input-wrap">
            <input id="cost-output-tokens" name="output_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-read-tokens">
          <span>キャッシュ読取 Token</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-read-tokens" name="cache_read_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-write-tokens">
          <span>キャッシュ書込 Token</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-write-tokens" name="cache_write_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
      </div>
    </fieldset>

    <fieldset class="cost-fieldset">
      <legend>2. 1M Token あたりの価格</legend>
      <div class="cost-fields">
        <label class="cost-field cost-field--wide" for="cost-currency">
          <span>表示通貨</span>
          <select id="cost-currency" name="currency">
            <option value="USD">USD · 米ドル</option>
            <option value="EUR">EUR · ユーロ</option>
            <option value="CNY">CNY · 人民元</option>
            <option value="JPY">JPY · 日本円</option>
          </select>
        </label>
        <label class="cost-field" for="cost-input-price">
          <span>入力価格</span>
          <span class="cost-input-wrap">
            <input id="cost-input-price" name="input_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-output-price">
          <span>出力価格</span>
          <span class="cost-input-wrap">
            <input id="cost-output-price" name="output_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-read-price">
          <span>キャッシュ読取価格</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-read-price" name="cache_read_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-write-price">
          <span>キャッシュ書込価格</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-write-price" name="cache_write_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
      </div>
    </fieldset>

    <fieldset class="cost-fieldset">
      <legend>3. 入金と月間利用量</legend>
      <div class="cost-fields">
        <label class="cost-field" for="cost-minimum-charge">
          <span>最低入金額</span>
          <span class="cost-input-wrap">
            <input id="cost-minimum-charge" name="minimum_charge" type="number" min="0" step="0.01" inputmode="decimal" autocomplete="off">
            <span aria-hidden="true">支払</span>
          </span>
        </label>
        <label class="cost-field" for="cost-credit-amount">
          <span>実際の付与クレジット</span>
          <span class="cost-input-wrap">
            <input id="cost-credit-amount" name="credit_amount" type="number" min="0" step="0.01" inputmode="decimal" autocomplete="off">
            <span aria-hidden="true">付与</span>
          </span>
        </label>
        <label class="cost-field" for="cost-monthly-requests">
          <span>月間の同種リクエスト数</span>
          <span class="cost-input-wrap">
            <input id="cost-monthly-requests" name="monthly_requests" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" value="">
            <span aria-hidden="true">回</span>
          </span>
        </label>
      </div>
      <p class="cost-field-note">月間リクエスト数が空の場合は 1 回として計算します。入金額と付与額は上で選んだ通貨で表示し、為替換算は行いません。</p>
    </fieldset>
  </form>

  <div class="cost-results" data-cost-results aria-live="polite" aria-atomic="false">
    <div class="cost-result">
      <span>1 リクエストの費用</span>
      <strong data-cost-result="request-cost">—</strong>
    </div>
    <div class="cost-result">
      <span>月間総費用</span>
      <strong data-cost-result="monthly-cost">—</strong>
    </div>
    <div class="cost-result">
      <span>1M Token あたりの実効費用</span>
      <strong data-cost-result="effective-per-million">—</strong>
    </div>
    <div class="cost-result">
      <span>クレジット換算率</span>
      <strong data-cost-result="credit-rate">—</strong>
    </div>
    <div class="cost-result">
      <span>月間の最低入金回数</span>
      <strong data-cost-result="topup-count">—</strong>
    </div>
  </div>
  <p class="cost-status" data-cost-status role="status">必須 8 項目を入力すると計算できます。入力はブラウザ内だけで処理されます。</p>
</section>

接続先の例は [`nuoapi.net`](https://nuoapi.net) です。モデル ID、グループ、倍率、可用性は変わるため、現在値は[モデル広場](https://nuoapi.net/model-plaza)と管理画面で確認してください。公開価格表は、自分のアカウントに適用される価格の代わりにはなりません。

## 1. 請求単位をそろえる

通貨、税の扱い、1K・1M・独自クレジットの単位、キャッシュ、画像・音声・ツール料金、最低請求単位を同じ条件に変換します。

```text
1M Token の価格 = 1K Token の価格 * 1,000
1M Token の価格 = 1 Token の価格 * 1,000,000
```

## 2. 1 リクエストの計算

```text
リクエスト費用 =
  入力 Token / 1,000,000 * 入力価格
  + 出力 Token / 1,000,000 * 出力価格
  + キャッシュ読取 Token / 1,000,000 * 読取価格
  + キャッシュ書込 Token / 1,000,000 * 書込価格
  + 画像・音声・検索・ツールの追加料金
```

画面に見える文章と課金対象の入力は同じとは限りません。ゲートウェイが system prompt、履歴、ツール結果、再試行を追加する場合があります。

## 3. 計算例

入力 800,000、キャッシュ読取 200,000、出力 300,000 Token、1M Token あたりの価格を入力 2、読取 0.50、出力 8 とします。

```text
入力:      800,000 / 1,000,000 * 2.00 = 1.60
キャッシュ:200,000 / 1,000,000 * 0.50 = 0.10
出力:      300,000 / 1,000,000 * 8.00 = 2.40
合計:      1.60 + 0.10 + 2.40 = 4.10
```

これは算術例であり、提供価格ではありません。キャッシュ読取が通常の入力にも含まれるか確認してください。

## 4. 長い文脈とキャッシュ

履歴を毎回送る場合、ターンごとに入力が増えます。system prompt、保持した履歴、文書、ツール結果、キャッシュ命中、要約、再試行を分けて記録します。大きなコンテキストウィンドウは、その利用が安いという意味ではありません。

## 5. 最低入金と実効クレジット

```text
クレジット換算率 = 支払額 / 付与クレジット
```

100 支払って 100 付与なら 1.0、100 支払って 80 付与なら 1.25 です。有効期限、利用可能グループ、返金条件、使えない残高も比較に含めます。

## 6. 月額費用

```text
月額総費用 =
  1 回の費用 * リクエスト数
  + 再試行・失敗した課金
  + 固定費
  + 最低入金で拘束される未使用残高
```

軽い利用、チーム利用、長い文脈の 3 シナリオを試算し、平均 1 リクエストだけで判断しないでください。

## 7. 価格差を確認する

表示価格が低い理由を判断する前に、正確なモデル ID、コンテキスト、量子化、グループ、地域、キャッシュ、速度制限、サポートを確認します。モデルの同一性は[検証方法](MODEL_VERIFICATION_METHODS.md)に従い、**一致 / 不一致 / 証拠不足** の三状態で記録します。

```bash
python examples/model_verify.py --selftest
python examples/model_verify.py
```

2 番目は計画を表示するだけで、`--run` を付けない限り課金リクエストを送りません。

## 8. 確認チェックリスト

1. すべての価格を通貨、単位、確認日付でそろえた。
2. 入力、出力、キャッシュ読取、キャッシュ書込を分けた。
3. 長い文脈、再試行、追加された system prompt を入力に含めた。
4. 最低入金、付与額、有効期限、返金条件を記録した。
5. 公開価格とアカウント固有価格を分けた。
6. 実際の請求書 1 件と計算結果を照合した。

## 関連ページ

- [モデル検証の方法論](MODEL_VERIFICATION_METHODS.md)
- [AI API の最低チャージと料金](minimum-charge-and-pricing.ja.md)
- [Codex が Reconnecting を繰り返す](Codex-一直Reconnecting-2026-10-18.ja.md)

## 免責事項

本稿は独立した技術資料であり、API アクセスを提供・再販するものではありません。OpenAI、Anthropic、Google、xAI、ByteDance、DeepSeek、MiniMax その他の提供者との公式な提携関係はありません。製品名は各所有者の商標です。利用前に最新の規約、プライバシーポリシー、料金、可用性を確認してください。
