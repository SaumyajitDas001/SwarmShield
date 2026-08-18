# SwarmShield

SwarmShield is an authorized, defensive AI-security assessment platform. It models campaign scope, agent state, evidence, consensus, remediation and re-validation without providing uncontrolled attack execution.

## Local development

1. Copy `.env.example` to `.env` and set secrets.
2. Run `docker compose up --build`.
3. Open `http://localhost:8000/docs` for the API and `http://localhost:5173` for the UI.

`DEMO_MODE=true` enables only synthetic telemetry against the seeded authorized demo target. Production integrations must enforce target authorization, scope budgets and rate limits at the execution boundary.

## Delivered foundations

- FastAPI control-plane contract and OpenAPI docs
- PostgreSQL persistence for targets, campaigns, agent events and findings
- explicit campaign and agent state machines
- immutable, structured event stream (SSE)
- safe demo campaign lifecycle with findings, consensus, risk and remediation records
- JWT authentication and role-based access controls for campaign operations
- pause, resume and cancellation lifecycle controls
- Attack DNA genomes with parent lineage and feature-level mutation history
- multi-agent consensus evidence (Judge, Evidence, Skeptic and Verifier)
- clearly labelled predicted conditions and a persisted attack-graph contract
- evidence-grounded remediation generation and controlled re-validation results
- campaign economics (requests, estimated tokens, latency and finding efficiency)
- backend-generated assessment report endpoint grounded in stored campaign records
- Docker Compose configuration for API, PostgreSQL, n8n and frontend

## Authentication

The dashboard requests a short-lived demo token only when `DEMO_MODE=true`. For a real deployment, set a strong `JWT_SECRET`, replace the single admin credentials with an identity provider or user repository, and set `DEMO_MODE=false`. Never expose target credentials or workflow secrets to the frontend.

The supplied frontend archive could not be read from the referenced Downloads location in this environment, so its visual components have not yet been merged. Place/extract it in this repository for a later visual integration phase.

## Deployment controls

The API container runs `alembic upgrade head` before starting, so PostgreSQL schema state is versioned. In production set all secrets in the deployment platform rather than a checked-in `.env`; set `DEMO_MODE=false`; and configure n8n to call `POST /internal/v1/orchestration/events` with the HMAC signature calculated from `N8N_WEBHOOK_SECRET`. Production campaign starts are handed to n8n through its signed `swarmshield-campaign-start` webhook.
