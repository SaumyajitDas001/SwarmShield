"""The only supported path from a campaign to a target adapter."""
from urllib.parse import urlparse
from .adapters import DemoTargetAdapter, TargetRequest, TargetResponse
from .config import settings


class ExecutionBlocked(ValueError):
    pass


def verify_execution_scope(*, base_url: str, authorization_reference: str, scope: dict, request_count: int, request_budget: int) -> None:
    """Reject target execution unless it is explicitly authorized and in scope."""
    if not authorization_reference.strip():
        raise ExecutionBlocked("A target authorization reference is required")
    if request_count >= request_budget:
        raise ExecutionBlocked("Campaign request budget has been exhausted")
    host = urlparse(base_url).hostname
    if not host:
        raise ExecutionBlocked("Target URL has no valid host")
    allowed_hosts = set(scope.get("allowed_hosts", []))
    if host not in allowed_hosts:
        raise ExecutionBlocked("Target host is outside the registered campaign scope")


async def execute_demo_validation(*, campaign_id: str, base_url: str, authorization_reference: str, scope: dict, request_count: int, request_budget: int, test_case: str, message: str) -> TargetResponse:
    verify_execution_scope(base_url=base_url, authorization_reference=authorization_reference, scope=scope, request_count=request_count, request_budget=request_budget)
    if not settings.demo_mode or urlparse(base_url).hostname != "demo.authorized.local":
        raise ExecutionBlocked("Only the local synthetic demo adapter is enabled in this release")
    adapter = DemoTargetAdapter()
    return await adapter.send(TargetRequest(campaign_id=campaign_id, test_case=test_case, message=message))
