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

[简体中文](README.md) · English · [日本語](README.ja.md) · [Español](README.es.md) · [繁體中文](README.zh-Hant.md)

## Verification paths by language

- [English: LLM gateway checklist](docs/llm-gateway-checklist.en.md) for model consistency, data residency, BYOK, audit logs, and failover.
- [日本語: minimum charge and pricing](docs/minimum-charge-and-pricing.ja.md) for top-up thresholds and cost conversion.
- [English: cost per 1M tokens](docs/cost-per-1m-tokens.en.md) for input, output, cache, minimum top-up, and a local cost calculator.

## Common errors at a glance

- [Gemini CLI: platform is not gemini](docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.en.md)
- [Codex keeps reconnecting](docs/Codex-一直Reconnecting-2026-10-18.en.md)
- [Claude Code 404: do not add /v1](docs/Claude-Code-不要加v1-2026-10-18.en.md)
- [401 invalid_api_key](docs/401-invalid-api-key.md)
- [400 invalid_request_error](docs/400-invalid-request-error.md)
- [404 model_not_found](docs/model_not_found.md)

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

Use the gateway as an address fixture: [`nuoapi.net`](https://nuoapi.net). Model IDs, groups, rates, and availability change, so copy current values from the [model plaza](https://nuoapi.net/model-plaza) and confirm them in the console.

## How verdicts work

- **Match**: the observed evidence is consistent with the claimed model and protocol.
- **Mismatch**: discriminating evidence contradicts the claim.
- **Insufficient evidence**: the sample, fields, or request window cannot support a verdict.

Model self-description, response speed, or one public puzzle does not establish authenticity. Keep the evidence window and the exact endpoint with any result.

## Safety

Run scripts locally with your own test key and revoke it when finished. Printed keys are masked. No UTM parameters, affiliate redirects, or self-hosted tracking are used by this project.

This repository does not provide or resell API access and is not an investment or purchase recommendation.
