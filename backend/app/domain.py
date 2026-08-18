from enum import StrEnum


class CampaignState(StrEnum):
    DRAFT = "DRAFT"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AgentState(StrEnum):
    IDLE = "IDLE"
    INITIALIZING = "INITIALIZING"
    PLANNING = "PLANNING"
    RECONNAISSANCE = "RECONNAISSANCE"
    ATTACKING = "ATTACKING"
    OBSERVING = "OBSERVING"
    MUTATING = "MUTATING"
    VERIFYING = "VERIFYING"
    WAITING = "WAITING"
    REMEDIATING = "REMEDIATING"
    REVALIDATING = "REVALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"


class FindingStatus(StrEnum):
    SUSPECTED = "SUSPECTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    CONFIRMED = "CONFIRMED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"


CAMPAIGN_TRANSITIONS = {
    CampaignState.DRAFT: {CampaignState.READY, CampaignState.CANCELLED},
    CampaignState.READY: {CampaignState.RUNNING, CampaignState.CANCELLED},
    CampaignState.RUNNING: {CampaignState.PAUSED, CampaignState.CANCELLING, CampaignState.COMPLETED, CampaignState.FAILED},
    CampaignState.PAUSED: {CampaignState.RUNNING, CampaignState.CANCELLING},
    CampaignState.CANCELLING: {CampaignState.CANCELLED},
}


def can_transition(current: CampaignState, next_state: CampaignState) -> bool:
    return next_state in CAMPAIGN_TRANSITIONS.get(current, set())


def normalized_risk(*, impact: float, exploitability: float, confidence: float,
                    reproducibility: float, privilege: float, data_sensitivity: float,
                    tool_access: float, chain_depth: int) -> float:
    """Explainable 0–100 score; every input is normalized 0–1 except depth."""
    values = (impact, exploitability, confidence, reproducibility, privilege, data_sensitivity, tool_access)
    if any(value < 0 or value > 1 for value in values) or chain_depth < 0:
        raise ValueError("Risk factors must be normalized to 0–1 and depth non-negative")
    depth_factor = min(chain_depth / 4, 1)
    weighted = (
        impact * .24 + exploitability * .18 + confidence * .14 + reproducibility * .14
        + privilege * .10 + data_sensitivity * .10 + tool_access * .06 + depth_factor * .04
    )
    return round(weighted * 100, 1)


def severity_for(score: float) -> str:
    if score >= 81: return "Critical"
    if score >= 61: return "High"
    if score >= 41: return "Medium"
    if score >= 21: return "Low"
    return "Informational"
