# app/utils/security_utils.py
from __future__ import annotations
import re
from typing import Any, Dict, Iterable

# --- Patrones para sanitización básica de XSS ---
_SCRIPT_TAG_RE = re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.I | re.S)
_EVENT_HANDLER_RE = re.compile(r"\s+on\w+\s*=\s*(\".*?\"|'.*?'|[^\s>]+)", re.I | re.S)
_JS_PROTO_RE = re.compile(r"(?i)javascript\s*:")
_DATA_PROTO_RE = re.compile(r"(?i)data\s*:[^,]*,")
_CTRL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")

# --- Longitudes máximas por campo/contexto (ajusta a tu dominio) ---
FIELD_MAX_LENGTHS: Dict[str, int] = {
    "search": 100,
    "code": 20,
    "name": 100,
    "description": 500,
    "basis": 20,
    "username": 50,
    "full_name": 150,
    "email": 254,
}

def sanitize_text(s: str | None, max_len: int | None = None) -> str:
    """Limpia controles y XSS triviales. No parsea HTML."""
    if s is None:
        return ""
    s = str(s)
    s = _CTRL_RE.sub("", s)
    s = _SCRIPT_TAG_RE.sub("", s)
    s = _EVENT_HANDLER_RE.sub("", s)
    s = _JS_PROTO_RE.sub("", s)
    s = _DATA_PROTO_RE.sub("", s)
    s = s.strip()
    if max_len and max_len > 0:
        s = s[:max_len]
    return s

def escape_like(term: str) -> str:
    """Escapa comodines para LIKE/ILIKE. Usar con escape=\"\\\"."""
    term = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return term

def is_safe_redirect(url: str, allowed_hosts: Iterable[str]) -> bool:
    """Permite rutas relativas o http(s) hacia hosts en lista blanca."""
    if not url:
        return False
    if url.startswith(("/", "./", "../")):
        return True
    m = re.match(r"^(?i)(https?)://([^/]+)", url.strip())
    if not m:
        return False
    host = m.group(2).lower()
    return host in {h.lower() for h in allowed_hosts}

class SecurityUtils:
    """
    Utilidades de seguridad usadas por CRUDs, Schemas y routers.
    Se expone FIELD_MAX_LENGTHS para uso en Pydantic: SecurityUtils.FIELD_MAX_LENGTHS
    """
    FIELD_MAX_LENGTHS: Dict[str, int] = FIELD_MAX_LENGTHS

    @staticmethod
    def sanitize_input(value: str, context: str = "") -> str:
        limit = SecurityUtils.FIELD_MAX_LENGTHS.get(context or "", None)
        return sanitize_text(value, max_len=limit)

    @staticmethod
    def sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitiza dict campo a campo respetando límites por nombre de campo."""
        if not isinstance(data, dict):
            return {}
        cleaned: Dict[str, Any] = {}
        for k, v in data.items():
            if isinstance(v, str):
                limit = SecurityUtils.FIELD_MAX_LENGTHS.get(k, None)
                cleaned[k] = sanitize_text(v, max_len=limit)
            elif isinstance(v, dict):
                cleaned[k] = SecurityUtils.sanitize_data(v)
            elif isinstance(v, list):
                limit = SecurityUtils.FIELD_MAX_LENGTHS.get(k, None)
                cleaned[k] = [
                    sanitize_text(x, max_len=limit) if isinstance(x, str) else x
                    for x in v
                ]
            else:
                cleaned[k] = v
        return cleaned

    @staticmethod
    def escape_like(term: str) -> str:
        return escape_like(term)

    @staticmethod
    def is_safe_redirect(url: str, allowed_hosts: Iterable[str]) -> bool:
        return is_safe_redirect(url, allowed_hosts)

__all__ = ["SecurityUtils", "FIELD_MAX_LENGTHS", "sanitize_text", "escape_like", "is_safe_redirect"]
