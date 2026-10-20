<!-- seo-meta
  title: Claude Code 404: Base URL must not include /v1
  description: Claude Code constructs /v1/messages itself. Set ANTHROPIC_BASE_URL to the root address, use ANTHROPIC_AUTH_TOKEN, then open a fresh terminal.
-->

# Claude Code 404: do not add /v1

> **Legal and trademark notice**
>
> 1. This is an independent configuration guide. It is not affiliated with Anthropic or any model vendor. Names are used only to explain protocol compatibility.
> 2. This repository does not provide or resell API access.
> 3. Check the provider's terms, privacy policy, pricing, and availability before use.

The address fixture is [`nuoapi.net`](https://nuoapi.net). Copy the current model ID from your group and confirm it in the [model plaza](https://nuoapi.net/model-plaza).

## Symptom

The request returns plain-text `404 page not found` instead of `401`. A common cause is adding `/v1` to `ANTHROPIC_BASE_URL`; Claude Code then sends `/v1/messages` to the wrong path.

The variable name matters too. Claude Code uses `ANTHROPIC_AUTH_TOKEN`, not `ANTHROPIC_API_KEY`.

## One configuration

```text
ANTHROPIC_BASE_URL=https://nuoapi.net
ANTHROPIC_AUTH_TOKEN=YOUR_NUOAPI_API_KEY
```

For the current PowerShell terminal:

```powershell
$env:ANTHROPIC_BASE_URL = "https://nuoapi.net"
$env:ANTHROPIC_AUTH_TOKEN = "YOUR_NUOAPI_API_KEY"
```

Use the platform environment-variable UI or an equivalent persistent setting when you want it to survive terminal restarts. Existing processes do not receive newly changed variables.

## Verification

Open a new terminal, start Claude Code, and send one short fixed prompt. Confirm the model and timestamp in the console. If the value still ends in `/v1`, the old process is probably still using the previous environment.

See the [third-party tool guide](接入第三方工具教程-2026-09-26.md#51-claude-code-与-claude-类工具) for other operating systems and the [FAQ](../FAQ.md#2-claude-code-的-base-url-要不要加-v1) for the short version.
