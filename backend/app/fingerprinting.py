"""Capability fingerprinting from declared target metadata only.

Fingerprinting is descriptive; it does not probe or exploit a target.
"""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TargetFingerprint:
    chat: bool
    rag: bool
    tools: bool
    structured_output: bool
    vision: bool
    streaming: bool
    declared_tools: tuple[str, ...]
    source: str = "declared_metadata"

    def as_dict(self) -> dict[str, Any]:
        return {
            "chat": self.chat,
            "rag": self.rag,
            "tools": self.tools,
            "structured_output": self.structured_output,
            "vision": self.vision,
            "streaming": self.streaming,
            "declared_tools": list(self.declared_tools),
            "source": self.source,
        }


def fingerprint_architecture(architecture: dict[str, Any]) -> TargetFingerprint:
    nodes = architecture.get("nodes", [])
    node_types = {str(node.get("type", "")).lower() for node in nodes if isinstance(node, dict)}
    capabilities = {str(value).lower() for value in architecture.get("capabilities", [])}
    declared_tools = tuple(str(value) for value in architecture.get("declared_tools", []))
    return TargetFingerprint(
        chat="chat" in capabilities or not capabilities or "llm" in node_types,
        rag="rag" in capabilities or "rag" in node_types,
        tools="tools" in capabilities or "tool" in node_types,
        structured_output="structured_output" in capabilities,
        vision="vision" in capabilities or "vision" in node_types,
        streaming="streaming" in capabilities,
        declared_tools=declared_tools,
    )


def active_agent_categories(fingerprint: TargetFingerprint) -> tuple[str, ...]:
    categories = ["prompt_injection", "privacy", "output_security"]
    if fingerprint.rag:
        categories.append("rag")
    if fingerprint.tools:
        categories.extend(["tool_abuse", "agency"])
    if fingerprint.vision:
        categories.append("multimodal")
    return tuple(categories)
