from app.graph import build_evidence_chain


def test_chain_contains_only_evidence_supported_relationships():
    graph = build_evidence_chain(attempts=[{"id": "a1", "test_case": "context", "agent": "PromptSafety"}], memories=[{"id": "m1", "memory_type": "DISCOVERY", "confidence": .82, "source_attack_id": "a1"}], findings=[{"id": "f1", "title": "Boundary influence", "severity": "Medium", "risk_score": 52}], evaluations=[{"observation_id": "o1", "is_vulnerable": True}])
    assert {node["kind"] for node in graph["nodes"]} == {"attack", "discovery", "finding"}
    assert any(edge["kind"] == "DISCOVERED" for edge in graph["edges"])
    assert any(edge["kind"] == "CAUSED" for edge in graph["edges"])
    assert graph["supported_evaluations"] == 1
