# FastAPI in Snowflake Container Services

A production-ready FastAPI application running inside **Snowflake Container Services (SPCS)**, using **Snowflake tables** as the database. Fully declarative infrastructure via Snowflake CLI — no Terraform required.

## Architecture

```
GitHub Actions ──push image──▶ Snowflake Image Registry
       │                            │
       │ snow spcs deploy           ▼
       └────────────────────▶ SPCS Service (FastAPI)
                                    │
                                    ▼
                             Snowflake Tables
```

## Stack

| Layer | Technology |
|-------|-----------|
| **API Framework** | FastAPI + Uvicorn |
| **Database** | Snowflake standard tables |
| **Auth** | JWT (python-jose) + bcrypt |
| **Container Runtime** | Snowflake Container Services |
| **Infrastructure** | Snowflake CLI (`snow`) — declarative |
| **CI/CD** | GitHub Actions |

## Project Structure

```
├── .github/workflows/
│   ├── setup-infra.yml     # One-time: DB, tables, compute pool, image repo
│   └── deploy.yml          # On push: build, push image, deploy service
├── app/
│   ├── main.py             # FastAPI app factory
│   ├── config.py           # Pydantic Settings
│   ├── database.py         # Snowflake connector wrapper
│   ├── security.py         # JWT + password hashing
│   ├── dependencies.py     # DI: get_current_user, etc.
│   ├── models/             # Pydantic request/response models
│   ├── crud/               # Database operations
│   └── routers/            # API endpoints
├── snowflake.yml           # SPCS project definition
├── spec.yml                # SPCS service specification
├── setup.sql               # One-time Snowflake DDL
├── Dockerfile              # Multi-stage build
└── requirements.txt
```

## Prerequisites

1. **Snowflake account** with Container Services enabled
2. **Snowflake CLI** (`snow`) installed locally — [install guide](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation)
3. **RSA key pair** for CI/CD authentication — [key pair guide](https://docs.snowflake.com/en/user-guide/key-pair-auth)

## Quick Start (Local Development)

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your Snowflake credentials

# 2. Run setup SQL in Snowflake (once)
snow sql --query "$(cat setup.sql)" --connection your_connection

# 3. Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 4. Run locally
uvicorn app.main:app --reload --port 8000

# 5. Open docs
open http://localhost:8000/api/v1/docs
```

## Deploy to SPCS

### 1. Configure GitHub Secrets

| Secret | Description |
|--------|-------------|
| `SNOWFLAKE_ACCOUNT` | `org-account` identifier |
| `SNOWFLAKE_USER` | Service account username |
| `SNOWFLAKE_PRIVATE_KEY` | RSA private key (base64-encoded PEM) |
| `SNOWFLAKE_DATABASE` | `fastapi_db` |
| `SNOWFLAKE_SCHEMA` | `fastapi_schema` |
| `SNOWFLAKE_WAREHOUSE` | `fastapi_wh` |
| `SNOWFLAKE_ROLE` | `fastapi_role` |

Generate the base64 private key:
```bash
base64 -i ~/.snowflake/rsa_key.p8 | tr -d '\n'
```

### 2. Run Infrastructure Setup (once)

Go to **Actions → Setup SPCS Infrastructure → Run workflow**

This creates: database, schema, tables, image repository, compute pool.

### 3. Deploy (automatic)

Push to `main` → GitHub Actions builds the image, pushes to Snowflake registry, and deploys/upgrades the service.

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/api/v1/auth/login` | Get JWT token | Public |
| `GET` | `/api/v1/users/me` | Current user profile | Bearer |
| `PATCH` | `/api/v1/users/me` | Update own profile | Bearer |
| `GET` | `/api/v1/users/` | List all users | Superuser |
| `POST` | `/api/v1/users/` | Create user | Superuser |
| `GET` | `/api/v1/items/` | List own items | Bearer |
| `POST` | `/api/v1/items/` | Create item | Bearer |
| `GET` | `/api/v1/items/{id}` | Get item | Bearer |
| `PATCH` | `/api/v1/items/{id}` | Update item | Bearer |
| `DELETE`| `/api/v1/items/{id}` | Delete item | Bearer |
| `GET` | `/api/v1/health` | Health check | Public |

## SPCS Auth Model

When running inside SPCS, the container automatically receives an OAuth token at `/snowflake/session/token`. The app detects `SNOWFLAKE_AUTH_TYPE=oauth` and uses this token — no passwords stored in the container.

## Based On

Simplified from the [FastAPI full-stack template](https://fastapi.tiangolo.com/project-generation/), with:
- PostgreSQL → **Snowflake tables**
- Alembic → **DDL in `setup.sql`**
- Removed: email recovery, Pytest, Traefik, Celery, React frontend
