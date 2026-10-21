<!-- seo-meta
  title: Precio por 1M de tokens de una API de IA: cómo comparar
  description: Calcula el coste real por 1M de tokens con entrada, salida, caché, contexto, recargas mínimas, precio efectivo e importes de facturas de ejemplo.
-->

# Cómo comparar el precio por 1M de tokens de una API de IA

El precio por 1M de tokens es una unidad útil, pero no es el coste final. Para comparar una API de IA, calcula por separado la entrada, la salida, la escritura y lectura de caché, el contexto enviado en cada solicitud, la recarga mínima y el crédito que realmente recibes.

> **Acción principal**: introduce tu propio uso y tus precios por 1M de tokens para ver el coste por solicitud, el coste mensual y el efecto de la recarga mínima.

<section class="cost-calculator" data-cost-calculator aria-labelledby="cost-calculator-title">
  <div class="cost-calculator-head">
    <p class="cost-kicker">Calculadora local</p>
    <h2 id="cost-calculator-title">Calcula el coste real antes de recargar</h2>
    <p id="cost-calculator-help">Los ocho campos de uso y precio son obligatorios. La recarga y el volumen mensual son opcionales. Los cálculos se ejecutan en tu navegador y no envían datos.</p>
  </div>
  <form class="cost-form" data-cost-form novalidate
    aria-describedby="cost-calculator-help"
    data-msg-ready="Cálculo local completado. No se enviaron datos."
    data-msg-missing="Completa los ocho campos obligatorios de uso y precio para calcular."
    data-msg-invalid="Revisa los campos marcados: usa cero o un número positivo; el volumen mensual debe ser un entero igual o mayor que cero.">
    <fieldset class="cost-fieldset">
      <legend>1. Uso de una solicitud</legend>
      <div class="cost-fields">
        <label class="cost-field" for="cost-input-tokens">
          <span>Tokens de entrada facturados</span>
          <span class="cost-input-wrap">
            <input id="cost-input-tokens" name="input_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-output-tokens">
          <span>Tokens de salida</span>
          <span class="cost-input-wrap">
            <input id="cost-output-tokens" name="output_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-read-tokens">
          <span>Tokens leídos desde caché</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-read-tokens" name="cache_read_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-write-tokens">
          <span>Tokens escritos en caché</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-write-tokens" name="cache_write_tokens" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" required>
            <span aria-hidden="true">tokens</span>
          </span>
        </label>
      </div>
    </fieldset>

    <fieldset class="cost-fieldset">
      <legend>2. Precios por 1M de tokens</legend>
      <div class="cost-fields">
        <label class="cost-field cost-field--wide" for="cost-currency">
          <span>Moneda de visualización</span>
          <select id="cost-currency" name="currency">
            <option value="USD">USD · dólar estadounidense</option>
            <option value="EUR">EUR · euro</option>
            <option value="CNY">CNY · yuan chino</option>
            <option value="JPY">JPY · yen japonés</option>
          </select>
        </label>
        <label class="cost-field" for="cost-input-price">
          <span>Precio de entrada</span>
          <span class="cost-input-wrap">
            <input id="cost-input-price" name="input_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-output-price">
          <span>Precio de salida</span>
          <span class="cost-input-wrap">
            <input id="cost-output-price" name="output_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-read-price">
          <span>Precio de lectura de caché</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-read-price" name="cache_read_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
        <label class="cost-field" for="cost-cache-write-price">
          <span>Precio de escritura de caché</span>
          <span class="cost-input-wrap">
            <input id="cost-cache-write-price" name="cache_write_price" type="number" min="0" step="0.000001" inputmode="decimal" autocomplete="off" required>
            <span aria-hidden="true">/ 1M</span>
          </span>
        </label>
      </div>
    </fieldset>

    <fieldset class="cost-fieldset">
      <legend>3. Recarga y volumen</legend>
      <div class="cost-fields">
        <label class="cost-field" for="cost-minimum-charge">
          <span>Importe mínimo de recarga</span>
          <span class="cost-input-wrap">
            <input id="cost-minimum-charge" name="minimum_charge" type="number" min="0" step="0.01" inputmode="decimal" autocomplete="off">
            <span aria-hidden="true">pagado</span>
          </span>
        </label>
        <label class="cost-field" for="cost-credit-amount">
          <span>Crédito que recibes</span>
          <span class="cost-input-wrap">
            <input id="cost-credit-amount" name="credit_amount" type="number" min="0" step="0.01" inputmode="decimal" autocomplete="off">
            <span aria-hidden="true">recibido</span>
          </span>
        </label>
        <label class="cost-field" for="cost-monthly-requests">
          <span>Solicitudes similares al mes</span>
          <span class="cost-input-wrap">
            <input id="cost-monthly-requests" name="monthly_requests" type="number" min="0" step="1" inputmode="numeric" autocomplete="off" value="">
            <span aria-hidden="true">veces</span>
          </span>
        </label>
      </div>
      <p class="cost-field-note">Si dejas vacío el volumen mensual, se calcula una sola solicitud. Los importes de recarga usan la misma moneda elegida arriba.</p>
    </fieldset>
  </form>

  <div class="cost-results" data-cost-results aria-live="polite" aria-atomic="false">
    <div class="cost-result">
      <span>Coste por solicitud</span>
      <strong data-cost-result="request-cost">—</strong>
    </div>
    <div class="cost-result">
      <span>Coste mensual</span>
      <strong data-cost-result="monthly-cost">—</strong>
    </div>
    <div class="cost-result">
      <span>Coste efectivo por 1M tokens</span>
      <strong data-cost-result="effective-per-million">—</strong>
    </div>
    <div class="cost-result">
      <span>Coste real por unidad de saldo</span>
      <strong data-cost-result="credit-rate">—</strong>
    </div>
    <div class="cost-result">
      <span>Recargas mínimas al mes</span>
      <strong data-cost-result="topup-count">—</strong>
    </div>
  </div>
  <p class="cost-status" data-cost-status role="status">Completa los ocho campos obligatorios para calcular. Todo se procesa en tu navegador.</p>
</section>

La dirección de ejemplo es [`nuoapi.net`](https://nuoapi.net). Los identificadores, grupos, tarifas y disponibilidad cambian, así que confirma los valores actuales en la [plaza de modelos](https://nuoapi.net/model-plaza) y en la consola. Una tabla pública no sustituye la tarifa aplicada a tu cuenta.

## 1. Unifica la unidad antes de comparar

Antes de ordenar precios, convierte todos los valores a la misma base:

- Moneda y tipo de cambio, con fecha.
- Impuestos incluidos o excluidos.
- Precio por 1K, 1M o una unidad interna de crédito.
- Entrada, salida, caché de lectura y caché de escritura.
- Imagen, audio, búsqueda, herramientas y otros cargos.
- Redondeo mínimo por solicitud.

No compares un precio por 1K tokens con otro por 1M sin convertir. Tampoco compares un precio promocional limitado a un grupo con una tarifa general.

```text
precio por 1M = precio por 1K * 1,000
precio por 1M = precio por token * 1,000,000
```

## 2. Fórmula del coste por solicitud

```text
coste de una solicitud =
  tokens_entrada / 1,000,000 * precio_entrada
  + tokens_salida / 1,000,000 * precio_salida
  + unidades_cache_escritura * precio_cache_escritura
  + unidades_cache_lectura * precio_cache_lectura
  + imagen_audio_busqueda_herramientas
```

La entrada no siempre es igual al texto visible en la interfaz. Un gateway puede añadir instrucciones de sistema, metadatos, resultados de herramientas o historial. Compara los tokens facturados con los que calculó tu aplicación. Si no coinciden, separa prefijo fijo, historial, reintentos y contenido de herramientas.

La caché también debe separarse. Una lectura de caché barata no elimina el coste de crear esa caché, y algunas plataformas cobran la lectura. Registra ambos conceptos y su duración de conservación.

## 3. Ejemplo aritmético

Supón estos precios ficticios para una comparación:

| Concepto | Precio de ejemplo |
|---|---:|
| Entrada | $2 por 1M tokens |
| Salida | $8 por 1M tokens |
| Lectura de caché | $0.50 por 1M tokens |

Una solicitud con 1,000,000 de tokens de entrada, 300,000 de salida y 200,000 leídos desde caché se calcula así:

```text
entrada visible: 800,000 / 1,000,000 * 2.00 = 1.60
caché leída:     200,000 / 1,000,000 * 0.50 = 0.10
salida:          300,000 / 1,000,000 * 8.00 = 2.40
total de ejemplo: 1.60 + 0.10 + 2.40 = 4.10
```

El ejemplo solo muestra la aritmética. No es una oferta ni una tarifa vigente. Comprueba cuántos tokens de entrada se facturan realmente y si los tokens leídos desde caché también aparecen en la entrada total.

## 4. Coste con contexto largo

Una conversación larga puede multiplicar el coste aunque el último mensaje sea corto. Para cada ronda, calcula:

```text
entrada acumulada =
  instrucciones del sistema
  + historial conservado
  + documento o resultados de herramientas
  + mensaje nuevo
```

Si el cliente reenvía todo el historial, el coste crece con la conversación. Si la plataforma recorta, resume o usa caché, debes comprobar qué parte se factura y qué parte se reutiliza. Una ventana de contexto grande no significa que usarla tenga el mismo precio que una solicitud breve.

## 5. Precio efectivo y recarga mínima

El importe mínimo de recarga puede dominar el primer mes:

```text
precio efectivo del crédito = importe pagado / crédito recibido
```

Si pagas 100 y recibes 100 de crédito, el factor es 1.0. Si pagas 100 y recibes 80, el factor es 1.25. Añade caducidad, restricciones de grupo, imposibilidad de reembolso y saldo que no puedes usar.

También distingue entre:

- Precio público del catálogo.
- Precio del grupo asignado a tu clave.
- Precio después de descuentos o crédito promocional.
- Importe final de una factura de prueba.

## 6. Simulador mensual

Crea al menos tres escenarios:

| Escenario | Solicitudes al mes | Entrada media | Salida media | Caché |
|---|---:|---:|---:|---:|
| Uso ligero | 500 | 2,000 | 500 | 10% |
| Uso de equipo | 10,000 | 6,000 | 1,000 | 30% |
| Contexto largo | 2,000 | 40,000 | 2,000 | 50% |

Para cada escenario:

```text
coste mensual =
  Σ coste de solicitudes
  + reintentos facturados
  + funciones adicionales
  + cuota fija
  + saldo obligatorio no utilizado
```

No uses solo el promedio. Modela una cola de solicitudes largas, un pico de reintentos y un mes con poca actividad. El saldo mínimo puede pesar más en el mes de baja actividad que en el de alta.

## 7. Qué hacer con la diferencia de precio

Una diferencia grande exige más evidencia, no una conclusión automática. Revisa si cambian el modelo exacto, la ventana de contexto, la cuantización, el grupo, la región, la caché, el límite de velocidad o el nivel de soporte. Después verifica la identidad del modelo con la [metodología de verificación](MODEL_VERIFICATION_METHODS.md); el resultado solo puede ser **coincidencia / discrepancia / evidencia insuficiente**.

Antes de contratar, ejecuta la comprobación local sin gasto:

```bash
python examples/model_verify.py --selftest
python examples/model_verify.py
```

Sin `--run`, el segundo comando solo muestra el plan y los tokens estimados.

## 8. Lista de comprobación

1. Todos los precios usan la misma moneda y unidad.
2. Entrada, salida y caché están separadas.
3. El contexto acumulado aparece en el escenario.
4. La recarga mínima y el crédito recibido están registrados.
5. El saldo no utilizado y su vencimiento están incluidos.
6. El precio público se compara con una factura de prueba.
7. La fuente y la fecha de comprobación están visibles.

## Páginas relacionadas

- [Metodología de verificación de modelos](MODEL_VERIFICATION_METHODS.md)
- [Codex keeps reconnecting](Codex-一直Reconnecting-2026-10-18.en.md)
- [LLM gateway checklist](llm-gateway-checklist.en.md)

## Aviso legal

Este documento es material técnico independiente. No ofrece ni revende acceso a API y no tiene relación oficial con OpenAI, Anthropic, Google, xAI, ByteDance, DeepSeek, MiniMax ni otros proveedores. Los nombres de productos pertenecen a sus propietarios. Confirma los términos, la privacidad, los precios y la disponibilidad antes de usar un servicio.
