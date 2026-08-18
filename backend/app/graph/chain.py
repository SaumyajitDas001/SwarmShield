"""Evidence-backed attack-chain projection from persisted campaign records."""
from typing import Any


def build_evidence_chain(*, attempts: list[dict[str, Any]], memories: list[dict[str, Any]], findings: list[dict[str, Any]], evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    nodes, edges = [], []
    supported = sum(1 for item in evaluations if item.get("is_vulnerable"))
    for item in attempts:
        nodes.append({"id": f"attempt:{item['id']}", "kind": "attack", "label": item.get("test_case"), "agent": item.get("agent")})
    for item in memories:
        nodes.append({"id": f"memory:{item['id']}", "kind": "discovery", "label": item.get("memory_type"), "confidence": item.get("confidence")})
        if item.get("source_attack_id"):
            edges.append({"id": f"derived:{item['id']}", "source": f"attempt:{item['source_attack_id']}", "target": f"memory:{item['id']}", "kind": "DISCOVERED"})
    for item in findings:
        nodes.append({"id": f"finding:{item['id']}", "kind": "finding", "label": item.get("title"), "severity": item.get("severity"), "risk_score": item.get("risk_score")})
    if supported:
        for attempt in attempts:
            if any(str(memory.get("source_attack_id")) == str(attempt["id"]) for memory in memories):
                for finding in findings:
                    edges.append({"id": f"caused:{attempt['id']}:{finding['id']}", "source": f"attempt:{attempt['id']}", "target": f"finding:{finding['id']}", "kind": "CAUSED"})
    return {"nodes": nodes, "edges": edges, "supported_evaluations": supported}
