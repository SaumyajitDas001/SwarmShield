import pytest
from app.memory import MemoryItem, retrieve_relevant, validate_memory


def test_memory_validates_types_confidence_and_retrieves():
    item = validate_memory(MemoryItem(memory_type="DISCOVERY", content="retrieval tool boundary", confidence=.8, agent="PromptSafety"))
    assert retrieve_relevant([item], "tool boundary")[0] == item
    with pytest.raises(ValueError):
        validate_memory(MemoryItem(memory_type="UNKNOWN", content="x", confidence=.8, agent="agent"))
    with pytest.raises(ValueError):
        validate_memory(MemoryItem(memory_type="DISCOVERY", content="x", confidence=1.2, agent="agent"))
