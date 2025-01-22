from fastapi import Request
import time
from app.core.logging import setup_logger

logger = setup_logger(__name__)

async def logging_middleware(request: Request, call_next):
    """
    Middleware for logging requests and responses.
    
    Args:
        request: FastAPI request
        call_next: Next middleware in chain
        
    Returns:
        Response: FastAPI response
    """
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Client: {request.client.host}"
    )
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Response: {response.status_code} "
            f"Process Time: {process_time:.2f}ms"
        )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"Error: {str(e)}"
        )
        raise