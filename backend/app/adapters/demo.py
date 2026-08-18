"""Synthetic adapter for the built-in authorized demonstration target."""
from .base import TargetRequest, TargetResponse


class DemoTargetAdapter:
    """Produces deterministic, redacted telemetry and never makes a network call."""

    async def send(self, request: TargetRequest) -> TargetResponse:
        return TargetResponse(
            text="Synthetic demo observation: retrieved context affected simulated tool-selection intent.",
            latency_ms=190,
            estimated_tokens=260,
            metadata={"synthetic": True, "test_case": request.test_case, "redacted": True},
        )

    async def metadata(self) -> dict[str, object]:
        return {"chat": True, "rag": True, "tools": True, "network": False}

    async def health(self) -> bool:
        return True
