import asyncio
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from .auth import LoginRequest, TokenResponse, authenticate, create_token, current_user, require_roles
from .config import settings
from .database import Base, engine, get_session
from .domain import CampaignState
from .fingerprinting import fingerprint_architecture
from .agents import active_descriptors, catalog
from .models import TargetRecord
from .orchestrator import Orchestrator, valid_signature
from .repository import Repository
from .schemas import AgentDescriptor, AgentMemory, AttackAttempt, AttackDNA, Campaign, CampaignCreate, ConsensusDecision, Evaluation, Event, Finding, MutationRequest, Observation, Prediction, Remediation, Report, Target, TargetCreate, TargetFingerprint

@asynccontextmanager
async def lifespan(_: FastAPI):
    with next(get_session()) as session:
        if settings.demo_mode and not session.scalar(select(TargetRecord.id).limit(1)):
            session.add(TargetRecord(name="Demo Support Agent", base_url="https://demo.authorized.local/api", authorization_reference="DEMO-AUTHORIZED-ONLY", architecture={"nodes":[{"id":"llm","type":"llm","label":"Support LLM"},{"id":"rag","type":"rag","label":"Knowledge RAG"},{"id":"tools","type":"tool","label":"Ticket API"}],"edges":[{"source":"rag","target":"llm"},{"source":"llm","target":"tools"}],"trust_boundaries":["retrieved-content","tool-permissions"],"scope":{"allowed_hosts":["demo.authorized.local"]}}))
            session.commit()
    yield

app = FastAPI(title="SwarmShield Control Plane", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url], allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(current_user)]
def repo(session: SessionDep) -> Repository: return Repository(session)

@app.get("/health")
def health(): return {"status": "ok", "mode": "demo-safe" if settings.demo_mode else "production", "persistence": "postgresql"}
@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login(data: LoginRequest): return authenticate(data)
@app.post("/api/v1/auth/demo-token", response_model=TokenResponse)
def demo_token():
    if not settings.demo_mode: raise HTTPException(404, "Demo mode disabled")
    return create_token("demo@swarmshield.local", "ADMIN")
@app.get("/api/v1/targets", response_model=list[Target])
def list_targets(session: SessionDep, _: UserDep): return repo(session).list_targets()
@app.post("/api/v1/targets", response_model=Target, status_code=201)
def create_target(data: TargetCreate, session: SessionDep, _: Annotated[dict, Depends(require_roles("ADMIN", "SECURITY_ANALYST"))]): return repo(session).create_target(data)
@app.get("/api/v1/targets/{target_id}/architecture")
def architecture(target_id: UUID, session: SessionDep, _: UserDep):
    target = repo(session).get_target(target_id)
    if not target: raise HTTPException(404, "Target not found")
    return target.architecture
@app.post("/api/v1/targets/{target_id}/fingerprint", response_model=TargetFingerprint)
def fingerprint(target_id: UUID, session: SessionDep, _: UserDep):
    target = repo(session).get_target(target_id)
    if not target: raise HTTPException(404, "Target not found")
    return fingerprint_architecture(target.architecture).as_dict()
@app.get("/api/v1/agents", response_model=list[AgentDescriptor])
def agents(_: UserDep): return [AgentDescriptor.model_validate(item) for item in catalog()]
@app.get("/api/v1/targets/{target_id}/agents", response_model=list[AgentDescriptor])
def target_agents(target_id: UUID, session: SessionDep, _: UserDep):
    target = repo(session).get_target(target_id)
    if not target: raise HTTPException(404, "Target not found")
    return [AgentDescriptor.model_validate(item) for item in active_descriptors(fingerprint_architecture(target.architecture))]
@app.post("/api/v1/campaigns", response_model=Campaign, status_code=201)
def create_campaign(data: CampaignCreate, session: SessionDep, _: Annotated[dict, Depends(require_roles("ADMIN", "SECURITY_ANALYST"))]):
    try: return repo(session).create_campaign(data)
    except KeyError: raise HTTPException(404, "Target not found")
@app.get("/api/v1/campaigns/{campaign_id}", response_model=Campaign)
def get_campaign(campaign_id: UUID, session: SessionDep, _: UserDep):
    item = repo(session).get_campaign(campaign_id)
    if not item: raise HTTPException(404, "Campaign not found")
    return repo(session).campaign(item)
@app.post("/api/v1/campaigns/{campaign_id}/start", response_model=Campaign)
def start(campaign_id: UUID, session: SessionDep, _: Annotated[dict, Depends(require_roles("ADMIN", "SECURITY_ANALYST"))]):
    repository = repo(session)
    try:
        item = repository.get_campaign(campaign_id)
        if not item: raise KeyError
        if item.state == CampaignState.DRAFT: repository.transition(campaign_id, CampaignState.READY)
        campaign = repository.transition(campaign_id, CampaignState.RUNNING)
        if settings.demo_mode:
            repository.run_demo(campaign_id)
            repository.transition(campaign_id, CampaignState.COMPLETED)
        else:
            try:
                Orchestrator().start_campaign(str(campaign_id), str(item.target_id), {"requests": item.request_budget, "tokens": item.token_budget, "seconds": item.time_budget_seconds})
                repository.emit(campaign_id, "Orchestrator", "WORKFLOW_TRIGGERED", "Informational", "Signed n8n campaign workflow started.")
                session.commit()
            except Exception:
                repository.emit(campaign_id, "Orchestrator", "WORKFLOW_FAILED", "High", "n8n workflow could not be started; no target action was performed.")
                session.commit()
                raise HTTPException(502, "Campaign orchestration unavailable")
        return campaign
    except KeyError: raise HTTPException(404, "Campaign not found")
    except ValueError as error: raise HTTPException(409, str(error))
@app.post("/api/v1/campaigns/{campaign_id}/pause", response_model=Campaign)
def pause(campaign_id: UUID, session: SessionDep, _: Annotated[dict, Depends(require_roles("ADMIN", "SECURITY_ANALYST"))]):
    try: return repo(session).transition(campaign_id, CampaignState.PAUSED)
    except KeyError: raise HTTPException(404, "Campaign not found")
    except ValueError as error: raise HTTPException(409, str(error))
@app.post("/api/v1/campaigns/{campaign_id}/resume", response_model=Campaign)
def resume(campaign_id: UUID, session: SessionDep, _: Annotated[dict, Depends(require_roles("ADMIN", "SECURITY_ANALYST"))]):
    try: return repo(session).transition(campaign_id, CampaignState.RUNNING)
    except KeyError: raise HTTPException(404, "Campaign not found")
    except ValueError as error: raise HTTPException(409, str(error))
@app.post("/api/v1/campaigns/{campaign_id}/cancel", response_model=Campaign)
def cancel(campaign_id: UUID, session: SessionDep, _: Annotated[dict, Depends(require_roles("ADMIN", "SECURITY_ANALYST"))]):
    repository = repo(session)
    try:
        repository.transition(campaign_id, CampaignState.CANCELLING)
        return repository.transition(campaign_id, CampaignState.CANCELLED)
    except KeyError: raise HTTPException(404, "Campaign not found")
    except ValueError as error: raise HTTPException(409, str(error))
@app.get("/api/v1/campaigns/{campaign_id}/findings", response_model=list[Finding])
def findings(campaign_id: UUID, session: SessionDep, _: UserDep):
    if not repo(session).get_campaign(campaign_id): raise HTTPException(404, "Campaign not found")
    return repo(session).findings(campaign_id)
@app.get("/api/v1/campaigns/{campaign_id}/attack-dna", response_model=list[AttackDNA])
def attack_dna(campaign_id: UUID, session: SessionDep, _: UserDep):
    if not repo(session).get_campaign(campaign_id): raise HTTPException(404, "Campaign not found")
    return repo(session).dna_for_campaign(campaign_id)
@app.post("/api/v1/campaigns/{campaign_id}/attack-dna/{dna_id}/mutate", response_model=AttackDNA)
def mutate_attack_dna(campaign_id: UUID, dna_id: UUID, data: MutationRequest, session: SessionDep, _: Annotated[dict, Depends(require_roles("ADMIN", "SECURITY_ANALYST"))]):
    try: return repo(session).mutate_dna(campaign_id, dna_id, data.mutation_type)
    except KeyError: raise HTTPException(404, "Attack DNA not found")
    except ValueError as error: raise HTTPException(422, str(error))
@app.get("/api/v1/campaigns/{campaign_id}/attempts", response_model=list[AttackAttempt])
def attempts(campaign_id: UUID, session: SessionDep, _: UserDep):
    if not repo(session).get_campaign(campaign_id): raise HTTPException(404, "Campaign not found")
    return repo(session).attempts(campaign_id)
@app.get("/api/v1/campaigns/{campaign_id}/observations", response_model=list[Observation])
def observations(campaign_id: UUID, session: SessionDep, _: UserDep):
    if not repo(session).get_campaign(campaign_id): raise HTTPException(404, "Campaign not found")
    return repo(session).observations(campaign_id)
@app.get("/api/v1/campaigns/{campaign_id}/evaluations", response_model=list[Evaluation])
def evaluations(campaign_id: UUID, session: SessionDep, _: UserDep):
    if not repo(session).get_campaign(campaign_id): raise HTTPException(404, "Campaign not found")
    return repo(session).evaluations(campaign_id)
@app.get("/api/v1/campaigns/{campaign_id}/memory", response_model=list[AgentMemory])
def memory(campaign_id: UUID, session: SessionDep, _: UserDep):
    if not repo(session).get_campaign(campaign_id): raise HTTPException(404, "Campaign not found")
    return repo(session).memories(campaign_id)
@app.get("/api/v1/campaigns/{campaign_id}/attack-graph")
def attack_graph(campaign_id: UUID, session: SessionDep, _: UserDep):
    if not repo(session).get_campaign(campaign_id): raise HTTPException(404, "Campaign not found")
    return repo(session).graph(campaign_id)
@app.get("/api/v1/campaigns/{campaign_id}/evidence-chain")
def evidence_chain(campaign_id: UUID, session: SessionDep, _: UserDep):
    if not repo(session).get_campaign(campaign_id): raise HTTPException(404, "Campaign not found")
    return repo(session).evidence_chain(campaign_id)
@app.get("/api/v1/findings/{finding_id}/consensus", response_model=list[ConsensusDecision])
def consensus(finding_id: UUID, session: SessionDep, _: UserDep):
    return repo(session).consensus(finding_id)
@app.get("/api/v1/targets/{target_id}/predictions", response_model=list[Prediction])
def predictions(target_id: UUID, session: SessionDep, _: UserDep):
    if not repo(session).get_target(target_id): raise HTTPException(404, "Target not found")
    return repo(session).predictions(target_id)
@app.get("/api/v1/findings/{finding_id}/remediations", response_model=list[Remediation])
def remediations(finding_id: UUID, session: SessionDep, _: UserDep): return repo(session).remediations(finding_id)
@app.post("/api/v1/findings/{finding_id}/remediations", response_model=Remediation, status_code=201)
def generate_remediation(finding_id: UUID, session: SessionDep, _: Annotated[dict, Depends(require_roles("ADMIN", "SECURITY_ANALYST"))]):
    try: return repo(session).generate_remediation(finding_id)
    except KeyError: raise HTTPException(404, "Finding not found")
@app.post("/api/v1/remediations/{remediation_id}/revalidate", response_model=Remediation)
def revalidate(remediation_id: UUID, session: SessionDep, _: Annotated[dict, Depends(require_roles("ADMIN", "SECURITY_ANALYST"))]):
    try: return repo(session).revalidate(remediation_id)
    except KeyError: raise HTTPException(404, "Remediation not found")
@app.get("/api/v1/campaigns/{campaign_id}/efficiency")
def efficiency(campaign_id: UUID, session: SessionDep, _: UserDep):
    if not repo(session).get_campaign(campaign_id): raise HTTPException(404, "Campaign not found")
    return repo(session).efficiency(campaign_id)
@app.get("/api/v1/campaigns/{campaign_id}/report", response_model=Report)
def report(campaign_id: UUID, session: SessionDep, _: UserDep):
    try: return repo(session).report(campaign_id)
    except KeyError: raise HTTPException(404, "Campaign not found")
@app.post("/internal/v1/orchestration/events")
async def orchestration_event(request: Request, session: SessionDep):
    body = await request.body()
    if not valid_signature(body, request.headers.get("X-SwarmShield-Signature")): raise HTTPException(401, "Invalid workflow signature")
    try:
        payload = await request.json(); campaign_id = UUID(payload["campaign_id"])
        if not repo(session).get_campaign(campaign_id): raise ValueError
    except (ValueError, KeyError): raise HTTPException(400, "Invalid campaign event")
    allowed = {"AGENT_STARTED", "ATTACK_STARTED", "ATTACK_COMPLETED", "MUTATION_CREATED", "EVIDENCE_COLLECTED", "FINDING_CREATED", "FINDING_VERIFIED", "REMEDIATION_GENERATED", "REVALIDATION_PASSED", "REVALIDATION_FAILED", "CAMPAIGN_COMPLETED"}
    if payload.get("event_type") not in allowed: raise HTTPException(400, "Unsupported event type")
    repo(session).emit(campaign_id, payload.get("agent", "n8n"), payload["event_type"], payload.get("severity", "Informational"), payload.get("message", "Workflow event received."), payload.get("metadata", {})); session.commit()
    return {"accepted": True}
@app.get("/api/v1/campaigns/{campaign_id}/events", response_model=list[Event])
def events(campaign_id: UUID, session: SessionDep, _: UserDep):
    if not repo(session).get_campaign(campaign_id): raise HTTPException(404, "Campaign not found")
    return repo(session).events(campaign_id)
@app.get("/api/v1/campaigns/{campaign_id}/stream")
async def stream(campaign_id: UUID, session: SessionDep, _: UserDep):
    repository = repo(session)
    if not repository.get_campaign(campaign_id): raise HTTPException(404, "Campaign not found")
    snapshot = repository.events(campaign_id)
    async def send_events():
        for event in snapshot:
            yield f"event: campaign-event\\ndata: {event.model_dump_json()}\\n\\n"
            await asyncio.sleep(.05)
    return StreamingResponse(send_events(), media_type="text/event-stream")
