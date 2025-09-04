from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
import logging

log = logging.getLogger("security")

def install_exception_handlers(app):
    @app.exception_handler(HTTPException)
    async def http_exc(request: Request, exc: HTTPException):
        if exc.status_code >= 500:
            log.error("http_error", extra={"path": str(request.url), "method": request.method, "status": exc.status_code})
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exc(request: Request, exc: RequestValidationError):
        log.warning("validation_error", extra={"path": str(request.url), "method": request.method})
        if settings.APP_ENV == "production":
            return JSONResponse({"detail": "Invalid request"}, status_code=422)
        return JSONResponse({"detail": exc.errors()}, status_code=422)

    @app.exception_handler(Exception)
    async def unhandled_exc(request: Request, exc: Exception):
        log.error("unhandled_error", extra={"path": str(request.url), "method": request.method})
        msg = "Internal server error" if settings.APP_ENV == "production" else str(exc)
        return JSONResponse({"detail": msg}, status_code=500)