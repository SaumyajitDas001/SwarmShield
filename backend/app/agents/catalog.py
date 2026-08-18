"""Capability-aware catalog for the built-in bounded validation agents."""
from dataclasses import dataclass
from .base import BaseAgent
from .prompt_safety import PromptSafetyAgent
from ..fingerprinting import TargetFingerprint

@dataclass(frozen=True)
class AgentDescriptor:
    name: str
    category: str
    description: str
    required_capability: str | None = None

DESCRIPTORS = (
    AgentDescriptor("PromptSafety", "prompt_injection", "Validates instruction and context separation."),
    AgentDescriptor("Privacy", "privacy", "Checks controlled leakage and metadata boundaries."),
    AgentDescriptor("OutputSecurity", "output_security", "Checks downstream output handling."),
    AgentDescriptor("RAGSafety", "rag", "Validates retrieved-content trust boundaries.", "rag"),
    AgentDescriptor("ToolSafety", "tool_abuse", "Validates declared tool policy boundaries.", "tools"),
    AgentDescriptor("AgencySafety", "agency", "Validates excessive-authority proposals.", "tools"),
    AgentDescriptor("MultimodalSafety", "multimodal", "Validates image-input boundaries.", "vision"),
)

def catalog() -> list[AgentDescriptor]: return list(DESCRIPTORS)
def active_descriptors(fingerprint: TargetFingerprint) -> list[AgentDescriptor]:
    values = fingerprint.as_dict()
    return [item for item in DESCRIPTORS if item.required_capability is None or values.get(item.required_capability, False)]
def instantiate(category: str) -> BaseAgent | None: return PromptSafetyAgent() if category == "prompt_injection" else None
