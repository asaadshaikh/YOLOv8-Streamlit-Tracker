"""
Rate limiting utilities
Implements token bucket algorithm for API rate limiting
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict
import time
from fastapi import HTTPException, status, Request
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from utils.logger import logger


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = requests_per_minute
        self.tokens: Dict[str, float] = defaultdict(lambda: requests_per_minute)
        self.last_update: Dict[str, datetime] = defaultdict(lambda: datetime.utcnow())
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        now = datetime.utcnow()
        last = self.last_update[identifier]
        
        # Refill tokens based on time passed
        time_passed = (now - last).total_seconds()
        tokens_to_add = (time_passed / 60.0) * self.tokens_per_minute
        
        self.tokens[identifier] = min(
            self.tokens_per_minute,
            self.tokens[identifier] + tokens_to_add
        )
        self.last_update[identifier] = now
        
        # Check if token available
        if self.tokens[identifier] >= 1.0:
            self.tokens[identifier] -= 1.0
            return True
        
        return False
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining tokens"""
        return int(self.tokens[identifier])


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_minute)
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier (IP address or user ID)
        client_id = request.client.host if request.client else "unknown"
        
        # Check rate limit
        if not self.rate_limiter.is_allowed(client_id):
            remaining = self.rate_limiter.get_remaining(client_id)
            logger.warning(f"Rate limit exceeded for {client_id}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again later.",
                headers={
                    "X-RateLimit-Limit": str(self.rate_limiter.requests_per_minute),
                    "X-RateLimit-Remaining": str(remaining),
                    "Retry-After": "60"
                }
            )
        
        response = await call_next(request)
        remaining = self.rate_limiter.get_remaining(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response

