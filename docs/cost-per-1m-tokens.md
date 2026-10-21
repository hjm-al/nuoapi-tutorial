<!-- seo-meta
  title: AI API 每百万 Token 真实成本计算：输入、输出与缓存
  description: 用本地计算器拆开输入、输出、缓存读取、缓存写入、最低充值和到账额度，比较每百万 Token 的真实成本与每月费用，不上传数据。
-->

# AI API 每百万 Token 成本怎么算：输入、输出与缓存

每百万 Token 单价只是比较起点，不是最终账单。真实成本还要拆开输入、输出、缓存读取、缓存写入、长上下文、最低充值和实际到账额度。

> **主操作**：填入一次请求的 Token 用量和四类每百万 Token 单价，查看单次成本、月度成本、有效单价以及最低充值次数。

<section class="cost-calculator" data-cost-calculator data-cost-locale="zh-CN" aria-labelledby="cost-calculator-title">
  <div class="cost-calculator-head">
    <p class="cost-kicker">本地计算器</p>
    <h2 id="cost-calculator-title">充值前先算出真实成本</h2>
    <p id="cost-calculator-help">八项用量与价格字段必填，最低充值和每月请求次数可选。计算只在浏览器本地完成，不会发送或保存输入。</p>
  </div>
  <form class="cost-form" data-cost-form novalidate
    aria-describedby="cost-calculator-help"
    data-msg-ready="本地计算完成，没有发送任何数据。"
    data-msg-missing="请填完八项必填的用量和价格字段。"
    data-msg-invalid="请检查标红字段：只能填零或正数，每月请求次数必须是非负整数。"
    data-msg-overflow="结果超出可处理的数值范围，请减小输入后重试。">
    <fieldset class="cost-fieldset">
      <legend>1. 单次请求用量</legend>
      <div class="cost-fields">
        <label class="cost-field" for="cost-input-tokens">
          <span>计费输入 Token</span>
          <span class="cost-input-wrap">
            <input id="cost-input-tokens" name="input_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-output-tokens">
          <span>输出 Token</span>
          <span class="cost-input-wrap">
            <input id="cost-output-tokens" name="output_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-read-tokens">
          <span>缓存读取 Token</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-read-tokens" name="cache_read_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-write-tokens">
          <span>缓存写入 Token</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-write-tokens" name="cache_write_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
      </div>
    </fieldset>

    <fieldset class="cost-fieldset">
      <legend>2. 每百万 Token 单价</legend>
      <div class="cost-fields">
        <label class="cost-field cost-field--wide" for="cost-currency">
          <span>显示货币</span>
          <select id="cost-currency" name="currency">
            <option value="USD">USD · 美元</option>
            <option value="EUR">EUR · 欧元</option>
            <option value="CNY">CNY · 人民币</option>
            <option value="JPY">JPY · 日元</option>
          </select>
        </label>
        <label class="cost-field" for="cost-input-price">
          <span>输入单价</span>
          <span class="cost-input-wrap">
            <input id="cost-input-price" name="input_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-output-price">
          <span>输出单价</span>
          <span class="cost-input-wrap">
            <input id="cost-output-price" name="output_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-read-price">
          <span>缓存读取单价</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-read-price" name="cache_read_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-write-price">
          <span>缓存写入单价</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-write-price" name="cache_write_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
      </div>
    </fieldset>

    <fieldset class="cost-fieldset">
      <legend>3. 充值与用量规模</legend>
      <div class="cost-fields">
        <label class="cost-field" for="cost-minimum-charge">
          <span>最低充值金额</span>
          <span class="cost-input-wrap">
            <input id="cost-minimum-charge" name="minimum_charge" type="number" min="0" step="0.01" inputmode="decimal" autocomplete="off">
            <span aria-hidden="true">实付</span>
          </span>
        </label>
        <label class="cost-field" for="cost-credit-amount">
          <span>实际到账额度</span>
          <span class="cost-input-wrap">
            <input id="cost-credit-amount" name="credit_amount" type="number" min="0" step="0.01" inputmode="decimal" autocomplete="off">
            <span aria-hidden="true">到账</span>
          </span>
        </label>
        <label class="cost-field" for="cost-monthly-requests">
          <span>每月同类请求次数</span>
          <span class="cost-input-wrap">
            <input id="cost-monthly-requests" name="monthly_requests" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" value="">
            <span aria-hidden="true">次</span>
          </span>
        </label>
      </div>
      <p class="cost-field-note">每月请求次数留空时按一次计算。充值和到账金额使用上方选择货币，不进行汇率换算。</p>
    </fieldset>
  </form>

  <div class="cost-results" data-cost-results aria-live="polite" aria-atomic="false">
    <div class="cost-result">
      <span>单次请求成本</span>
      <strong data-cost-result="request-cost">—</strong>
    </div>
    <div class="cost-result">
      <span>每月总成本</span>
      <strong data-cost-result="monthly-cost">—</strong>
    </div>
    <div class="cost-result">
      <span>有效每百万 Token 成本</span>
      <strong data-cost-result="effective-per-million">—</strong>
    </div>
    <div class="cost-result">
      <span>到账额度折算率</span>
      <strong data-cost-result="credit-rate">—</strong>
    </div>
    <div class="cost-result">
      <span>每月最低充值次数</span>
      <strong data-cost-result="topup-count">—</strong>
    </div>
  </div>
  <p class="cost-status" data-cost-status role="status">填完八项必填字段后即可计算。输入只在你的浏览器中处理。</p>
</section>

文中以 [`nuoapi.net`](https://nuoapi.net) 作为地址示例。模型 ID、分组、倍率和可用性会变化，请以[模型广场](https://nuoapi.net/model-plaza)和控制台实时显示为准。公开价格表不能替代你账户实际生效的价格。

## 1. 先统一计价单位

比较前先把候选服务换算到同一口径：

- 货币和汇率日期。
- 含税还是未税。
- 按 1K、1M 还是站内额度计费。
- 输入、输出、缓存读取和缓存写入是否分开。
- 图片、音频、搜索、工具和最低单次计费。

```text
每百万 Token 价格 = 每千 Token 价格 * 1,000
每百万 Token 价格 = 每 Token 价格 * 1,000,000
```

## 2. 单次请求公式

```text
单次成本 =
  输入 Token / 1,000,000 * 输入单价
  + 输出 Token / 1,000,000 * 输出单价
  + 缓存读取 Token / 1,000,000 * 缓存读取单价
  + 缓存写入 Token / 1,000,000 * 缓存写入单价
  + 图片、音频、搜索和工具附加费
```

界面里看到的输入不一定等于实际计费输入。网关可能附加系统提示、工具结果、历史消息或重试内容。对账时要区分固定前缀、会话历史和业务正文。

## 3. 算例

假设输入 800,000 Token、缓存读取 200,000 Token、输出 300,000 Token，单价分别为每百万 2、0.50 和 8：

```text
输入：    800,000 / 1,000,000 * 2.00 = 1.60
缓存读取：200,000 / 1,000,000 * 0.50 = 0.10
输出：    300,000 / 1,000,000 * 8.00 = 2.40
单次合计：1.60 + 0.10 + 2.40 = 4.10
```

这只是算术示例，不是报价。缓存 Token 是否同时计入普通输入，必须按服务的计费说明分别核对。

## 4. 长上下文会放大成本

多轮对话如果重复发送完整历史，每轮输入都会增长：

```text
累计输入 =
  系统提示
  + 保留的历史消息
  + 文档和工具结果
  + 本轮新消息
```

上下文窗口很大不代表使用它很便宜。要分别记录每轮输入长度、缓存命中、摘要压缩和重试次数。

## 5. 最低充值与到账额度

```text
额度折算率 = 实付金额 / 实际到账额度
```

支付 100、到账 100 时折算率是 1.0；支付 100、到账 80 时是 1.25。还要记录额度有效期、可用分组、退款条件和无法使用的余额。

## 6. 月度总成本

```text
月度总成本 =
  单次成本 * 请求次数
  + 重试和失败请求费用
  + 固定费用
  + 未使用但被最低充值占用的余额
```

至少模拟轻度、团队和长上下文三种场景，不要只用一个平均请求估算。

## 7. 价格差异要回到证据

价差很大时，先核对模型 ID、上下文窗口、量化、分组、区域、缓存、限速和支持级别，再判断是否值得购买。模型身份只能用[验证方法](MODEL_VERIFICATION_METHODS.md)得出 **匹配 / 不匹配 / 证据不足** 三态结论。

```bash
python examples/model_verify.py --selftest
python examples/model_verify.py
```

第二条命令默认只打印计划，不会发送计费请求。

## 8. 检查清单

1. 所有价格使用相同货币、单位和日期。
2. 输入、输出、缓存读取、缓存写入分开记录。
3. 长上下文、重试和系统提示计入输入。
4. 最低充值、到账额度、有效期和退款条件已记录。
5. 公开价格与账户实际价格分别保存。
6. 用一次真实账单复核计算结果。

## 相关页面

- [模型真伪与防掺水方法](MODEL_VERIFICATION_METHODS.md)
- [Codex Reconnecting 排查](Codex-一直Reconnecting-2026-10-18.md)
- [Claude Code 404 排查](Claude-Code-不要加v1-2026-10-18.md)

## 免责声明

本文是独立技术资料，不提供也不转售 API 服务，与 OpenAI、Anthropic、Google、xAI、ByteDance、DeepSeek、MiniMax 等厂商没有官方关联。产品名称归各自所有者。使用前请核对最新条款、隐私政策、价格和可用性。
