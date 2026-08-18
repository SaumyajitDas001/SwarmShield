from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


MEMORY_TYPES = {"DISCOVERY", "SUCCESS", "FAILURE", "TARGET_CAPABILITY", "TOOL", "VULNERABILITY", "ATTACK_PATTERN"}


@dataclass(frozen=True)
class MemoryItem:
    memory_type: str
    content: str
    confidence: float
    agent: str
    source_attack_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def validate_memory(item: MemoryItem) -> MemoryItem:
    if item.memory_type not in MEMORY_TYPES:
        raise ValueError("Unsupported swarm memory type")
    if not 0 <= item.confidence <= 1:
        raise ValueError("Memory confidence must be between 0 and 1")
    if not item.content.strip() or not item.agent.strip():
        raise ValueError("Memory content and agent are required")
    return item


def retrieve_relevant(items: list[MemoryItem], query: str, limit: int = 10) -> list[MemoryItem]:
    """Deterministic lexical fallback; semantic retrieval can replace this later."""
    terms = {term.lower() for term in query.split() if term.strip()}
    ranked = sorted(items, key=lambda item: (len(terms & set(item.content.lower().split())), item.confidence), reverse=True)
    return ranked[:max(0, limit)]
