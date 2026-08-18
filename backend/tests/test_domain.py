import pytest
from app.domain import CampaignState, can_transition, normalized_risk, severity_for

def test_campaign_transitions_are_explicit():
    assert can_transition(CampaignState.DRAFT, CampaignState.READY)
    assert not can_transition(CampaignState.COMPLETED, CampaignState.RUNNING)

def test_risk_is_explainable_and_bounded():
    score = normalized_risk(impact=1, exploitability=1, confidence=1, reproducibility=1, privilege=1, data_sensitivity=1, tool_access=1, chain_depth=9)
    assert score == 100
    assert severity_for(score) == "Critical"
    with pytest.raises(ValueError): normalized_risk(impact=2, exploitability=0, confidence=0, reproducibility=0, privilege=0, data_sensitivity=0, tool_access=0, chain_depth=0)
