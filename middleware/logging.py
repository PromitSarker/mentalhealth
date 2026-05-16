"""Logging middleware for request/response tracking."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging
import json
import time
from datetime import datetime


logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logs all requests and responses with appropriate levels."""

    async def dispatch(self, request: Request, call_next):
        """Log request and response details."""
        
        start_time = time.time()
        
        # Log request
        request_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", ""),
        }
        
        logger.info(f"REQUEST: {json.dumps(request_log)}")
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            response_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
            }
            
            # Determine log level based on status code
            if response.status_code >= 500:
                logger.error(f"RESPONSE: {json.dumps(response_log)}")
            elif response.status_code >= 400:
                logger.warning(f"RESPONSE: {json.dumps(response_log)}")
            else:
                logger.info(f"RESPONSE: {json.dumps(response_log)}")
            
            response.headers["X-Process-Time"] = str(process_time)
            return response
        
        except Exception as e:
            process_time = time.time() - start_time
            
            error_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path,
                "error": str(e),
                "process_time_ms": round(process_time * 1000, 2),
            }
            
            logger.error(f"ERROR: {json.dumps(error_log)}")
            raise


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Audit logs for compliance (GDPR, insurance transparency)."""

    AUDIT_PATHS = [
        "/ai/chat/interact",
        "/ai/report/generate",
        "/gdpr/delete",
    ]

    async def dispatch(self, request: Request, call_next):
        """Log audit-relevant requests."""
        
        if request.url.path in self.AUDIT_PATHS:
            try:
                body = await request.body()
                audit_log = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": request.url.path,
                    "method": request.method,
                    "client_ip": request.client.host if request.client else "unknown",
                    "request_body": body.decode() if body else None,
                }
                logger.warning(f"AUDIT: {json.dumps(audit_log)}")
            except Exception as e:
                logger.error(f"Audit logging error: {str(e)}")
        
        response = await call_next(request)
        return response


def get_logging_middleware() -> type:
    """Get logging middleware class."""
    return LoggingMiddleware
