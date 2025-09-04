from __future__ import annotations
import re, html
from urllib.parse import urlparse
from typing import Any, Dict

SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC|ALTER|CREATE|TRUNCATE)\b)",
    r"(\-\-|\#|\/\*)",
    r"(\b(OR|AND)\s+['\"]?[01]['\"]?\s*[=<>])",
    r"(;|\|&)",
]
SENSITIVE_FIELDS = {"password","token","secret","authorization","api_key"}

def sanitize_text(value: str, *, max_len: int | None = None) -> str:
    if max_len is not None: value = value[:max_len]
    value = re.sub(r"<\s*\/?\s*script[^>]*>", "", value, flags=re.I)
    value = re.sub(r"on\w+\s*=", "", value, flags=re.I)
    value = re.sub(r"javascript\s*:", "", value, flags=re.I)
    return html.escape(value, quote=True)

def sanitize_dict(d: Dict[str, Any], field_max: Dict[str,int] | None = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k,v in d.items():
        if isinstance(v, str): out[k] = sanitize_text(v, max_len=(field_max or {}).get(k))
        elif isinstance(v, dict): out[k] = sanitize_dict(v, field_max)
        elif isinstance(v, list): out[k] = [sanitize_text(x) if isinstance(x, str) else x for x in v]
        else: out[k] = v
    return out

def looks_like_sql_injection(text: str) -> bool:
    return any(re.search(p, text, flags=re.I) for p in SQL_INJECTION_PATTERNS)

def obfuscate_sensitive(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: ("***REDACTED***" if k.lower() in SENSITIVE_FIELDS else v) for k,v in d.items()}

def is_safe_redirect(url: str, allowed_hosts: list[str] | None = None) -> bool:
    allowed_hosts = allowed_hosts or []
    p = urlparse(url)
    if not p.netloc:  # relativo
        return True
    return p.netloc.lower() in [h.lower() for h in allowed_hosts]
