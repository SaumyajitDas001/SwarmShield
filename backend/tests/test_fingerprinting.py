from app.fingerprinting import active_agent_categories, fingerprint_architecture


def test_fingerprint_uses_declared_capabilities_without_probing():
    fingerprint = fingerprint_architecture({
        "capabilities": ["chat", "rag", "tools"],
        "declared_tools": ["search_docs", "calculator"],
        "nodes": [],
    })
    assert fingerprint.chat and fingerprint.rag and fingerprint.tools
    assert not fingerprint.vision
    assert active_agent_categories(fingerprint) == ("prompt_injection", "privacy", "output_security", "rag", "tool_abuse", "agency")


def test_fingerprint_does_not_activate_irrelevant_agents():
    fingerprint = fingerprint_architecture({"capabilities": ["chat"], "nodes": []})
    assert active_agent_categories(fingerprint) == ("prompt_injection", "privacy", "output_security")
