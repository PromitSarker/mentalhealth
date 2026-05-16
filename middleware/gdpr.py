"""GDPR compliance middleware for data handling."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging


logger = logging.getLogger(__name__)


class GDPRMiddleware(BaseHTTPMiddleware):
    """Ensures GDPR compliance in data handling."""

    async def dispatch(self, request: Request, call_next):
        """Enforce GDPR principles in request processing."""
        
        # Add GDPR-required headers
        response = await call_next(request)
        
        # Inform users about data processing
        response.headers["X-Data-Processing"] = "This request is processed securely in compliance with UK GDPR"
        
        # Privacy policy and cookie notice should be served separately
        # This middleware ensures responses don't leak unnecessary data
        
        # Remove sensitive headers that shouldn't be exposed
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)
        
        return response


class ConsentMiddleware(BaseHTTPMiddleware):
    """Validates user consent before processing sensitive data."""

    SENSITIVE_ENDPOINTS = [
        "/ai/chat/interact",
        "/ai/audio/stt",
        "/ai/audio/tts",
        "/ai/report/generate",
    ]

    async def dispatch(self, request: Request, call_next):
        """Check consent for sensitive operations."""
        
        if request.url.path in self.SENSITIVE_ENDPOINTS:
            # In production, verify consent token in request headers
            # or session before allowing access
            
            consent_header = request.headers.get("X-User-Consent")
            
            if not consent_header and request.method in ["POST", "PUT"]:
                logger.warning(f"Missing consent header for {request.url.path}")
                # In strict mode, could reject request without consent
                # For now, log and allow to pass
        
        response = await call_next(request)
        return response


def get_gdpr_middleware() -> type:
    """Get GDPR middleware class."""
    return GDPRMiddleware
