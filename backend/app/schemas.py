from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl
from .domain import CampaignState, FindingStatus


class TargetCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    base_url: HttpUrl
    authorization_reference: str = Field(min_length=8, description="Reference to the target owner's authorization record")
    scope: dict[str, Any] = Field(default_factory=dict)


class Target(BaseModel):
    id: UUID
    name: str
    base_url: HttpUrl
    authorization_reference: str
    architecture: dict[str, Any]


class CampaignCreate(BaseModel):
    target_id: UUID
    name: str = Field(min_length=2, max_length=120)
    request_budget: int = Field(default=50, ge=1, le=10_000)
    token_budget: int = Field(default=20_000, ge=100, le=2_000_000)
    time_budget_seconds: int = Field(default=900, ge=60, le=86_400)


class Campaign(BaseModel):
    id: UUID
    target_id: UUID
    name: str
    state: CampaignState
    created_at: datetime
    request_budget: int
    token_budget: int
    time_budget_seconds: int


class Event(BaseModel):
    id: UUID
    campaign_id: UUID
    timestamp: datetime
    agent: str
    event_type: str
    severity: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    id: UUID
    campaign_id: UUID
    title: str
    category: str
    severity: str
    status: FindingStatus
    confidence: float
    risk_score: float
    evidence: list[dict[str, Any]]
    remediation: str


class AttackDNA(BaseModel):
    id: UUID
    campaign_id: UUID
    parent_id: UUID | None
    generation: int
    genome: dict[str, Any]
    mutations: list[dict[str, Any]]
    success_probability: float
    confidence: float


class ConsensusDecision(BaseModel):
    agent: str
    verdict: str
    confidence: float
    evidence_summary: str
    created_at: datetime


class Prediction(BaseModel):
    id: UUID
    target_id: UUID
    family: str
    component: str
    probability: float
    confidence: float
    rationale: str
    validation_test: str


class Remediation(BaseModel):
    id: UUID
    finding_id: UUID
    remediation_before: str
    remediation_action: str
    validation_strategy: str
    validation_result: str
    remediation_confidence: float
    created_at: datetime


class Report(BaseModel):
    campaign_id: UUID
    executive_summary: str
    target_scope: str
    methodology: str
    findings: list[Finding]
    predicted_conditions: list[Prediction]
    remediation_count: int
    efficiency: dict[str, float | int]
