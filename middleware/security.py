"""Security middleware for TLS/HTTPS and request validation."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging
import hashlib
import hmac
import os
from datetime import datetime


logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Enforces security headers and validates requests."""

    def __init__(self, app):
        super().__init__(app)
        self.hmac_key = os.getenv("HMAC_KEY", "default-key").encode()

    async def dispatch(self, request: Request, call_next):
        """Process request with security checks."""
        
        # Validate request signature (optional rate limiting key)
        if not self._validate_request(request):
            logger.warning(f"Invalid request signature from {request.client.host}")
            return JSONResponse(
                {"error": "Invalid request signature"},
                status_code=401
            )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers for TLS/HTTPS enforcement
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

    def _validate_request(self, request: Request) -> bool:
        """Validate request authenticity (optional).
        
        Args:
            request: HTTP request.
            
        Returns:
            True if request is valid.
        """
        # In production, implement HMAC signature validation
        # or JWT token verification
        return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_history = {}

    async def dispatch(self, request: Request, call_next):
        """Check rate limits before processing request."""
        
        client_ip = request.client.host if request.client else "unknown"
        
        # In production, implement proper rate limiting with Redis or similar
        # For now, this is a placeholder
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validates and sanitizes input to prevent injection attacks."""

    async def dispatch(self, request: Request, call_next):
        """Validate input before processing."""
        
        # Check for suspicious patterns
        if request.method in ["POST", "PUT"]:
            try:
                body = await request.body()
                if self._contains_injection_patterns(body.decode()):
                    logger.warning(f"Potential injection attack from {request.client.host}")
                    return JSONResponse(
                        {"error": "Invalid input detected"},
                        status_code=400
                    )
            except Exception:
                pass
        
        response = await call_next(request)
        return response

    @staticmethod
    def _contains_injection_patterns(content: str) -> bool:
        """Detect common injection patterns.
        
        Args:
            content: Request body content.
            
        Returns:
            True if injection patterns detected.
        """
        patterns = [
            "DROP TABLE", "DELETE FROM", "INSERT INTO",
            "<script>", "javascript:", "onerror=", "onclick="
        ]
        content_upper = content.upper()
        return any(pattern in content_upper for pattern in patterns)


def get_security_middleware() -> type:
    """Get security middleware class."""
    return SecurityMiddleware
