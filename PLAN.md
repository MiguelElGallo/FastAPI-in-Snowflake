# FastAPI in Snowflake Container Services — Implementation Plan

## Prerequisites

A working **Snowflake CLI** (`snow`) connection with these privileges:

| Privilege | Scope |
|---|---|
| `CREATE COMPUTE POOL` | Account |
| `CREATE DATABASE` / `CREATE SCHEMA` | Account |
| `CREATE SERVICE` | Schema |
| `BIND SERVICE ENDPOINT` | Account |
| `CREATE IMAGE REPOSITORY` | Schema |
| `USAGE` on warehouse | Warehouse |

Authentication for CI/CD: **key-pair** auth stored in GitHub Secrets.

---

## Architecture Overview

```
GitHub Actions ──push image──▶ Snowflake Image Registry
       │                            │
       │ snow spcs deploy           ▼
       └────────────────────▶ SPCS Service (FastAPI container)
                                    │
                                    ▼
                             Snowflake Tables (via snowflake-connector-python)
```

---

## A) Declarative SPCS Infrastructure via `snowflake.yml`

No Terraform. No imperative SQL. Everything defined in `snowflake.yml` (definition_version: 2).

### Resources declared:
1. **Image Repository** — where Docker images are pushed
2. **Compute Pool** — `CPU_X64_XS`, 1 node, auto-suspend 300s
3. **Service** — runs the FastAPI container from the image repo

### Key files:
- `snowflake.yml` — project definition (compute pool, service, image repo)
- `spec.yml` — service specification (container config, endpoints, env vars)
- `setup.sql` — one-time DDL for database, schema, warehouse, roles

### Deployment flow:
```bash
# Build & push image
snow spcs image-repository create fastapi_repo --if-not-exists
docker build -t <registry>/fastapi_db/fastapi_schema/fastapi_repo/fastapi-app:latest .
snow spcs image-registry login
docker push <registry>/fastapi_db/fastapi_schema/fastapi_repo/fastapi-app:latest

# Create compute pool + deploy service (declarative)
snow spcs compute-pool create fastapi_pool --if-not-exists \
  --family CPU_X64_XS --min-nodes 1 --max-nodes 1
snow spcs service create fastapi_service --compute-pool fastapi_pool \
  --spec-path spec.yml --if-not-exists
```

---

## B) Simplified FastAPI App (from full-stack-fastapi-template)

### KEPT from template:
- ✅ FastAPI app factory & routers
- ✅ Pydantic settings management
- ✅ JWT authentication (python-jose + passlib)
- ✅ User model & CRUD
- ✅ Items model & CRUD (example entity)
- ✅ CORS middleware
- ✅ Health check endpoint
- ✅ Docker multi-stage build

### REMOVED:
- ❌ Email-based password recovery
- ❌ Pytest test suite
- ❌ Traefik reverse proxy
- ❌ PostgreSQL + Alembic migrations
- ❌ Celery workers
- ❌ Frontend (React)

### REPLACED:
- 🔄 PostgreSQL → **Snowflake tables** via `snowflake-connector-python`
- 🔄 SQLModel sessions → **Snowflake connector** with raw SQL or dict-based results
- 🔄 Alembic → **DDL in `setup.sql`** (run once)

---

## C) Implementation Plan

### File Structure

```
FastAPI-in-Snowflake/
├── .github/
│   └── workflows/
│       ├── deploy.yml          # Build, push, deploy to SPCS
│       └── setup-infra.yml     # One-time infra setup
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory
│   ├── config.py               # Pydantic Settings
│   ├── security.py             # JWT token creation/verification
│   ├── database.py             # Snowflake connector wrapper
│   ├── dependencies.py         # Dependency injection (get_db, get_current_user)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User Pydantic models
│   │   └── item.py             # Item Pydantic models
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── user.py             # User CRUD operations
│   │   └── item.py             # Item CRUD operations
│   └── routers/
│       ├── __init__.py
│       ├── auth.py             # Login endpoint
│       ├── users.py            # User management endpoints
│       └── items.py            # Item CRUD endpoints
├── snowflake.yml               # SPCS project definition
├── spec.yml                    # SPCS service specification
├── setup.sql                   # One-time Snowflake DDL
├── Dockerfile                  # Multi-stage build
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── PLAN.md                     # This file
└── README.md                   # Usage documentation
```

### Implementation Order

| Step | What | Files |
|------|------|-------|
| 1 | Snowflake declarative config | `snowflake.yml`, `spec.yml`, `setup.sql` |
| 2 | FastAPI app core | `app/main.py`, `app/config.py` |
| 3 | Snowflake database layer | `app/database.py` |
| 4 | Auth & security | `app/security.py`, `app/dependencies.py` |
| 5 | Models (Pydantic) | `app/models/user.py`, `app/models/item.py` |
| 6 | CRUD operations | `app/crud/user.py`, `app/crud/item.py` |
| 7 | API Routers | `app/routers/auth.py`, `app/routers/users.py`, `app/routers/items.py` |
| 8 | Docker | `Dockerfile`, `requirements.txt` |
| 9 | GitHub Actions | `.github/workflows/deploy.yml`, `.github/workflows/setup-infra.yml` |
| 10 | Documentation | `README.md`, `.env.example` |

---

## GitHub Actions Workflows

### `setup-infra.yml` (manual trigger)
1. Install Snowflake CLI
2. Configure connection from secrets (key-pair auth)
3. Run `setup.sql` (create DB, schema, warehouse, tables, roles)
4. Create image repository
5. Create compute pool

### `deploy.yml` (on push to main)
1. Install Snowflake CLI
2. Configure connection from secrets
3. Login to Snowflake image registry
4. Build Docker image
5. Push to Snowflake image registry
6. Deploy/upgrade service via `snow spcs service create/upgrade`

### Required GitHub Secrets
| Secret | Description |
|--------|-------------|
| `SNOWFLAKE_ACCOUNT` | Account identifier (org-account) |
| `SNOWFLAKE_USER` | Service account username |
| `SNOWFLAKE_PRIVATE_KEY` | RSA private key (PEM, base64) |
| `SNOWFLAKE_DATABASE` | Target database |
| `SNOWFLAKE_SCHEMA` | Target schema |
| `SNOWFLAKE_WAREHOUSE` | Warehouse for queries |
| `SNOWFLAKE_ROLE` | Role with SPCS privileges |
| `JWT_SECRET_KEY` | Secret for JWT token signing |
| `FIRST_SUPERUSER_PASSWORD` | Initial admin password |
