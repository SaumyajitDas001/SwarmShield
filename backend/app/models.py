from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid
from .database import Base


def now() -> datetime: return datetime.now(timezone.utc)


class TargetRecord(Base):
    __tablename__ = "targets"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120))
    base_url: Mapped[str] = mapped_column(String(2048))
    authorization_reference: Mapped[str] = mapped_column(String(256))
    architecture: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class CampaignRecord(Base):
    __tablename__ = "campaigns"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    target_id: Mapped[object] = mapped_column(Uuid, ForeignKey("targets.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(32), index=True)
    request_budget: Mapped[int] = mapped_column(Integer)
    token_budget: Mapped[int] = mapped_column(Integer)
    time_budget_seconds: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class EventRecord(Base):
    __tablename__ = "agent_events"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    campaign_id: Mapped[object] = mapped_column(Uuid, ForeignKey("campaigns.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    agent: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(24))
    message: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)


class FindingRecord(Base):
    __tablename__ = "findings"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    campaign_id: Mapped[object] = mapped_column(Uuid, ForeignKey("campaigns.id"), index=True)
    title: Mapped[str] = mapped_column(String(280))
    category: Mapped[str] = mapped_column(String(120))
    severity: Mapped[str] = mapped_column(String(24), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    confidence: Mapped[float]
    risk_score: Mapped[float]
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    remediation: Mapped[str] = mapped_column(Text)


class AttackDNARecord(Base):
    __tablename__ = "attack_dna"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    campaign_id: Mapped[object] = mapped_column(Uuid, ForeignKey("campaigns.id"), index=True)
    parent_id: Mapped[object | None] = mapped_column(Uuid, nullable=True)
    generation: Mapped[int] = mapped_column(Integer, default=0)
    genome: Mapped[dict] = mapped_column(JSON)
    mutations: Mapped[list] = mapped_column(JSON, default=list)
    success_probability: Mapped[float]
    confidence: Mapped[float]


class ConsensusRecord(Base):
    __tablename__ = "finding_consensus"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    finding_id: Mapped[object] = mapped_column(Uuid, ForeignKey("findings.id"), index=True)
    agent: Mapped[str] = mapped_column(String(64))
    verdict: Mapped[str] = mapped_column(String(48))
    confidence: Mapped[float]
    evidence_summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class PredictionRecord(Base):
    __tablename__ = "predictions"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    target_id: Mapped[object] = mapped_column(Uuid, ForeignKey("targets.id"), index=True)
    family: Mapped[str] = mapped_column(String(120))
    component: Mapped[str] = mapped_column(String(120))
    probability: Mapped[float]
    confidence: Mapped[float]
    rationale: Mapped[str] = mapped_column(Text)
    validation_test: Mapped[str] = mapped_column(Text)


class GraphElementRecord(Base):
    __tablename__ = "attack_graph_elements"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    campaign_id: Mapped[object] = mapped_column(Uuid, ForeignKey("campaigns.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    element_key: Mapped[str] = mapped_column(String(120))
    payload: Mapped[dict] = mapped_column(JSON)


class RemediationRecord(Base):
    __tablename__ = "remediations"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    finding_id: Mapped[object] = mapped_column(Uuid, ForeignKey("findings.id"), index=True)
    remediation_before: Mapped[str] = mapped_column(Text)
    remediation_action: Mapped[str] = mapped_column(Text)
    validation_strategy: Mapped[str] = mapped_column(Text)
    validation_result: Mapped[str] = mapped_column(String(48), default="PENDING")
    remediation_confidence: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AttemptEconomicsRecord(Base):
    __tablename__ = "attempt_economics"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    campaign_id: Mapped[object] = mapped_column(Uuid, ForeignKey("campaigns.id"), index=True)
    agent: Mapped[str] = mapped_column(String(64))
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    mutation_depth: Mapped[int] = mapped_column(Integer, default=0)
    tool_calls: Mapped[int] = mapped_column(Integer, default=0)
