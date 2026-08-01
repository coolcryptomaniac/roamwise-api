import time
from typing import Optional, Dict
from app.core.config import get_settings

settings = get_settings()

# In-memory store for demo. Use Redis in production.
_request_store: Dict[str, list] = {}

def check_rate_limit(api_key: str, tier: str) -> tuple[bool, int, int]:
    """
    Check if request is within rate limit.
    Returns: (allowed, remaining, reset_in_seconds)
    """
    limits = {
        "basic": settings.rate_limit_basic,
        "pro": settings.rate_limit_pro,
        "enterprise": settings.rate_limit_enterprise,
    }
    limit = limits.get(tier, settings.rate_limit_basic)

    now = time.time()
    window = 60  # 1 minute window

    if api_key not in _request_store:
        _request_store[api_key] = []

    # Clean old requests
    _request_store[api_key] = [t for t in _request_store[api_key] if now - t < window]

    current_count = len(_request_store[api_key])

    if current_count >= limit:
        reset_in = int(window - (now - _request_store[api_key][0]))
        return False, 0, reset_in

    _request_store[api_key].append(now)
    remaining = limit - current_count - 1
    return True, remaining, 0

def get_rate_limit_headers(allowed: bool, remaining: int, reset_in: int, tier: str) -> dict:
    limits = {
        "basic": settings.rate_limit_basic,
        "pro": settings.rate_limit_pro,
        "enterprise": settings.rate_limit_enterprise,
    }
    return {
        "X-RateLimit-Limit": str(limits.get(tier, 20)),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset_in),
        "X-RateLimit-Tier": tier,
    }
