from .base import EvaluationDecision, Evaluator


class CompositeEvaluator:
    def __init__(self, evaluators: list[Evaluator], verification_threshold: float = .75):
        self.evaluators = evaluators
        self.verification_threshold = verification_threshold

    def evaluate(self, response_summary: str, metadata: dict[str, object]) -> tuple[bool, float, list[EvaluationDecision]]:
        decisions = [evaluator.evaluate(response_summary, metadata) for evaluator in self.evaluators]
        confidence = round(sum(decision.confidence for decision in decisions) / len(decisions), 2) if decisions else 0.0
        verified = bool(decisions) and all(decision.is_vulnerable for decision in decisions) and confidence >= self.verification_threshold
        return verified, confidence, decisions
