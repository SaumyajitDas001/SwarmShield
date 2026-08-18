# SwarmShield architecture

SwarmShield is an authorized AI-security assessment control plane. Its current release deliberately separates the user-facing control plane from target execution: the built-in demo path produces only synthetic, redacted evidence, while production orchestration is delegated to a signed workflow boundary.

## Current flow

```text
Dashboard → FastAPI API → PostgreSQL repository
                    ↓
          Campaign state machine
                    ↓
       Demo telemetry or signed n8n workflow
                    ↓
     Findings, evidence, lineage, graph, remediation
```

`TargetRecord` stores the authorized target reference, declared digital-twin architecture, and allowed-host scope. A campaign is constrained by request, token, and time budgets. The explicit state machine prevents invalid lifecycle changes.

In demo mode, `Repository.run_demo` invokes a typed `PromptSafetyAgent` through the execution guard and deterministic demo adapter. The guard requires an authorization reference, exact allowed host, and remaining request budget; the adapter never makes an external target request. The resulting normalized attempt and observation, synthetic events, evidence-backed findings, Attack DNA lineage, consensus signals, a predicted condition, graph elements, economics, and remediation inputs are persisted. In production mode, `Orchestrator` signs the workflow-start payload with `N8N_WEBHOOK_SECRET`; incoming workflow events must carry a valid HMAC signature.

The React dashboard obtains a demo token only when demo mode is enabled and renders campaign findings, consensus, Attack DNA, predicted conditions, efficiency, remediation, and a chronological event console.

## Security boundaries

- Target registration requires an authorization reference.
- Campaign starts and lifecycle changes require an authenticated security role.
- Request, token, and time budgets are persisted with every campaign.
- Demo mode is synthetic and explicitly labelled in the UI and API.
- Production integrations must enforce authorization, scope, rate limits, and redaction at their execution boundary.
- Workflow callbacks are HMAC-authenticated.

## Persistence

PostgreSQL holds targets, campaigns, immutable agent events, findings, Attack DNA, consensus decisions, predictions, graph elements, remediations, and campaign-attempt economics. Alembic owns schema upgrades.
