import logging
import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis
from sqlalchemy import create_engine, text

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import Base, engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("vaultly")

# Auto-create tables on startup (especially for sqlite / dev environments)
if settings.environment != "testing":
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning("Could not connect to database at module startup: %s", e)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Vaultly — Smart Receipt, Warranty & Subscription Vault API",
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        "%s %s -> status %d (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled server exception on %s %s: %s", request.method, request.url.path, exc
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please try again later."
        },
    )


@app.get("/health")
def health() -> dict:
    """Reports real connectivity to PostgreSQL/SQLite and Redis."""
    checks = {}
    try:
        connect_args = (
            {"connect_timeout": 2}
            if not settings.database_url.startswith("sqlite")
            else {}
        )
        test_engine = create_engine(settings.database_url, connect_args=connect_args)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {type(exc).__name__}"

    try:
        redis_client = redis.Redis.from_url(settings.redis_url, socket_timeout=2)
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {type(exc).__name__}"

    # Backwards compatibility check key 'postgres'
    checks["postgres"] = checks["database"]

    status_str = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status_str, **checks}


# Mount API V1 routes
app.include_router(api_v1_router)
