from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resp = await call_next(request)

        # Headers base
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        resp.headers["Permissions-Policy"] = "geolocation=(), microphone=()"

        # CSP reforzada
        if request.url.path == "/docs":
            resp.headers["Content-Security-Policy"] = (
                "default-src 'self' https://cdn.jsdelivr.net; "
                "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "img-src 'self' https://cdn.jsdelivr.net data:; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
            )
        else:
            resp.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
            )

        # No almacenar respuestas sensibles de auth
        if request.url.path.startswith("/auth"):
            resp.headers["Cache-Control"] = "no-store"

        return resp
