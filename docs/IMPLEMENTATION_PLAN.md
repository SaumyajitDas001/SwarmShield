# Implementation plan

## Completed foundation

- FastAPI control plane, PostgreSQL models, Alembic migration, CORS, JWT demo authentication, and role checks.
- Target registration and campaign lifecycle with budget controls.
- Safe synthetic campaign telemetry, evidence-grounded finding, risk score, Attack DNA lineage, consensus, graph contract, economics, remediation, revalidation, SSE event replay, and report contract.
- Docker Compose development stack and a responsive dashboard for the current APIs.

## In progress: controlled target-execution layer

Build the controlled target-execution layer behind the existing orchestration boundary:

1. Implemented typed target request/response contracts and a deterministic demo-only adapter.
2. Implemented authorization-reference, allowed-host, and request-budget enforcement ahead of the adapter.
3. Implemented `BaseAgent`, `AgentContext`, `AttackCandidate`, and a bounded prompt-safety validation agent.
4. Implemented persisted normalized attack attempts and observations, with read APIs.
5. Implemented deterministic evaluator composition with a persisted decision record and a configurable verification threshold. Findings are emitted only after the threshold is met.

## Completed in the next phase

- Added declared-metadata target fingerprinting with chat, RAG, tools, structured output, vision, streaming, and declared-tool fields.
- Added capability-aware agent category activation. Fingerprinting never sends a target request.

## Remaining later increments

- Attack-chain construction from persisted evidence.
- Attack-chain construction from persisted evidence.
- Additional agent categories and controlled benchmark fixtures.
- Report export, monitoring, RBAC hardening, and CI integration.

No future increment should make a request to an unregistered or out-of-scope target, or enable real-world tool actions from the demo target.
