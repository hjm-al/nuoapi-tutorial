<!-- seo-meta
  title: NuoAPI: configuración de Codex, Claude Code y Gemini
  description: Configura Codex, ejecuta comprobaciones sin gasto y distingue entre coincidencia, discrepancia y evidencia insuficiente para verificar un modelo.
-->

# [NuoAPI](https://nuoapi.net/model-plaza) Starter y kit de verificación de modelos

> **Aviso legal y de marcas**
>
> 1. Este es un proyecto técnico independiente, un conjunto de configuración y una suite de diagnóstico mantenidos por un desarrollador individual. No ofrece ni revende acceso a API. No mantiene afiliación, inversión, patrocinio ni colaboración oficial con OpenAI, Anthropic, Google, xAI, ByteDance, DeepSeek, MiniMax ni otros proveedores de modelos.
> 2. Los nombres de productos y empresas pertenecen a sus respectivos propietarios. Solo se usan para explicar compatibilidad de protocolos y configuración.
> 3. Todos los ejemplos usan únicamente marcadores de posición (`YOUR_NUOAPI_API_KEY`). Este repositorio no recopila claves de API. Antes de usar un servicio, revisa sus términos, política de privacidad, precios y disponibilidad.

Este repositorio ayuda a conectar Codex, Claude Code, Gemini CLI y otros clientes compatibles con una puerta de enlace de IA. También ofrece comprobaciones reproducibles para una pregunta más concreta: **¿la respuesta facturada proviene del modelo declarado por el servicio?**

[简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md) · Español · [繁體中文](README.zh-Hant.md)

## Rutas de verificación por idioma

- [English: LLM Gateway Checklist](docs/llm-gateway-checklist.en.md): consistencia del modelo, residencia de datos, BYOK, auditoría y conmutación por error.
- [日本語: 最低チャージと料金](docs/minimum-charge-and-pricing.ja.md): importe mínimo, conversión de crédito, precio oficial y fecha de comprobación.
- [Español: precio por 1M de tokens](docs/cost-per-1m-tokens.es.md): calculadora local de entrada, salida, caché, recarga mínima y coste efectivo.
- [Metodología de verificación](docs/MODEL_VERIFICATION_METHODS.md): el resultado solo puede ser **coincidencia / discrepancia / evidencia insuficiente**.

## Empieza sin gastar

El primer comando valida el sondeo en local. El segundo muestra un plan de solicitud sin hacer una llamada facturable.

```bash
python examples/model_verify.py --selftest
python examples/model_verify.py
```

Sin `--run` no se envía una solicitud facturable al modelo. El sondeo solo devuelve uno de tres estados: coincidencia, discrepancia o evidencia insuficiente. Lee la [metodología](docs/MODEL_VERIFICATION_METHODS.md) antes de convertir una observación aislada en una conclusión.

## Errores frecuentes

- [Gemini CLI: platform is not gemini](docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.en.md)
- [Codex keeps reconnecting](docs/Codex-一直Reconnecting-2026-10-18.en.md)
- [Claude Code 404: do not add /v1](docs/Claude-Code-不要加v1-2026-10-18.en.md)
- [401 invalid_api_key](docs/401-invalid-api-key.md)
- [400 invalid_request_error](docs/400-invalid-request-error.md)
- [404 model_not_found](docs/model_not_found.md)

## Comprobación rápida de Base URL

| Cliente | Base URL | Error habitual |
|---|---|---|
| Codex | `https://nuoapi.net/v1` con `wire_api = "responses"` | Dejar WebSocket activado |
| Claude Code | `https://nuoapi.net` | Añadir `/v1` dos veces |
| Gemini CLI | `https://nuoapi.net` | Añadir `/v1beta` |

La dirección de ejemplo es [`nuoapi.net`](https://nuoapi.net). Los identificadores de modelo, grupos, tarifas y disponibilidad cambian; copia los valores actuales desde la [plaza de modelos](https://nuoapi.net/model-plaza) y confírmalos en la consola.

## Cómo interpretar el resultado

- **Coincidencia**: la evidencia observada es compatible con el modelo y el protocolo declarados.
- **Discrepancia**: evidencia con capacidad discriminante contradice la declaración.
- **Evidencia insuficiente**: la muestra, los campos o la ventana de observación no permiten concluir.

La descripción que hace el modelo de sí mismo, la velocidad de respuesta o un acertijo público no demuestran autenticidad. Conserva la ventana de evidencia y el endpoint exacto junto con cada resultado.

## Seguridad

Ejecuta los scripts en local con una clave de prueba propia y revócala al terminar. Las claves impresas se enmascaran. Este proyecto no usa UTM, redirecciones de afiliación ni seguimiento propio.

Este repositorio no ofrece ni revende acceso a API y no constituye una recomendación de inversión o compra.
