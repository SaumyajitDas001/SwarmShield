import asyncio
import pytest
from app.agents import AgentContext, PromptSafetyAgent
from app.execution import ExecutionBlocked, execute_demo_validation, verify_execution_scope


def test_execution_scope_requires_authorization_host_and_budget():
    scope = {"allowed_hosts": ["demo.authorized.local"]}
    verify_execution_scope(base_url="https://demo.authorized.local/api", authorization_reference="AUTH-123456", scope=scope, request_count=0, request_budget=1)
    with pytest.raises(ExecutionBlocked):
        verify_execution_scope(base_url="https://outside.example/api", authorization_reference="AUTH-123456", scope=scope, request_count=0, request_budget=1)
    with pytest.raises(ExecutionBlocked):
        verify_execution_scope(base_url="https://demo.authorized.local/api", authorization_reference="", scope=scope, request_count=0, request_budget=1)
    with pytest.raises(ExecutionBlocked):
        verify_execution_scope(base_url="https://demo.authorized.local/api", authorization_reference="AUTH-123456", scope=scope, request_count=1, request_budget=1)


def test_prompt_safety_agent_and_demo_adapter_are_bounded():
    context = AgentContext(campaign_id="campaign", target_id="target", request_budget=2, token_budget=1000)
    candidate = asyncio.run(PromptSafetyAgent().generate_attacks(context))[0]
    assert candidate.metadata["synthetic_only"] is True
    response = asyncio.run(execute_demo_validation(campaign_id="campaign", base_url="https://demo.authorized.local/api", authorization_reference="AUTH-123456", scope={"allowed_hosts": ["demo.authorized.local"]}, request_count=0, request_budget=2, test_case=candidate.test_case, message=candidate.safe_message))
    assert response.metadata["synthetic"] is True
    assert response.metadata["redacted"] is True
