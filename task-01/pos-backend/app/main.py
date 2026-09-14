from contextlib import asynccontextmanager
import logging
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.workers.sweeper import sweeper

import secrets
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.api.v1.router import api_router


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
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
        version="1.0.0"
    )

    origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Idempotency-Key",
            "Accept",
            "Origin",
            "X-Requested-With",
        ],
    )

    security = HTTPBasic()

    def authenticate_docs(credentials: HTTPBasicCredentials = Depends(security)):
        correct_username = secrets.compare_digest(credentials.username, settings.DOCS_USERNAME)
        correct_password = secrets.compare_digest(credentials.password, settings.DOCS_PASSWORD)

        if not (correct_username and correct_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials for API documentation",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials.username

    @app.get("/api/v1/openapi.json", include_in_schema=False)
    async def get_protected_openapi(username: str = Depends(authenticate_docs)):
        return get_openapi(title=app.title, version="1.0.0", routes=app.routes)

    @app.get("/docs", include_in_schema=False)
    async def get_protected_swagger_ui(username: str = Depends(authenticate_docs)):
        return get_swagger_ui_html(
            openapi_url="/api/v1/openapi.json",
            title=f"{app.title} - Swagger UI",
        )

    @app.get("/redoc", include_in_schema=False)
    async def get_protected_redoc(username: str = Depends(authenticate_docs)):
        return get_redoc_html(
            openapi_url="/api/v1/openapi.json",
            title=f"{app.title} - ReDoc",
        )


    @app.get("/health", tags=["Health"])
    async def health_check():
        """Liveness check endpoint for load balancers and orchestrators."""
        return {
            "status": "healthy",
            "project": settings.PROJECT_NAME,
            "version": "1.0.0",
        }

    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()