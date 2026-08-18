import sys
sys.path.insert(0, "backend")
from app.orchestrator import valid_signature
from app.config import settings
import hashlib, hmac

def test_signed_n8n_callback_is_verified():
    body = b'{"event":"safe"}'
    signature = hmac.new(settings.n8n_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    assert valid_signature(body, signature)
    assert not valid_signature(body, "tampered")
