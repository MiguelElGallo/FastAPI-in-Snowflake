"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.crud.user import create_user, get_user_by_email
from app.models.user import UserCreate
from app.routers import auth, items, users

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure the first superuser exists."""
    _ensure_superuser()
    yield


def _ensure_superuser() -> None:
    """Create the initial superuser if it doesn't exist yet."""
    try:
        existing = get_user_by_email(settings.FIRST_SUPERUSER)
        if existing is None:
            create_user(
                UserCreate(
                    email=settings.FIRST_SUPERUSER,
                    password=settings.FIRST_SUPERUSER_PASSWORD,
                    is_superuser=True,
                    full_name="Admin",
                )
            )
            logger.info("Created first superuser: %s", settings.FIRST_SUPERUSER)
        else:
            logger.info("Superuser already exists: %s", settings.FIRST_SUPERUSER)
    except Exception:
        logger.warning(
            "Could not create superuser (database may not be ready yet). "
            "Run setup.sql first.",
            exc_info=True,
        )


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(items.router, prefix=settings.API_V1_PREFIX)


@app.get(f"{settings.API_V1_PREFIX}/health", tags=["health"])
def health_check():
    """Health check endpoint used by SPCS readiness probe."""
    return {"status": "healthy"}
