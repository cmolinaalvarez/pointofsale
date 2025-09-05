# app/security/input_validation.py
from __future__ import annotations

import json
import logging
import re
from typing import Any, Iterable, Callable, Awaitable, Mapping

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette import status
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.schemas.security_schemas import _sanitize  # sanitizador central

log = logging.getLogger("security")

# ---------------------------------------------------------------------
# Config por defecto (puedes mover/override con settings / kwargs)
# ---------------------------------------------------------------------
DEFAULT_MAX_BODY_BYTES = getattr(settings, "MAX_BODY_BYTES", 2 * 1024 * 1024)  # 2MB

# Patrones básicos para bloquear payloads obvios de SQLi/XSS (rápidos)
SQLI_RX = re.compile(
    r"(?i)\b(union\s+select|or\s+1=1|and\s+1=1|drop\s+table|;--|insert\s+into|update\s+\w+\s+set|delete\s+from)\b"
)
XSS_RX = re.compile(
    r"(?i)(<\s*/?\s*script\b|on\w+\s*=|javascript\s*:|document\.|window\.)"
)


def _iter_strings(value: Any) -> Iterable[str]:
    """Itera recursivamente cadenas dentro de dict/list/tupla/set."""
    if value is None:
        return
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _iter_strings(v)
    elif isinstance(value, (list, tuple, set)):
        for v in value:
            yield from _iter_strings(v)


def _looks_malicious(value: Any) -> bool:
    for s in _iter_strings(value):
        if SQLI_RX.search(s) or XSS_RX.search(s):
            return True
    return False


def _apply_field_max(data: Any, field_max: Mapping[str, int]) -> Any:
    """
    Enforce longitudes máximas por nombre de campo (clave exacta).
    - Si el valor es str y la clave está en field_max, recorta a ese tamaño.
    - Aplica recursivamente en dicts y contenedores.
    """
    if not field_max:
        return data

    if isinstance(data, dict):
        new_d = {}
        for k, v in data.items():
            v2 = _apply_field_max(v, field_max)
            if isinstance(v2, str) and k in field_max:
                maxlen = field_max[k]
                if maxlen is not None and maxlen >= 0 and len(v2) > maxlen:
                    v2 = v2[:maxlen]
            new_d[k] = v2
        return new_d

    if isinstance(data, list):
        return [_apply_field_max(x, field_max) for x in data]
    if isinstance(data, tuple):
        return tuple(_apply_field_max(x, field_max) for x in data)
    if isinstance(data, set):
        return {_apply_field_max(x, field_max) for x in data}

    return data


class BodySanitizationMiddleware(BaseHTTPMiddleware):
    """
    - Procesa solo JSON (application/json) en POST/PUT/PATCH.
    - Limita tamaño por Content-Length y por bytes leídos.
    - Sanitiza con `_sanitize` (recursivo).
    - Rechaza payloads que hagan match con patrones obvios SQLi/XSS.
    - Enforce longitudes máximas por campo (opcional vía `field_max`).
    - Reinyecta el JSON sanitizado al request.
    - `skip_paths`: lista de rutas exactas a omitir (opcional).
    - No afecta form-data/x-www-form-urlencoded (p.ej. /auth/token).
    """

    def __init__(
        self,
        app,
        *,
        max_body_bytes: int | None = None,
        field_max: Mapping[str, int] | None = None,
        skip_paths: Iterable[str] | None = None,
    ):
        super().__init__(app)
        self.max_body_bytes = int(max_body_bytes or DEFAULT_MAX_BODY_BYTES)
        self.field_max = dict(field_max or {})
        self.skip_paths = set(skip_paths or ())

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in self.skip_paths:
            return await call_next(request)

        ctype = request.headers.get("content-type", "").lower()
        method = request.method.upper()

        # Ignorar si no es JSON o métodos sin body típico
        if "application/json" not in ctype or method not in {"POST", "PUT", "PATCH"}:
            return await call_next(request)

        # Límite por Content-Length (si llega)
        try:
            clen = int(request.headers.get("content-length", "0"))
            if clen > self.max_body_bytes:
                return JSONResponse(
                    {"detail": "Payload demasiado grande"},
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )
        except ValueError:
            pass

        try:
            raw = await request.body()
        except Exception:
            log.exception("No se pudo leer el body")
            return JSONResponse({"detail": "Invalid JSON"}, status_code=400)

        if len(raw) > self.max_body_bytes:
            return JSONResponse(
                {"detail": "Payload demasiado grande"},
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        if not raw:
            return await call_next(request)

        # Parsear JSON
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            return JSONResponse({"detail": "JSON inválido"}, status_code=400)

        # Sanitizar (centralizado)
        try:
            data = _sanitize(data)
        except ValueError:
            return JSONResponse({"detail": "Payload malicioso detectado"}, status_code=400)

        # Heurística anti SQLi/XSS
        if _looks_malicious(data):
            log.warning("Payload bloqueado por patrones SQLi/XSS en %s", request.url.path)
            return JSONResponse({"detail": "Input rejected by validator"}, status_code=400)

        # Enforce tamaños por campo (si se configuró)
        if self.field_max:
            data = _apply_field_max(data, self.field_max)

        # Reinyectar body sanitizado
        new_body = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

        async def receive():
            return {"type": "http.request", "body": new_body, "more_body": False}

        request = Request(request.scope, receive=receive)
        request.state.sanitized_body = True

        try:
            return await call_next(request)
        except Exception:
            log.exception("input_validation middleware error")
            return JSONResponse({"detail": "Invalid JSON"}, status_code=400)


# Alias para compatibilidad con importaciones antiguas
InputValidationMiddleware = BodySanitizationMiddleware

# ---------------------------------------------------------------------
# Utilidad para validar uploads (CSV import)
# ---------------------------------------------------------------------
ALLOWED_IMPORT_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "text/plain",
    "application/vnd.ms-excel",
}
MAX_IMPORT_BYTES = getattr(settings, "MAX_IMPORT_BYTES", 5 * 1024 * 1024)  # 5MB


def validate_upload(
    file: UploadFile,
    *,
    allowed_types: set[str] = ALLOWED_IMPORT_CONTENT_TYPES,
    max_bytes: int = MAX_IMPORT_BYTES,
) -> bytes:
    ctype = (file.content_type or "").lower()
    if ctype not in allowed_types:
        raise HTTPException(status_code=415, detail="Tipo de archivo no permitido")

    raw = file.file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Archivo vacío")

    if len(raw) > max_bytes:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande")

    return raw


__all__ = [
    "BodySanitizationMiddleware",
    "InputValidationMiddleware",
    "validate_upload",
]
