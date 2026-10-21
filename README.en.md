<!-- seo-meta
  title: NuoAPI starter: Codex, Claude Code, and Gemini API setup
  description: Connect Codex, Claude Code, and Gemini CLI through an AI API gateway, troubleshoot errors, and run dry-run model authenticity checks before paying.
-->

# [NuoAPI](https://nuoapi.net/model-plaza) Starter and Model Verification Toolkit

> **Legal and trademark notice**
>
> 1. This is an independent technical research project, configuration scaffold, and diagnostic test suite maintained by an individual developer. It does not provide or resell API access. It has no official affiliation, investment, sponsorship, or partnership relationship with OpenAI, Anthropic, Google, xAI, ByteDance, DeepSeek, MiniMax, or any other model vendor.
> 2. Product and company names are trademarks of their respective owners. They are used only to explain protocol compatibility and configuration.
> 3. All examples contain placeholders only (`YOUR_NUOAPI_API_KEY`). This repository does not collect anyone's API key. Review each provider's terms, privacy policy, pricing, and availability before use.

This repository helps you connect Codex, Claude Code, Gemini CLI, and other compatible clients to a third-party AI gateway. It also gives you reproducible checks for a narrower question: **did the paid response come from the model claimed by the service?** Read the [model verification methodology](docs/MODEL_VERIFICATION_METHODS.md) before turning one observation into a conclusion.

Documentation site: <a href="https://hjm-al.github.io/nuoapi-tutorial/en/">Open the English guide</a>.

[简体中文](README.md) · English · [日本語](README.ja.md) · [Español](README.es.md) · [繁體中文](README.zh-Hant.md)

## Verification paths by language

- [English: LLM gateway checklist](docs/llm-gateway-checklist.en.md) for model consistency, data residency, BYOK, audit logs, and failover.
- [日本語: minimum charge and pricing](docs/minimum-charge-and-pricing.ja.md) for top-up thresholds and cost conversion.
- [English: cost per 1M tokens](docs/cost-per-1m-tokens.en.md) for input, output, cache, minimum top-up, and a local cost calculator.

## Common errors at a glance

### Gemini CLI says `platform is not gemini`?

Set `GOOGLE_GEMINI_BASE_URL` to the root URL `https://nuoapi.net`; do not append `/v1` or `/v1beta`, and copy the model ID from the current group exactly. See the [Gemini CLI troubleshooting guide](docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.en.md).

### What if Codex keeps reconnecting?

Set the provider's `wire_api` to `responses` and `supports_websockets` to `false`, then fully quit and restart Codex. See the [Codex reconnecting guide](docs/Codex-一直Reconnecting-2026-10-18.en.md).

### Claude Code returns 404. Should I add `/v1`?

No. Set `ANTHROPIC_BASE_URL` to the root URL `https://nuoapi.net`, put the key in `ANTHROPIC_AUTH_TOKEN`, and open a new terminal. See the [Claude Code 404 guide](docs/Claude-Code-不要加v1-2026-10-18.en.md).

### What should I check first for `401 invalid_api_key`?

Confirm that the current client process sees a key, that the variable name matches the client, and that there is no surrounding whitespace; do not print the full key. See the [401 troubleshooting guide](docs/401-invalid-api-key.md).

### Why is `400 invalid_request_error` so generic?

Read the `message` in the response body. Common causes are a duplicated `/v1`, a protocol or model mismatch, a missing required field, or mixed streaming parameters. See the [400 troubleshooting guide](docs/400-invalid-request-error.md).

### Does `404 model_not_found` mean the gateway is down?

Usually not. The request reached the gateway, but the current key's group does not contain that exact model ID. Copy the ID from `/v1/models` or the model marketplace. See the [model name troubleshooting guide](docs/model_not_found.md).

## Start without spending

The first command validates the probe locally. The second prints a request plan without making a billed model call.

```bash
python examples/model_verify.py --selftest
python examples/model_verify.py
```

No `--run` flag means no paid model request. The probe reports one of three outcomes: match, mismatch, or insufficient evidence.

## Base URL quick check

| Client | Base URL | Common mistake |
|---|---|---|
| Codex | `https://nuoapi.net/v1` with `wire_api = "responses"` | Leaving WebSocket enabled |
| Claude Code | `https://nuoapi.net` | Adding `/v1` twice |
| Gemini CLI | `https://nuoapi.net` | Adding `/v1beta` |

Before testing, create a dedicated key from [account registration](https://nuoapi.net/register) and [key management](https://nuoapi.net/keys). The gateway used as an address fixture is nuoapi.net. Model IDs, groups, rates, and availability change, so copy current values from the model plaza and confirm them in the console.

## How verdicts work

- **Match**: the observed evidence is consistent with the claimed model and protocol.
- **Mismatch**: discriminating evidence contradicts the claim.
- **Insufficient evidence**: the sample, fields, or request window cannot support a verdict.

Model self-description, response speed, or one public puzzle does not establish authenticity. Keep the evidence window and the exact endpoint with any result.

## Safety

Run scripts locally with your own test key and revoke it when finished. Printed keys are masked. No UTM parameters, affiliate redirects, or self-hosted tracking are used by this project.

This repository does not provide or resell API access and is not an investment or purchase recommendation.
