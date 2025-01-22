from fastapi import Request, HTTPException
from typing import Dict, Tuple, Optional
import time
from app.core.logging import setup_logger
from app.core.config import get_settings

logger = setup_logger(__name__)
settings = get_settings()

class RateLimiter:
    """Rate limiting implementation."""
    
    def __init__(self) -> None:
        self.requests: Dict[str, Dict[str, list]] = {}
        self.limits = {
            "/api/v1/auth/signup": 5,  # 5 requests per minute
            "/api/v1/auth/token": 10,  # 10 requests per minute
            "default": settings.RATE_LIMIT_PER_MINUTE
        }

    def is_allowed(self, ip: str, path: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request is allowed under rate limiting rules.
        
        Args:
            ip: Client IP address
            path: Request path
            
        Returns:
            Tuple[bool, Optional[int]]: (is_allowed, retry_after_seconds)
        """
        try:
            now = time.time()
            minute_ago = now - 60

            if ip not in self.requests:
                self.requests[ip] = {}
            if path not in self.requests[ip]:
                self.requests[ip][path] = []

            # Clean old requests
            self.requests[ip][path] = [
                req for req in self.requests[ip][path] 
                if req > minute_ago
            ]

            limit = self.limits.get(path, self.limits["default"])

            if len(self.requests[ip][path]) >= limit:
                retry_after = 60 - int(now - self.requests[ip][path][0])
                return False, retry_after

            self.requests[ip][path].append(now)
            return True, None
            
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            return True, None  # Allow request in case of error

rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware for rate limiting requests.
    
    Args:
        request: FastAPI request
        call_next: Next middleware in chain
        
    Returns:
        Response: FastAPI response
    """
    try:
        client_ip = request.client.host
        path = request.url.path
        
        is_allowed, retry_after = rate_limiter.is_allowed(client_ip, path)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for IP: {client_ip} on path: {path}")
            raise HTTPException(
                status_code=429,
                detail="Too many requests",
                headers={"Retry-After": str(retry_after)}
            )
        
        response = await call_next(request)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limiting middleware error: {str(e)}")
        return await call_next(request)