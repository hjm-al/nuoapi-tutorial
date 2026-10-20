<!-- seo-meta
  title: Gemini CLI platform is not gemini: use the root Base URL
  description: A 400 platform is not gemini or a silent Gemini CLI usually means the wrong protocol path. Set the root Base URL, keep model IDs exact, and restart.
-->

# Gemini CLI: platform is not gemini

> **Legal and trademark notice**
>
> 1. This is an independent configuration guide. It is not affiliated with Google, OpenAI, Anthropic, or any model vendor. Names are used only to explain protocol compatibility.
> 2. This repository does not provide or resell API access.
> 3. Check the provider's terms, privacy policy, pricing, and availability before use.

The address fixture is [`nuoapi.net`](https://nuoapi.net). Copy the current model ID from your group and confirm it in the [model plaza](https://nuoapi.net/model-plaza).

## Symptom

- `400 platform is not gemini`: the request did not enter the Gemini protocol route.
- Gemini CLI never responds, or reports an unexpected path: `GOOGLE_GEMINI_BASE_URL` may contain `/v1beta`.

`API_KEY_INVALID` or `API key not valid` is a credential problem, not the same failure. The protocol background is in the [API protocol guide](AI模型API协议科普-2026-10-12.md#6-gemini-原生协议).

## One configuration

In `~/.gemini/.env`:

```env
GOOGLE_GEMINI_BASE_URL=https://nuoapi.net
GEMINI_API_KEY=YOUR_NUOAPI_API_KEY
GEMINI_MODEL=MODEL_NAME_FROM_MODEL_PLAZA
```

Do not append `/v1` or `/v1beta` to the Base URL. Gemini CLI adds its own protocol path. The model ID must match the current group exactly, including any date suffix.

## Verification

Exit Gemini CLI, open a new terminal, and start it again. Send one short fixed prompt, then check the console for the same model and timestamp. The longer setup reference is in the [third-party tool guide](接入第三方工具教程-2026-09-26.md#53-gemini-cli).

If the response says `API_KEY_INVALID`, go to the [401 guide](401-invalid-api-key.md) instead of changing protocol routes.
