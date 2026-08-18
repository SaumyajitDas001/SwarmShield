"""Normalized target adapter contracts.

Adapters are deliberately small: authorization and scope policy live in the
execution service, not in a provider-specific transport implementation.
"""
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class TargetRequest:
    campaign_id: str
    test_case: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TargetResponse:
    text: str
    latency_ms: int
    estimated_tokens: int
    metadata: dict[str, Any] = field(default_factory=dict)


class TargetAdapter(Protocol):
    async def send(self, request: TargetRequest) -> TargetResponse: ...
    async def metadata(self) -> dict[str, Any]: ...
    async def health(self) -> bool: ...
