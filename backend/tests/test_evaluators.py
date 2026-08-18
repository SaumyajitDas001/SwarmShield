from app.evaluators import CompositeEvaluator, ContextSeparationRuleEvaluator


def test_controlled_evidence_requires_explicit_verification_threshold():
    evaluator = CompositeEvaluator([ContextSeparationRuleEvaluator()], verification_threshold=.75)
    verified, confidence, decisions = evaluator.evaluate(
        "Synthetic demo observation: retrieved context affected simulated tool-selection intent.",
        {"synthetic": True, "redacted": True},
    )
    assert verified is True
    assert confidence == .82
    assert decisions[0].evidence["redacted"] is True


def test_unmatched_observation_does_not_create_a_verification_decision():
    evaluator = CompositeEvaluator([ContextSeparationRuleEvaluator()])
    verified, confidence, _ = evaluator.evaluate("A normal response", {"synthetic": True})
    assert verified is False
    assert confidence < .75
