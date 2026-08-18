"""Safe, explainable Attack DNA mutations.

Mutations alter metadata describing a validation case. They do not generate
unbounded exploit payloads or change target scope.
"""
from typing import Any

ALLOWED_MUTATIONS: dict[str, tuple[str, str]] = {
    "context_variation": ("context_strategy", "retrieval_relevance_camouflage"),
    "role_variation": ("role_strategy", "reviewer_context"),
    "format_variation": ("format_strategy", "structured_validation"),
    "multi_turn_continuation": ("conversation_strategy", "bounded_follow_up"),
    "indirect_content_variation": ("delivery_strategy", "document_metadata"),
}


def mutate_genome(genome: dict[str, Any], mutation_type: str) -> tuple[dict[str, Any], dict[str, str]]:
    if mutation_type not in ALLOWED_MUTATIONS:
        raise ValueError("Unsupported mutation type")
    field, value = ALLOWED_MUTATIONS[mutation_type]
    child = dict(genome)
    previous = str(child.get(field, "unset"))
    child[field] = value
    return child, {"feature": field, "from": previous, "to": value, "mutation_type": mutation_type}
