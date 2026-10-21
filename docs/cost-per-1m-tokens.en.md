<!-- seo-meta
  title: AI API Cost per 1M Tokens: Real Cost Calculator
  description: Calculate input, output, cache read, cache write, monthly usage, minimum top-up, and effective credit cost locally without sending your data anywhere.
-->

# AI API Cost per 1M Tokens: Input, Output and Cache

A headline price per 1M tokens is only a comparison unit. The final bill also depends on billed input, output, cache reads, cache writes, long context, minimum top-up, and the credit you actually receive.

> **Primary action**: enter one request's token usage and four per-million-token prices to calculate request cost, monthly cost, effective unit cost, and the number of minimum top-ups.

<section class="cost-calculator" data-cost-calculator data-cost-locale="en-US" aria-labelledby="cost-calculator-title">
  <div class="cost-calculator-head">
    <p class="cost-kicker">Local calculator</p>
    <h2 id="cost-calculator-title">Calculate the real cost before topping up</h2>
    <p id="cost-calculator-help">The eight usage and price fields are required. Top-up and monthly volume are optional. All calculations run in your browser; no input is sent or saved.</p>
  </div>
  <form class="cost-form" data-cost-form novalidate
    aria-describedby="cost-calculator-help"
    data-msg-ready="Local calculation completed. No data was sent."
    data-msg-missing="Complete all eight required usage and price fields."
    data-msg-invalid="Check the marked fields: use zero or a positive number, and monthly requests must be a non-negative integer."
    data-msg-overflow="The result exceeds the supported numeric range. Reduce the inputs and try again.">
    <fieldset class="cost-fieldset">
      <legend>1. Usage for one request</legend>
      <div class="cost-fields">
        <label class="cost-field" for="cost-input-tokens">
          <span>Billed input tokens</span>
          <span class="cost-input-wrap">
            <input id="cost-input-tokens" name="input_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-output-tokens">
          <span>Output tokens</span>
          <span class="cost-input-wrap">
            <input id="cost-output-tokens" name="output_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-read-tokens">
          <span>Cache read tokens</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-read-tokens" name="cache_read_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-write-tokens">
          <span>Cache write tokens</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-write-tokens" name="cache_write_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
      </div>
    </fieldset>

    <fieldset class="cost-fieldset">
      <legend>2. Price per 1M tokens</legend>
      <div class="cost-fields">
        <label class="cost-field cost-field--wide" for="cost-currency">
          <span>Display currency</span>
          <select id="cost-currency" name="currency">
            <option value="USD">USD · US dollar</option>
            <option value="EUR">EUR · euro</option>
            <option value="CNY">CNY · Chinese yuan</option>
            <option value="JPY">JPY · Japanese yen</option>
          </select>
        </label>
        <label class="cost-field" for="cost-input-price">
          <span>Input price</span>
          <span class="cost-input-wrap">
            <input id="cost-input-price" name="input_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-output-price">
          <span>Output price</span>
          <span class="cost-input-wrap">
            <input id="cost-output-price" name="output_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-read-price">
          <span>Cache read price</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-read-price" name="cache_read_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-write-price">
          <span>Cache write price</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-write-price" name="cache_write_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
      </div>
    </fieldset>

    <fieldset class="cost-fieldset">
      <legend>3. Top-up and monthly volume</legend>
      <div class="cost-fields">
        <label class="cost-field" for="cost-minimum-charge">
          <span>Minimum top-up amount</span>
          <span class="cost-input-wrap">
            <input id="cost-minimum-charge" name="minimum_charge" type="number" min="0" step="0.01" inputmode="decimal" autocomplete="off">
            <span aria-hidden="true">paid</span>
          </span>
        </label>
        <label class="cost-field" for="cost-credit-amount">
          <span>Credit received</span>
          <span class="cost-input-wrap">
            <input id="cost-credit-amount" name="credit_amount" type="number" min="0" step="0.01" inputmode="decimal" autocomplete="off">
            <span aria-hidden="true">credited</span>
          </span>
        </label>
        <label class="cost-field" for="cost-monthly-requests">
          <span>Similar requests per month</span>
          <span class="cost-input-wrap">
            <input id="cost-monthly-requests" name="monthly_requests" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" value="">
            <span aria-hidden="true">times</span>
          </span>
        </label>
      </div>
      <p class="cost-field-note">Leave monthly requests empty to calculate one request. Top-up and credit amounts use the selected display currency; no exchange-rate conversion is performed.</p>
    </fieldset>
  </form>

  <div class="cost-results" data-cost-results aria-live="polite" aria-atomic="false">
    <div class="cost-result">
      <span>Cost per request</span>
      <strong data-cost-result="request-cost">—</strong>
    </div>
    <div class="cost-result">
      <span>Monthly cost</span>
      <strong data-cost-result="monthly-cost">—</strong>
    </div>
    <div class="cost-result">
      <span>Effective cost per 1M tokens</span>
      <strong data-cost-result="effective-per-million">—</strong>
    </div>
    <div class="cost-result">
      <span>Credit conversion rate</span>
      <strong data-cost-result="credit-rate">—</strong>
    </div>
    <div class="cost-result">
      <span>Minimum top-ups per month</span>
      <strong data-cost-result="topup-count">—</strong>
    </div>
  </div>
  <p class="cost-status" data-cost-status role="status">Complete the eight required fields to calculate. Inputs are processed only in your browser.</p>
</section>

The example address is [`nuoapi.net`](https://nuoapi.net). Model IDs, groups, rates, and availability change, so confirm current values in the [model plaza](https://nuoapi.net/model-plaza) and your console. A public price table does not replace the rate applied to your account.

## 1. Normalize the billing unit

Before comparing prices, align currency, tax treatment, billing unit, cache semantics, image or tool charges, and minimum billing rules.

```text
price per 1M = price per 1K * 1,000
price per 1M = price per token * 1,000,000
```

## 2. Calculate one request

```text
request cost =
  input tokens / 1,000,000 * input price
  + output tokens / 1,000,000 * output price
  + cache read tokens / 1,000,000 * cache read price
  + cache write tokens / 1,000,000 * cache write price
  + image, audio, search, and tool charges
```

Visible text is not always billed input. A gateway may add system prompts, retained history, tool results, or retries. Reconcile the fixed prefix, conversation history, and new request separately.

## 3. Worked example

For 800,000 input tokens, 200,000 cache-read tokens, and 300,000 output tokens at example prices of 2, 0.50, and 8 per 1M:

```text
input:      800,000 / 1,000,000 * 2.00 = 1.60
cache read: 200,000 / 1,000,000 * 0.50 = 0.10
output:     300,000 / 1,000,000 * 8.00 = 2.40
total:      1.60 + 0.10 + 2.40 = 4.10
```

This is arithmetic, not a quote. Check whether cache-read tokens are also included in ordinary billed input.

## 4. Long context and cache

Repeated history makes input grow every turn. Record system prompts, retained history, documents, tool results, cache hits, summaries, and retries separately. A large context window is not permission to treat every turn as a short request.

## 5. Top-up and effective credit

```text
credit conversion rate = amount paid / credit received
```

Paying 100 for 100 in credit gives 1.0; paying 100 for 80 gives 1.25. Add expiration, group restrictions, refund terms, and unusable balance to the comparison.

## 6. Monthly cost

```text
monthly cost =
  request cost * number of requests
  + retries and billed failures
  + fixed fees
  + unused balance tied up by a minimum top-up
```

Model light, team, and long-context scenarios instead of relying on one average request.

## 7. Investigate a price gap

Check the exact model ID, context, quantization, group, region, cache, rate limits, and support level before treating a lower headline price as better value. Use the [model verification methodology](MODEL_VERIFICATION_METHODS.md) and record **match / mismatch / insufficient evidence**.

```bash
python examples/model_verify.py --selftest
python examples/model_verify.py
```

The second command prints a plan and does not send a billed request unless `--run` is added.

## 8. Review checklist

1. Every price uses the same currency, unit, and date.
2. Input, output, cache read, and cache write are separate.
3. Long context, retries, and injected prompts are included.
4. Top-up, credit, expiration, and refund terms are recorded.
5. Public and account-specific prices are kept separate.
6. A real invoice is reconciled against the calculation.

## Related pages

- [Model verification methodology](MODEL_VERIFICATION_METHODS.md)
- [LLM gateway checklist](llm-gateway-checklist.en.md)
- [Codex reconnect troubleshooting](Codex-一直Reconnecting-2026-10-18.en.md)

## Legal and vendor boundary

This is independent technical material. It does not provide or resell API access and is not affiliated with OpenAI, Anthropic, Google, xAI, ByteDance, DeepSeek, MiniMax, or any other model vendor. Product names belong to their owners. Confirm current terms, privacy policy, pricing, and availability before use.
