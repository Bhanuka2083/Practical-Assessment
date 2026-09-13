from contextlib import asynccontextmanager
import logging
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.workers.sweeper import sweeper

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s",
)
logger = logging.getLogger("pos.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages startup and shutdown events cleanly:
    1. Validates PostgreSQL connectivity before accepting traffic.
    2. Launches the async reservation sweeper in the event loop.
    3. Gracefully terminates workers and closes the DB engine pool on shutdown.
    """
    logger.info("Starting up %s...", settings.PROJECT_NAME)

    # Database connectivity check
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL database connection pool established.")
    except Exception as exc:
        logger.critical("Failed to connect to PostgreSQL: %s", exc)
        raise exc

    # Start background reservation sweeper (runs every 15 seconds)
    sweeper.start(interval_seconds=15)
    logger.info("Stock reservation sweeper scheduled.")

    yield  # Application serves requests

    # Graceful shutdown
    logger.info("Shutting down %s...", settings.PROJECT_NAME)
    await sweeper.stop()
    await engine.dispose()
    logger.info("Database engine connections closed and background tasks stopped.")


def create_application() -> FastAPI:
    """Application factory configuring routes, middleware, and documentation."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Cross-Origin Resource Sharing (CORS) Configuration
    # Tune allow_origins for your client application domain (e.g. http://localhost:3000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Idempotency-Key"],
    )

    # Include aggregated v1 routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/health", tags=["Health"])
    async def health_check():
        """Liveness check endpoint for load balancers and orchestrators."""
        return {
            "status": "healthy",
            "project": settings.PROJECT_NAME,
            "version": "1.0.0",
        }

    return app


app = create_application()