#Tracing & Correlation Middleware - to trace an alert from the moment it hits the API to the background AI task. used Correlation ID.

import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Start timer & Generate/Capture Correlation ID
        start_time = time.time()
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # 2. Add ID to request state for use in background tasks
        request.state.correlation_id = correlation_id
        
        # 3. Process request
        response = await call_next(request)
        
        # 4. Record metrics & Add ID to response headers
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response

