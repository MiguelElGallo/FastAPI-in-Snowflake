"""Snowflake database connection management."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Generator

import snowflake.connector
from snowflake.connector import DictCursor

from app.config import settings


def _get_connection_params() -> dict[str, Any]:
    """Build Snowflake connection parameters based on auth type."""
    base = {
        "account": settings.SNOWFLAKE_ACCOUNT,
        "database": settings.SNOWFLAKE_DATABASE,
        "schema": settings.SNOWFLAKE_SCHEMA,
        "warehouse": settings.SNOWFLAKE_WAREHOUSE,
    }

    if settings.SNOWFLAKE_AUTH_TYPE == "oauth":
        # Inside SPCS, the OAuth token is mounted at /snowflake/session/token
        token_path = "/snowflake/session/token"
        if os.path.exists(token_path):
            with open(token_path) as f:
                token = f.read().strip()
            base["authenticator"] = "oauth"
            base["token"] = token
            # SPCS requires explicit host for OAuth connections
            base["host"] = settings.SNOWFLAKE_HOST
        else:
            raise RuntimeError(
                "SNOWFLAKE_AUTH_TYPE=oauth but token file not found at /snowflake/session/token"
            )
    else:
        # Password-based auth (local development)
        base["user"] = settings.SNOWFLAKE_USER
        base["password"] = settings.SNOWFLAKE_PASSWORD
        base["role"] = settings.SNOWFLAKE_ROLE

    return base


@contextmanager
def get_connection() -> Generator[snowflake.connector.SnowflakeConnection, None, None]:
    """Yield a Snowflake connection, ensuring it's closed after use."""
    conn = snowflake.connector.connect(**_get_connection_params())
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
