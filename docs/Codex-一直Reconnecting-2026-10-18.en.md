<!-- seo-meta
  title: Codex keeps reconnecting: disable WebSocket in config
  description: If Codex repeatedly reconnects or logs wss:// for /v1/responses, use the HTTP Responses wire API, set supports_websockets false, and fully restart.
-->

# Codex keeps reconnecting: disable WebSocket

> **Legal and trademark notice**
>
> 1. This is an independent configuration guide. It is not affiliated with OpenAI or any model vendor. Names are used only to explain protocol compatibility.
> 2. This repository does not provide or resell API access.
> 3. Check the provider's terms, privacy policy, pricing, and availability before use.

The address fixture is [`nuoapi.net`](https://nuoapi.net). Copy a current model ID from your group and confirm it in the [model plaza](https://nuoapi.net/model-plaza).

## Symptom

Codex keeps showing `Reconnecting`, or its log contains one of these:

- `wss://nuoapi.net/v1/responses`
- `WebSocket connection ... failed`
- repeated `connecting to wss://...`

The client is trying WebSocket while the route needs HTTP Responses. Setting a proxy environment variable does not disable that attempt.

## One configuration

In `~/.codex/config.toml` on macOS/Linux, or `%USERPROFILE%\.codex\config.toml` on Windows:

```toml
model_provider = "nuoapi"
model = "MODEL_NAME_FROM_MODEL_PLAZA"

[model_providers.nuoapi]
name = "nuoapi"
base_url = "https://nuoapi.net/v1"
wire_api = "responses"
requires_openai_auth = true
supports_websockets = false
```

Keep the API key out of the TOML file. Put the placeholder below in the adjacent `auth.json` and replace it locally:

```json
{"OPENAI_API_KEY":"YOUR_NUOAPI_API_KEY"}
```

The Base URL stops at `/v1`; do not append `/responses` or another `/v1`.

## Verification

Fully exit Codex, reopen it, send one short fixed prompt, and check the console for the model and timestamp. The log should no longer contain `wss://nuoapi.net/v1/responses`.

If it still reconnects, verify the file path and confirm the process restarted. See [FAQ section 11](../FAQ.md#11-codex-读取不到配置怎么办) and the [setup guide](接入第三方工具教程-2026-09-26.md#52-codex-cli-与其他-responses-cli).
