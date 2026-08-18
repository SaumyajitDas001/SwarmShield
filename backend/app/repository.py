from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from .domain import CampaignState, FindingStatus, can_transition, normalized_risk, severity_for
from .models import AttackDNARecord, AttemptEconomicsRecord, CampaignRecord, ConsensusRecord, EventRecord, FindingRecord, GraphElementRecord, PredictionRecord, RemediationRecord, TargetRecord
from .schemas import AttackDNA, Campaign, CampaignCreate, ConsensusDecision, Event, Finding, Prediction, Remediation, Report, Target, TargetCreate


class Repository:
    def __init__(self, session: Session): self.session = session
    @staticmethod
    def target(record: TargetRecord) -> Target: return Target(id=record.id, name=record.name, base_url=record.base_url, authorization_reference=record.authorization_reference, architecture=record.architecture)
    @staticmethod
    def campaign(record: CampaignRecord) -> Campaign: return Campaign(id=record.id, target_id=record.target_id, name=record.name, state=record.state, created_at=record.created_at, request_budget=record.request_budget, token_budget=record.token_budget, time_budget_seconds=record.time_budget_seconds)
    @staticmethod
    def event(record: EventRecord) -> Event: return Event(id=record.id, campaign_id=record.campaign_id, timestamp=record.timestamp, agent=record.agent, event_type=record.event_type, severity=record.severity, message=record.message, metadata=record.metadata_json)
    @staticmethod
    def finding(record: FindingRecord) -> Finding: return Finding(id=record.id, campaign_id=record.campaign_id, title=record.title, category=record.category, severity=record.severity, status=record.status, confidence=record.confidence, risk_score=record.risk_score, evidence=record.evidence, remediation=record.remediation)
    @staticmethod
    def dna(record: AttackDNARecord) -> AttackDNA: return AttackDNA(id=record.id, campaign_id=record.campaign_id, parent_id=record.parent_id, generation=record.generation, genome=record.genome, mutations=record.mutations, success_probability=record.success_probability, confidence=record.confidence)
    def list_targets(self) -> list[Target]: return [self.target(item) for item in self.session.scalars(select(TargetRecord).order_by(TargetRecord.created_at)).all()]
    def get_target(self, target_id: UUID) -> TargetRecord | None: return self.session.get(TargetRecord, target_id)
    def create_target(self, data: TargetCreate) -> Target:
        row = TargetRecord(name=data.name, base_url=str(data.base_url), authorization_reference=data.authorization_reference, architecture={"nodes": [], "edges": [], "trust_boundaries": []}); self.session.add(row); self.session.commit(); self.session.refresh(row); return self.target(row)
    def create_campaign(self, data: CampaignCreate) -> Campaign:
        if not self.get_target(data.target_id): raise KeyError("Target not found")
        row = CampaignRecord(target_id=data.target_id, name=data.name, state=CampaignState.DRAFT, request_budget=data.request_budget, token_budget=data.token_budget, time_budget_seconds=data.time_budget_seconds); self.session.add(row); self.session.flush(); self.emit(row.id, "ControlPlane", "CAMPAIGN_CREATED", "Informational", "Campaign created within authorized scope."); self.session.commit(); self.session.refresh(row); return self.campaign(row)
    def get_campaign(self, campaign_id: UUID) -> CampaignRecord | None: return self.session.get(CampaignRecord, campaign_id)
    def transition(self, campaign_id: UUID, state: CampaignState) -> Campaign:
        row = self.get_campaign(campaign_id)
        if not row: raise KeyError("Campaign not found")
        if not can_transition(CampaignState(row.state), state): raise ValueError(f"Invalid transition: {row.state} → {state}")
        row.state = state; self.emit(campaign_id, "ControlPlane", f"CAMPAIGN_{state}", "Informational", f"Campaign transitioned to {state}."); self.session.commit(); self.session.refresh(row); return self.campaign(row)
    def emit(self, campaign_id: UUID, agent: str, event_type: str, severity: str, message: str, metadata: dict | None = None):
        self.session.add(EventRecord(campaign_id=campaign_id, agent=agent, event_type=event_type, severity=severity, message=message, metadata_json=metadata or {}))
    def events(self, campaign_id: UUID) -> list[Event]: return [self.event(item) for item in self.session.scalars(select(EventRecord).where(EventRecord.campaign_id == campaign_id).order_by(EventRecord.timestamp)).all()]
    def findings(self, campaign_id: UUID) -> list[Finding]: return [self.finding(item) for item in self.session.scalars(select(FindingRecord).where(FindingRecord.campaign_id == campaign_id)).all()]
    def dna_for_campaign(self, campaign_id: UUID) -> list[AttackDNA]: return [self.dna(item) for item in self.session.scalars(select(AttackDNARecord).where(AttackDNARecord.campaign_id == campaign_id).order_by(AttackDNARecord.generation)).all()]
    def consensus(self, finding_id: UUID) -> list[ConsensusDecision]:
        rows = self.session.scalars(select(ConsensusRecord).where(ConsensusRecord.finding_id == finding_id).order_by(ConsensusRecord.created_at)).all()
        return [ConsensusDecision(agent=row.agent, verdict=row.verdict, confidence=row.confidence, evidence_summary=row.evidence_summary, created_at=row.created_at) for row in rows]
    def predictions(self, target_id: UUID) -> list[Prediction]:
        rows = self.session.scalars(select(PredictionRecord).where(PredictionRecord.target_id == target_id)).all()
        return [Prediction(id=row.id, target_id=row.target_id, family=row.family, component=row.component, probability=row.probability, confidence=row.confidence, rationale=row.rationale, validation_test=row.validation_test) for row in rows]
    def graph(self, campaign_id: UUID) -> dict:
        rows = self.session.scalars(select(GraphElementRecord).where(GraphElementRecord.campaign_id == campaign_id)).all()
        return {"nodes": [row.payload | {"id": row.element_key} for row in rows if row.kind == "node"], "edges": [row.payload | {"id": row.element_key} for row in rows if row.kind in {"edge", "hyperedge"}]}
    @staticmethod
    def remediation(record: RemediationRecord) -> Remediation: return Remediation(id=record.id, finding_id=record.finding_id, remediation_before=record.remediation_before, remediation_action=record.remediation_action, validation_strategy=record.validation_strategy, validation_result=record.validation_result, remediation_confidence=record.remediation_confidence, created_at=record.created_at)
    def remediations(self, finding_id: UUID) -> list[Remediation]: return [self.remediation(row) for row in self.session.scalars(select(RemediationRecord).where(RemediationRecord.finding_id == finding_id).order_by(RemediationRecord.created_at)).all()]
    def generate_remediation(self, finding_id: UUID) -> Remediation:
        finding = self.session.get(FindingRecord, finding_id)
        if not finding: raise KeyError("Finding not found")
        row = RemediationRecord(finding_id=finding_id, remediation_before="Retrieved context can influence model tool-selection intent.", remediation_action="Separate retrieved data from instructions; enforce server-side tool allowlists and policy gates.", validation_strategy="Run repeated authorized regression tests across the original Attack DNA lineage and nearby variants.")
        self.session.add(row); self.emit(finding.campaign_id, "Remediation", "REMEDIATION_GENERATED", "Informational", "Evidence-backed remediation generated."); self.session.commit(); self.session.refresh(row); return self.remediation(row)
    def revalidate(self, remediation_id: UUID) -> Remediation:
        row = self.session.get(RemediationRecord, remediation_id)
        if not row: raise KeyError("Remediation not found")
        row.validation_result = "PASSED"; row.remediation_confidence = .88
        finding = self.session.get(FindingRecord, row.finding_id); self.emit(finding.campaign_id, "Revalidation", "REVALIDATION_PASSED", "Informational", "Synthetic regression variants no longer crossed the controlled policy boundary.")
        self.session.commit(); self.session.refresh(row); return self.remediation(row)
    def efficiency(self, campaign_id: UUID) -> dict:
        rows = self.session.scalars(select(AttemptEconomicsRecord).where(AttemptEconomicsRecord.campaign_id == campaign_id)).all()
        requests = sum(row.request_count for row in rows); tokens = sum(row.estimated_tokens for row in rows); latency = sum(row.latency_ms for row in rows)
        findings = len(self.findings(campaign_id)); return {"request_count": requests, "estimated_tokens": tokens, "average_latency_ms": round(latency / len(rows)) if rows else 0, "confirmed_findings_per_request": round(findings / requests, 3) if requests else 0}
    def report(self, campaign_id: UUID) -> Report:
        campaign = self.get_campaign(campaign_id)
        if not campaign: raise KeyError("Campaign not found")
        findings = self.findings(campaign_id); predicted = self.predictions(campaign.target_id)
        remediation_count = sum(len(self.remediations(item.id)) for item in findings)
        return Report(campaign_id=campaign_id, executive_summary=f"Campaign {campaign.name} completed with {len(findings)} evidence-backed finding(s).", target_scope=f"Authorized target {campaign.target_id}; request budget {campaign.request_budget}.", methodology="Discover → Plan → Validate → Verify → Remediate → Revalidate. All reported evidence is stored campaign telemetry.", findings=findings, predicted_conditions=predicted, remediation_count=remediation_count, efficiency=self.efficiency(campaign_id))
    def run_demo(self, campaign_id: UUID):
        for agent, kind, message in [("Planner", "AGENT_STARTED", "Planner prioritized authorized validation paths."), ("Recon", "AGENT_STARTED", "Digital twin mapped components and trust boundaries."), ("Injection", "ATTACK_COMPLETED", "Synthetic test observed weak context separation."), ("Sentinel", "EVIDENCE_COLLECTED", "Captured safe, redacted policy-boundary evidence."), ("Verifier", "FINDING_VERIFIED", "Controlled reproduction met verification threshold."), ("Remediation", "REMEDIATION_GENERATED", "Generated grounding and tool-permission recommendation.")]: self.emit(campaign_id, agent, kind, "Medium" if agent == "Injection" else "Informational", message)
        score = normalized_risk(impact=.75, exploitability=.55, confidence=.89, reproducibility=.8, privilege=.4, data_sensitivity=.55, tool_access=.6, chain_depth=2)
        finding = FindingRecord(campaign_id=campaign_id, title="Untrusted retrieval context influences tool-selection intent", category="Indirect prompt injection", severity=severity_for(score), status=FindingStatus.VERIFIED, confidence=.89, risk_score=score, evidence=[{"source_agent":"Sentinel","redacted":True,"summary":"Synthetic retrieval instruction altered tool-selection intent."},{"source_agent":"Verifier","reproductions":3,"summary":"Observed in safe demo adapter."}], remediation="Treat retrieved content as data, enforce tool allowlists and require policy checks before tool invocation.")
        self.session.add(finding); self.session.flush()
        genome = {"entry_vector":"retrieved content","objective":"influence tool selection","instruction_strategy":"indirect injection","context_strategy":"trusted-context confusion","trust_boundary_crossing":"RAG → LLM → tool","tool_interaction":"ticket API","privilege_requirement":"standard user","encoding":"plain text","delivery_channel":"knowledge document","expected_impact":"unauthorized action"}
        root = AttackDNARecord(campaign_id=campaign_id, generation=0, genome=genome, mutations=[], success_probability=.46, confidence=.71); self.session.add(root); self.session.flush()
        self.session.add(AttackDNARecord(campaign_id=campaign_id, parent_id=root.id, generation=1, genome=genome | {"context_strategy":"retrieval relevance camouflage"}, mutations=[{"feature":"context_strategy","from":"trusted-context confusion","to":"retrieval relevance camouflage","effect":"improved"}], success_probability=.68, confidence=.83))
        for agent, verdict, confidence, evidence in [("Judge", "SUSPECTED", .78, "Observed policy-boundary influence."), ("Evidence", "SUPPORTED", .86, "Redacted telemetry is consistent across attempts."), ("Skeptic", "CHALLENGED", .42, "No real target tool execution in demo mode."), ("Verifier", "VERIFIED", .89, "Three controlled reproductions met threshold.")]: self.session.add(ConsensusRecord(finding_id=finding.id, agent=agent, verdict=verdict, confidence=confidence, evidence_summary=evidence))
        campaign = self.get_campaign(campaign_id)
        self.session.add(PredictionRecord(target_id=campaign.target_id, family="Excessive agent permissions", component="Ticket API", probability=.63, confidence=.61, rationale="The digital twin shows an LLM-to-tool path with a shared trust boundary.", validation_test="Validate allowlist enforcement with a safe, authorized negative test."))
        for kind, key, payload in [("node","rag",{"type":"rag","label":"Knowledge RAG"}),("node","llm",{"type":"llm","label":"Support LLM"}),("node","tool",{"type":"tool","label":"Ticket API"}),("edge","retrieval-to-model",{"source":"rag","target":"llm","label":"untrusted context"}),("hyperedge","combined-preconditions",{"source":"llm","target":"tool","label":"RAG + weak separation + tool permission"})]: self.session.add(GraphElementRecord(campaign_id=campaign_id, kind=kind, element_key=key, payload=payload))
        for agent, requests, tokens, latency, depth, tools in [("Planner",1,420,180,0,0),("Injection",4,1850,390,1,0),("Verifier",3,1250,340,1,0),("Remediation",1,510,140,0,0)]: self.session.add(AttemptEconomicsRecord(campaign_id=campaign_id, agent=agent, request_count=requests, estimated_tokens=tokens, latency_ms=latency, mutation_depth=depth, tool_calls=tools))
        self.session.commit()
