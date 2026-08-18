"""n8n boundary: production work is delegated, while demo mode remains local and synthetic."""
import hashlib
import hmac
import json
import httpx
from .config import settings


class Orchestrator:
    def start_campaign(self, campaign_id: str, target_id: str, budgets: dict[str, int]) -> None:
        body = json.dumps({"campaign_id": campaign_id, "target_id": target_id, "budgets": budgets}, separators=(",", ":")).encode()
        signature = hmac.new(settings.n8n_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
        response = httpx.post(f"{settings.n8n_base_url.rstrip('/')}/webhook/swarmshield-campaign-start", content=body, headers={"Content-Type": "application/json", "X-SwarmShield-Signature": signature}, timeout=10)
        response.raise_for_status()


def valid_signature(body: bytes, signature: str | None) -> bool:
    expected = hmac.new(settings.n8n_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    return bool(signature) and hmac.compare_digest(expected, signature)
