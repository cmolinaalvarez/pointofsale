from slowapi import Limiter
from slowapi.util import get_remote_address
import os

DEFAULT_LIMIT = os.getenv("RATE_LIMIT", "60/minute")
limiter = Limiter(key_func=get_remote_address, default_limits=[DEFAULT_LIMIT])

def limit(rule: str | None = None):
    return limiter.limit(rule or DEFAULT_LIMIT)