from __future__ import annotations
import json, re, html
from typing import Any, Mapping
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException, status, UploadFile
from app.core.config import settings
import io

SCRIPT_RE = re.compile(r"<\s*\/?\s*script[^>]*>", re.I)
EVENT_HANDLER_RE = re.compile(r"on\w+\s*=", re.I)
JS_URL_RE = re.compile(r"javascript\s*:", re.I)

def _sanitize_str(s: str, max_len: int | None = None) -> str:
    if max_len is not None: s = s[:max_len]
    s = SCRIPT_RE.sub("", s); s = EVENT_HANDLER_RE.sub("", s); s = JS_URL_RE.sub("", s)
    return html.escape(s, quote=True)

def _walk_and_clean(obj: Any, field_max: Mapping[str,int] | None = None) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k,v in obj.items():
            out[k] = _walk_and_clean(v, field_max)
            if isinstance(v, str) and field_max and k in field_max:
                out[k] = _sanitize_str(v, max_len=field_max[k])
        return out
    if isinstance(obj, list): return [_walk_and_clean(v, field_max) for v in obj]
    if isinstance(obj, str):  return _sanitize_str(obj)
    return obj

class BodySanitizationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, field_max: Mapping[str,int] | None = None):
        super().__init__(app); self.field_max = field_max or {}
    async def dispatch(self, request: Request, call_next):
        if request.headers.get("content-type","").lower().startswith("application/json"):
            raw = await request.body()
            try: data = json.loads(raw.decode("utf-8"))
            except Exception: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")
            cleaned = _walk_and_clean(data, self.field_max)
            new_body = json.dumps(cleaned).encode("utf-8")
            async def receive(): return {"type":"http.request","body":new_body,"more_body":False}
            request._receive = receive  # type: ignore
        return await call_next(request)
    
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "application/pdf"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
def validate_upload(file: UploadFile):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
def validate_upload(file: UploadFile) -> bytes:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type")
    max_bytes = settings.MAX_IMPORT_FILE_SIZE_MB * 1024 * 1024
    buf = io.BytesIO()
    while True:
        chunk = file.file.read(65536)
        if not chunk:
            break
        buf.write(chunk)
        if buf.tell() > max_bytes:
            raise HTTPException(status_code=400, detail="File too large")
    return buf.getvalue()
