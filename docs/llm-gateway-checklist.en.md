<!-- seo-meta
  title: LLM Gateway Checklist: Model Consistency and Residency
  description: Evaluate an LLM gateway for model consistency, data residency, BYOK, audit logs, failover, cost controls, and verifiable operational evidence.
-->

# LLM Gateway Checklist: Model Consistency, Data Residency and Failover

An `OpenAI-compatible` endpoint is a protocol claim, not proof of model identity, data residency, or security certification. Use this checklist to separate what a gateway documents from what your organization can independently verify.

> **Primary action**: before procurement, require one written evidence packet that maps every requested model to its serving provider, protocol path, data boundary, logging policy, failover rule, price unit, and review date.

The example address is [`nuoapi.net`](https://nuoapi.net). Model IDs, groups, rates, and availability change, so confirm current values in the [model plaza](https://nuoapi.net/model-plaza) and your console. Read the [model verification methodology](MODEL_VERIFICATION_METHODS.md) before treating a responsive endpoint as proof that the claimed model is being served.

## 1. Start with the decision, not the logo

Write down the decision this gateway must support:

| Decision | Evidence that matters | Evidence that is not enough |
|---|---|---|
| Which model answers the request? | Serving provider, exact model ID, protocol path, response fields, repeatable distribution checks | A model says its own name |
| Where does application data travel? | Hosted regions, subprocessors, retention periods, cache behavior, deletion path | A badge on a marketing page |
| Can the service fail over? | Documented failover order, observable error codes, model/region changes in logs | A status page alone |
| What will it cost? | Input, output, cache, image, and minimum top-up rules | One headline price per token |
| Can an administrator investigate an incident? | Request IDs, timestamps, policy version, audit retention, support route | Screenshots without raw records |

If the vendor cannot name the accountable operator for each row, stop treating the answer as procurement evidence.

## 2. Model consistency

Protocol compatibility means a client can send a request in a familiar shape. It does not establish which model produced the response.

Ask for all of the following:

1. The exact model ID accepted by the route, including preview or date suffixes.
2. The upstream provider and product family for that ID.
3. The protocol route used upstream and whether conversion occurs.
4. The billing unit and cache semantics, including which tokens are charged.
5. Whether routing can change by group, account pool, time, region, or fallback rule.
6. The notice process before a model alias is repointed.

Then test a representative request through the same route your application uses. Keep raw response headers, response body, UTC timestamp, model ID, request ID, and price record. A 200 response proves reachability. It does not prove model identity.

Use the [verification workflow](MODEL_VERIFICATION_METHODS.md) to classify the result as **match / mismatch / insufficient evidence**. Start with the offline self-test:

```bash
python examples/model_verify.py --selftest
python examples/model_verify.py
```

The second command prints a request plan only. A billed request requires an explicit `--run`.

## 3. Data residency and governance

Residency is a property of the complete path, not only the first hostname. Ask where request content, response content, logs, crash traces, support exports, and backups are stored and processed.

| Control | Minimum evidence to request |
|---|---|
| Region | Named processing and storage regions for each model and service component |
| Subprocessors | Current list, role, location, change notice, and contractual flow-down |
| Retention | Default and configurable periods for prompts, completions, metadata, and abuse logs |
| Training use | A contractual statement covering customer content and derived data |
| Deletion | API or support process, target systems, backup treatment, and confirmation format |
| Isolation | Tenant separation method and whether logs can be accessed by support staff |
| Certification | Scope, issuing body, report date, covered entities, and exceptions; certification is not a guarantee |
| Encryption | In transit, at rest, key ownership, rotation, and support access controls |

For regulated or proprietary workloads, a self-hosted or private deployment may remove some gateway concerns while adding patching, capacity, observability, and incident-response duties. A hosted gateway may simplify operations while concentrating risk in a third party. Neither model is automatically safer.

## 4. BYOK, hosted credentials and self-hosting

Record how upstream credentials are supplied and who can use them.

| Mode | Main benefit | Main question |
|---|---|---|
| Gateway-owned upstream account | Lower operational work for the buyer | Who controls quotas, suspension, logging, and provider terms? |
| BYOK | Buyer controls the upstream account relationship | Are keys encrypted, scoped, rotated, and excluded from logs? |
| Self-hosted gateway | Buyer controls deployment and network boundary | Who updates the proxy and verifies provider credentials? |

Do not send a production key to a test endpoint. Use a low-quota test key and revoke it after evaluation. A masked key prefix in a screenshot is not evidence that full credentials are excluded from application logs.

## 5. Failover and operational behavior

Failover can preserve availability while silently changing the model, region, price, or capability. Require a written policy that covers:

- The primary and fallback provider for each model.
- Whether fallback keeps the same model ID or substitutes another model.
- Regions that may serve a retry.
- Timeout, retry, idempotency, and duplicate-billing behavior.
- User-visible signaling when a fallback occurs.
- The fields written to request logs before and after fallback.
- How customers are notified of provider or route changes.

A status page reports selected symptoms. It is not an SLA. For an SLA claim, inspect the measurement window, excluded errors, credit calculation, regional scope, and support escalation path.

## 6. Observability and audit

Your own logs should answer: who called, from which application, at what UTC time, through which configured endpoint, with what model ID, under which policy version, at what cost, and with which upstream request ID.

Protect the audit trail from the same failure it is meant to diagnose. Retain it outside the gateway account where appropriate, restrict access, and define a legal-hold and deletion policy. Avoid storing full prompts or completions by default when hashes, metadata, and sampling are sufficient.

## 7. Cost governance

Model the total unit cost, not only the quoted input price:

```text
request cost =
  input tokens / 1,000,000 * input price
  + output tokens / 1,000,000 * output price
  + cache write/read units * their prices
  + image, audio, tool, or platform charges
```

Also account for retries, failed requests that bill, context growth, injected system prompts, minimum top-up, currency conversion, and unused credit. Compare the effective credit received with the amount paid, then reconcile against a sample invoice.

## 8. Exit test

Before signing, run one narrow pilot that includes:

1. A fixed request set against every promised model and protocol route.
2. One forced timeout or controlled failure to observe fallback signaling.
3. One export of request logs and invoice lines for reconciliation.
4. One key-revocation test.
5. One data-deletion request with written confirmation.
6. One review of model, subprocessor, and price change notices.

Choose the exit criteria before the pilot starts. A gateway that cannot produce reproducible evidence is not ready for production, even when the demo is fast.

## Related evidence

- [Model verification methodology](MODEL_VERIFICATION_METHODS.md)
- [Codex reconnect troubleshooting](Codex-一直Reconnecting-2026-10-18.en.md)
- [Claude Code 404 troubleshooting](Claude-Code-不要加v1-2026-10-18.en.md)

## Legal and vendor boundary

This is an independent technical checklist. It does not provide or resell API access and is not affiliated with OpenAI, Anthropic, Google, xAI, ByteDance, DeepSeek, MiniMax, or any other model vendor. Product names belong to their respective owners. Confirm current terms, privacy policy, security documentation, pricing, and availability with the provider before use.
