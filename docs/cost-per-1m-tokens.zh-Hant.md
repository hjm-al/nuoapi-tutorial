<!-- seo-meta
  title: AI API 每百萬 Token 真實成本計算：輸入、輸出與快取
  description: 用本機計算器拆開輸入、輸出、快取讀取、快取寫入、最低儲值與實際到帳額度，比較每百萬 Token 的真實成本與每月費用，不上傳資料。
-->

# AI API 每百萬 Token 成本怎麼算：輸入、輸出與快取

每百萬 Token 單價只是比較起點，不是最後帳單。真實成本還要拆開輸入、輸出、快取讀取、快取寫入、長上下文、最低儲值與實際到帳額度。

> **主要操作**：填入一次請求的 Token 用量與四類每百萬 Token 單價，查看單次成本、每月成本、有效單價與最低儲值次數。

<section class="cost-calculator" data-cost-calculator data-cost-locale="zh-TW" aria-labelledby="cost-calculator-title">
  <div class="cost-calculator-head">
    <p class="cost-kicker">本機計算器</p>
    <h2 id="cost-calculator-title">儲值前先算出真實成本</h2>
    <p id="cost-calculator-help">八項用量與價格欄位必填，最低儲值與每月請求次數可選。計算只在瀏覽器本機完成，不會傳送或保存輸入。</p>
  </div>
  <form class="cost-form" data-cost-form novalidate
    aria-describedby="cost-calculator-help"
    data-msg-ready="本機計算完成，沒有傳送任何資料。"
    data-msg-missing="請填完八項必填的用量與價格欄位。"
    data-msg-invalid="請檢查標示欄位：只能填零或正數，每月請求次數必須是非負整數。"
    data-msg-overflow="結果超出可處理的數值範圍，請減小輸入後重試。">
    <fieldset class="cost-fieldset">
      <legend>1. 單次請求用量</legend>
      <div class="cost-fields">
        <label class="cost-field" for="cost-input-tokens">
          <span>計費輸入 Token</span>
          <span class="cost-input-wrap">
            <input id="cost-input-tokens" name="input_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-output-tokens">
          <span>輸出 Token</span>
          <span class="cost-input-wrap">
            <input id="cost-output-tokens" name="output_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-read-tokens">
          <span>快取讀取 Token</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-read-tokens" name="cache_read_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-write-tokens">
          <span>快取寫入 Token</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-write-tokens" name="cache_write_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
      </div>
    </fieldset>

    <fieldset class="cost-fieldset">
      <legend>2. 每百萬 Token 單價</legend>
      <div class="cost-fields">
        <label class="cost-field cost-field--wide" for="cost-currency">
          <span>顯示貨幣</span>
          <select id="cost-currency" name="currency">
            <option value="USD">USD · 美元</option>
            <option value="EUR">EUR · 歐元</option>
            <option value="CNY">CNY · 人民幣</option>
            <option value="JPY">JPY · 日圓</option>
          </select>
        </label>
        <label class="cost-field" for="cost-input-price">
          <span>輸入單價</span>
          <span class="cost-input-wrap">
            <input id="cost-input-price" name="input_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-output-price">
          <span>輸出單價</span>
          <span class="cost-input-wrap">
            <input id="cost-output-price" name="output_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-read-price">
          <span>快取讀取單價</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-read-price" name="cache_read_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-write-price">
          <span>快取寫入單價</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-write-price" name="cache_write_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
      </div>
    </fieldset>

    <fieldset class="cost-fieldset">
      <legend>3. 儲值與用量規模</legend>
      <div class="cost-fields">
        <label class="cost-field" for="cost-minimum-charge">
          <span>最低儲值金額</span>
          <span class="cost-input-wrap">
            <input id="cost-minimum-charge" name="minimum_charge" type="number" min="0" step="0.01" inputmode="decimal" autocomplete="off">
            <span aria-hidden="true">實付</span>
          </span>
        </label>
        <label class="cost-field" for="cost-credit-amount">
          <span>實際到帳額度</span>
          <span class="cost-input-wrap">
            <input id="cost-credit-amount" name="credit_amount" type="number" min="0" step="0.01" inputmode="decimal" autocomplete="off">
            <span aria-hidden="true">到帳</span>
          </span>
        </label>
        <label class="cost-field" for="cost-monthly-requests">
          <span>每月同類請求次數</span>
          <span class="cost-input-wrap">
            <input id="cost-monthly-requests" name="monthly_requests" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" value="">
            <span aria-hidden="true">次</span>
          </span>
        </label>
      </div>
      <p class="cost-field-note">每月請求次數留空時按一次計算。儲值與到帳金額使用上方選擇的貨幣，不進行匯率換算。</p>
    </fieldset>
  </form>

  <div class="cost-results" data-cost-results aria-live="polite" aria-atomic="false">
    <div class="cost-result">
      <span>單次請求成本</span>
      <strong data-cost-result="request-cost">—</strong>
    </div>
    <div class="cost-result">
      <span>每月總成本</span>
      <strong data-cost-result="monthly-cost">—</strong>
    </div>
    <div class="cost-result">
      <span>有效每百萬 Token 成本</span>
      <strong data-cost-result="effective-per-million">—</strong>
    </div>
    <div class="cost-result">
      <span>到帳額度折算率</span>
      <strong data-cost-result="credit-rate">—</strong>
    </div>
    <div class="cost-result">
      <span>每月最低儲值次數</span>
      <strong data-cost-result="topup-count">—</strong>
    </div>
  </div>
  <p class="cost-status" data-cost-status role="status">填完八項必填欄位後即可計算。輸入只在你的瀏覽器中處理。</p>
</section>

文中以 [`nuoapi.net`](https://nuoapi.net) 作為位址範例。模型 ID、分組、倍率與可用性會變動，請以[模型廣場](https://nuoapi.net/model-plaza)與控制台即時顯示為準。公開價格表不能取代你帳戶實際生效的價格。

## 1. 先統一計價單位

比較前先將貨幣、稅務、1K／1M／站內額度、快取、圖片與工具費用、最低單次計費換算到同一口徑。

```text
每百萬 Token 價格 = 每千 Token 價格 * 1,000
每百萬 Token 價格 = 每 Token 價格 * 1,000,000
```

## 2. 單次請求公式

```text
單次成本 =
  輸入 Token / 1,000,000 * 輸入單價
  + 輸出 Token / 1,000,000 * 輸出單價
  + 快取讀取 Token / 1,000,000 * 快取讀取單價
  + 快取寫入 Token / 1,000,000 * 快取寫入單價
  + 圖片、音訊、搜尋與工具附加費
```

畫面中看得到的文字不一定等於計費輸入。閘道可能加入系統提示、歷史訊息、工具結果或重試內容。對帳時要分開固定前綴、對話歷史與本次內容。

## 3. 計算範例

輸入 800,000、快取讀取 200,000、輸出 300,000 Token，每百萬單價分別為 2、0.50、8：

```text
輸入：    800,000 / 1,000,000 * 2.00 = 1.60
快取讀取：200,000 / 1,000,000 * 0.50 = 0.10
輸出：    300,000 / 1,000,000 * 8.00 = 2.40
單次合計：1.60 + 0.10 + 2.40 = 4.10
```

這只是算術示例，不是報價。快取讀取 Token 是否也計入普通輸入，必須依服務的計費說明核對。

## 4. 長上下文與快取

多輪對話若重送完整歷史，每輪輸入都會增加。要分別記錄系統提示、保留歷史、文件、工具結果、快取命中、摘要與重試。上下文窗口很大，不代表使用它很便宜。

## 5. 最低儲值與到帳額度

```text
額度折算率 = 實付金額 / 實際到帳額度
```

支付 100、到帳 100 的折算率是 1.0；支付 100、到帳 80 是 1.25。還要記錄有效期限、可用分組、退款條件與無法使用的餘額。

## 6. 每月總成本

```text
每月總成本 =
  單次成本 * 請求次數
  + 重試與失敗請求費用
  + 固定費用
  + 被最低儲值占用的未使用餘額
```

至少模擬輕度、團隊與長上下文三種情境，不要只用一個平均請求估算。

## 7. 價差要回到證據

價差很大時，先核對模型 ID、上下文、量化、分組、區域、快取、限速與支援層級。模型身份要依[驗證方法](MODEL_VERIFICATION_METHODS.md)得到 **匹配 / 不匹配 / 證據不足** 三態結論。

```bash
python examples/model_verify.py --selftest
python examples/model_verify.py
```

第二條命令預設只顯示計畫，不會送出計費請求。

## 8. 檢查清單

1. 所有價格使用相同貨幣、單位與日期。
2. 輸入、輸出、快取讀取、快取寫入分開記錄。
3. 長上下文、重試與系統提示計入輸入。
4. 最低儲值、到帳額度、期限與退款條件已記錄。
5. 公開價格與帳戶實際價格分別保存。
6. 用一次真實帳單覆核計算結果。

## 相關頁面

- [模型真偽與防摻水方法](MODEL_VERIFICATION_METHODS.md)
- [Codex 一直 Reconnecting](Codex-一直Reconnecting-2026-10-18.zh-Hant.md)
- [Claude Code 報 404](Claude-Code-不要加v1-2026-10-18.zh-Hant.md)

## 免責聲明

本文是獨立技術資料，不提供也不轉售 API 服務，與 OpenAI、Anthropic、Google、xAI、ByteDance、DeepSeek、MiniMax 等廠商沒有官方關聯。產品名稱歸各自所有者。使用前請核對最新條款、隱私政策、價格與可用性。
