from typing import Any, Dict, Optional
import time

# Simple in-memory idempotency cache (24h TTL)
# In production v2.0, replace with Redis
_IDEMPOTENCY_CACHE: Dict[str, Dict[str, Any]] = {}
TTL_SECONDS = 86400  # 24 hours


def get_idempotent_response(key: str) -> Optional[Dict[str, Any]]:
    if key in _IDEMPOTENCY_CACHE:
        entry = _IDEMPOTENCY_CACHE[key]
        if time.time() - entry["timestamp"] < TTL_SECONDS:
            return entry["response"]
        else:
            del _IDEMPOTENCY_CACHE[key]
    return None


def store_idempotent_response(key: str, response: Dict[str, Any]):
    _IDEMPOTENCY_CACHE[key] = {
        "timestamp": time.time(),
        "response": response,
    }
