from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EvaluationDecision:
    evaluator: str
    is_vulnerable: bool
    confidence: float
    reason: str
    evidence: dict[str, object]


class Evaluator(Protocol):
    def evaluate(self, response_summary: str, metadata: dict[str, object]) -> EvaluationDecision: ...
