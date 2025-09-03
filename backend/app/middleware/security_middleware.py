from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import re
from typing import Callable, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter: Dict[str, list] = {}
        self.blocked_ips: Dict[str, float] = {}
        self.rate_limit = getattr(settings, 'RATE_LIMIT', 100)
        self.burst_limit = getattr(settings, 'BURST_LIMIT', 15)

    async def dispatch(self, request: Request, call_next: Callable):
        client_ip = request.client.host
        
        # 1. Verificar IP bloqueada
        if self._is_ip_blocked(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas solicitudes. IP temporalmente bloqueada."}
            )

        # 2. Rate limiting
        if not self._check_rate_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas solicitudes"}
            )

        # 3. Validar headers de seguridad
        security_errors = self._validate_request_headers(request)
        if security_errors:
            return JSONResponse(
                status_code=400,
                content={"detail": security_errors}
            )

        # 4. Procesar solicitud
        response = await call_next(request)
        
        # 5. Agregar headers de seguridad a la respuesta (CON REQUEST)
        self._add_security_headers(response, request)
        
        return response

    def _check_rate_limit(self, ip: str) -> bool:
        current_time = time.time()
        window_start = current_time - 60  # Ventana de 1 minuto
        
        # Limpiar registros antiguos
        self.rate_limiter[ip] = [t for t in self.rate_limiter.get(ip, []) if t > window_start]
        
        if len(self.rate_limiter[ip]) >= self.rate_limit:
            if len(self.rate_limiter[ip]) >= self.rate_limit + self.burst_limit:
                self.blocked_ips[ip] = current_time + 300  # Bloquear por 5 minutos
            return False
        
        self.rate_limiter.setdefault(ip, []).append(current_time)
        return True

    def _is_ip_blocked(self, ip: str) -> bool:
        block_time = self.blocked_ips.get(ip, 0)
        if block_time > time.time():
            return True
        elif ip in self.blocked_ips:
            del self.blocked_ips[ip]
        return False

    def _validate_request_headers(self, request: Request) -> str:
        """Valida headers de seguridad en la solicitud"""
        errors = []
        
        # Validar Content-Type para requests con body
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('content-type', '')
            if not content_type.startswith('application/json'):
                errors.append("Content-Type debe ser application/json")
        
        # Validar User-Agent
        user_agent = request.headers.get('user-agent', '')
        if not user_agent or len(user_agent) > 256:
            errors.append("User-Agent inválido")
        
        return "; ".join(errors) if errors else ""

    def _add_security_headers(self, response, request: Request = None):
        """Agrega headers de seguridad con CSP personalizado para Swagger"""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=()"
        }
        
        # CSP diferente para Swagger UI
        if request and request.url.path == "/docs":
            security_headers["Content-Security-Policy"] = (
                "default-src 'self' https://cdn.jsdelivr.net; "
                "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "img-src 'self' https://cdn.jsdelivr.net data:; "
                "font-src 'self' https://cdn.jsdelivr.net;"
            )
        else:
            security_headers["Content-Security-Policy"] = "default-src 'self'"
        
        for header, value in security_headers.items():
            response.headers[header] = value