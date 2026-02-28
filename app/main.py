"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.crud.user import create_user, get_user_by_email
from app.models.user import UserCreate
from app.routers import auth, items, users

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


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
    # Disable default docs/redoc — we serve self-hosted versions below
    # so they work inside SPCS (ingress CSP blocks external CDN scripts).
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

# Mount self-hosted Swagger UI / ReDoc assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

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


@app.get(f"{settings.API_V1_PREFIX}/docs", include_in_schema=False)
def custom_swagger_ui():
    """Serve Swagger UI from local assets (SPCS blocks CDN scripts)."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.PROJECT_NAME} — Docs",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get(f"{settings.API_V1_PREFIX}/redoc", include_in_schema=False)
def custom_redoc():
    """Serve ReDoc from local assets."""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{settings.PROJECT_NAME} — ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


@app.get(f"{settings.API_V1_PREFIX}/health", tags=["health"])
def health_check():
    """Health check endpoint used by SPCS readiness probe."""
    return {"status": "healthy"}
