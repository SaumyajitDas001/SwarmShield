from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class AgentContext:
    campaign_id: str
    target_id: str
    request_budget: int
    token_budget: int
    shared_memory: tuple[str, ...] = ()


@dataclass(frozen=True)
class AttackCandidate:
    category: str
    test_case: str
    safe_message: str
    expected_signal: str
    priority: float
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(Protocol):
    name: str
    category: str

    async def initialize(self, context: AgentContext) -> None: ...
    async def generate_attacks(self, context: AgentContext) -> list[AttackCandidate]: ...
    async def finalize(self, context: AgentContext) -> None: ...
