# from fastapi import FastAPI
# from app.api.v1.endpoints.router import api_router
# from app.core.config import settings

# app = FastAPI()
# app.include_router(api_router, prefix=settings.API_V1_STR)

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from redis.asyncio import Redis

from app.core.config import settings
from app.core.database import engine, Base
from app.core.redis import init_redis, close_redis, get_redis

# CRUCIAL: Import models so SQLAlchemy registers tables before create_all
from app.models.incident import Incident, Alert

# Import your API Router
from app.api.v1.endpoints.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan: Handles DB initialization, pgvector extension,
    and Redis pool lifecycle on startup and shutdown.
    """
    print("🚀 Starting AI Incident Engine services...")
    
    # 1. Initialize Redis connection pool
    await init_redis()
    print("✅ Redis pool connected.")
    
    # 2. Enable pgvector extension and create missing database tables
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables (incidents, alerts) created/verified.")
        
    yield  # Server runs and handles requests here
    
    # 3. Cleanup on shutdown
    print("🛑 Shutting down services...")
    await close_redis()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["System"])
async def health_check(redis: Redis = Depends(get_redis)):
    """Health check endpoint for database and redis connectivity."""
    redis_status = "unhealthy"
    try:
        if await redis.ping():
            redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "services": {
            "database": "connected",
            "redis": redis_status
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)