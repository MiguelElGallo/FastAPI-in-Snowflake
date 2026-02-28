"""Snowflake database connection management."""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Generator

import snowflake.connector
from snowflake.connector import DictCursor

from app.config import settings

logger = logging.getLogger(__name__)


def _get_login_token() -> str:
    """Read the SPCS-injected OAuth token."""
    token_path = "/snowflake/session/token"
    if not os.path.exists(token_path):
        raise RuntimeError(
            "SNOWFLAKE_AUTH_TYPE=oauth but token file not found at /snowflake/session/token"
        )
    with open(token_path) as f:
        return f.read().strip()


def _get_connection_params() -> dict[str, Any]:
    """Build Snowflake connection parameters based on auth type."""
    if settings.SNOWFLAKE_AUTH_TYPE == "oauth":
        # Inside SPCS: use auto-injected env vars (SNOWFLAKE_HOST, SNOWFLAKE_ACCOUNT,
        # SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA) and the mounted OAuth token.
        # No 'user' parameter needed — SPCS uses a service-level identity.
        return {
            "host": os.getenv("SNOWFLAKE_HOST"),
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "authenticator": "oauth",
            "token": _get_login_token(),
            "database": os.getenv("SNOWFLAKE_DATABASE", settings.SNOWFLAKE_DATABASE),
            "schema": os.getenv("SNOWFLAKE_SCHEMA", settings.SNOWFLAKE_SCHEMA),
            "warehouse": settings.SNOWFLAKE_WAREHOUSE,
        }
    else:
        # Password-based auth (local development)
        return {
            "account": settings.SNOWFLAKE_ACCOUNT,
            "user": settings.SNOWFLAKE_USER,
            "password": settings.SNOWFLAKE_PASSWORD,
            "role": settings.SNOWFLAKE_ROLE,
            "database": settings.SNOWFLAKE_DATABASE,
            "schema": settings.SNOWFLAKE_SCHEMA,
            "warehouse": settings.SNOWFLAKE_WAREHOUSE,
        }


@contextmanager
def get_connection() -> Generator[snowflake.connector.SnowflakeConnection, None, None]:
    """Yield a Snowflake connection, ensuring it's closed after use."""
    params = _get_connection_params()
    # Log connection params (redact token) for debugging
    safe = {k: (v[:8] + "..." if k == "token" and v else v) for k, v in params.items()}
    logger.info("Snowflake connect params: %s", safe)
    conn = snowflake.connector.connect(**params)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_cursor() -> Generator[DictCursor, None, None]:
    """Yield a DictCursor for convenient row-as-dict access."""
    with get_connection() as conn:
        cur = conn.cursor(DictCursor)
        try:
            yield cur
        finally:
            cur.close()


def execute_query(
    query: str, params: tuple | dict | None = None, *, fetch: bool = True
) -> list[dict[str, Any]]:
    """Execute a query and optionally return all rows as dicts."""
    with get_cursor() as cur:
        cur.execute(query, params)
        if fetch:
            return [dict(row) for row in cur.fetchall()]
        return []


def execute_scalar(query: str, params: tuple | dict | None = None) -> Any:
    """Execute a query and return the first column of the first row."""
    with get_cursor() as cur:
        cur.execute(query, params)
        row = cur.fetchone()
        if row is None:
            return None
        # DictCursor returns a dict — get first value
        return next(iter(row.values()))
