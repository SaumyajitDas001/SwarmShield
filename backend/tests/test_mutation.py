import pytest
from app.mutation import mutate_genome


def test_mutation_is_allowlisted_and_preserves_genome_fields():
    child, record = mutate_genome({"entry_vector": "retrieved content"}, "context_variation")
    assert child["entry_vector"] == "retrieved content"
    assert child["context_strategy"] == "retrieval_relevance_camouflage"
    assert record["mutation_type"] == "context_variation"
    with pytest.raises(ValueError):
        mutate_genome({}, "arbitrary_payload")
