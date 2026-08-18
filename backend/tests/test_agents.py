from app.agents import active_descriptors, catalog
from app.fingerprinting import fingerprint_architecture

def test_catalog_activates_agents_from_target_capabilities():
    assert len(catalog()) == 7
    categories = {item.category for item in active_descriptors(fingerprint_architecture({"capabilities": ["chat", "rag", "tools"]}))}
    assert {"prompt_injection", "privacy", "output_security", "rag", "tool_abuse", "agency"} <= categories
    assert "multimodal" not in categories
