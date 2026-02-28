-- =============================================================
-- FastAPI in Snowflake — One-time infrastructure setup
-- Run this with a role that has ACCOUNTADMIN or equivalent
-- =============================================================

-- 1. Database & Schema
CREATE DATABASE IF NOT EXISTS fastapi_db;
CREATE SCHEMA IF NOT EXISTS fastapi_db.fastapi_schema;

-- 2. Warehouse
CREATE WAREHOUSE IF NOT EXISTS fastapi_wh
  WITH WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

-- 3. Role for the service
CREATE ROLE IF NOT EXISTS fastapi_role;
GRANT USAGE ON DATABASE fastapi_db TO ROLE fastapi_role;
GRANT USAGE ON SCHEMA fastapi_db.fastapi_schema TO ROLE fastapi_role;
GRANT ALL ON SCHEMA fastapi_db.fastapi_schema TO ROLE fastapi_role;
GRANT USAGE ON WAREHOUSE fastapi_wh TO ROLE fastapi_role;
GRANT CREATE COMPUTE POOL ON ACCOUNT TO ROLE fastapi_role;
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE fastapi_role;
GRANT CREATE SERVICE ON SCHEMA fastapi_db.fastapi_schema TO ROLE fastapi_role;
GRANT CREATE IMAGE REPOSITORY ON SCHEMA fastapi_db.fastapi_schema TO ROLE fastapi_role;

-- 4. Image repository
CREATE IMAGE REPOSITORY IF NOT EXISTS fastapi_db.fastapi_schema.fastapi_repo;

-- 5. Stage for specs
CREATE STAGE IF NOT EXISTS fastapi_db.fastapi_schema.fastapi_stage
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- 6. Tables
USE SCHEMA fastapi_db.fastapi_schema;

CREATE TABLE IF NOT EXISTS users (
    id              STRING DEFAULT UUID_STRING() PRIMARY KEY,
    email           STRING NOT NULL UNIQUE,
    hashed_password STRING NOT NULL,
    full_name       STRING,
    is_active       BOOLEAN DEFAULT TRUE,
    is_superuser    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS items (
    id          STRING DEFAULT UUID_STRING() PRIMARY KEY,
    title       STRING NOT NULL,
    description STRING,
    owner_id    STRING NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Grant table-level privileges to fastapi_role
-- (tables above are created by ACCOUNTADMIN, so explicit grants are needed)
GRANT ALL ON ALL TABLES IN SCHEMA fastapi_db.fastapi_schema TO ROLE fastapi_role;
GRANT ALL ON FUTURE TABLES IN SCHEMA fastapi_db.fastapi_schema TO ROLE fastapi_role;

-- 7. External access integration (for outbound HTTPS if needed)
-- NOTE: Not supported on trial accounts. Uncomment on paid accounts.
-- CREATE NETWORK RULE IF NOT EXISTS fastapi_egress_rule
--   MODE = EGRESS
--   TYPE = HOST_PORT
--   VALUE_LIST = ('0.0.0.0:443');
--
-- CREATE EXTERNAL ACCESS INTEGRATION IF NOT EXISTS fastapi_external_access
--   ALLOWED_NETWORK_RULES = (fastapi_egress_rule)
--   ENABLED = TRUE;

-- 8. OAuth security integration for SPCS service-to-Snowflake auth
-- NOTE: May require specific account features. Uncomment if needed.
-- CREATE SECURITY INTEGRATION IF NOT EXISTS snowservices_ingress_oauth
--   TYPE = oauth
--   OAUTH_CLIENT = snowservices_ingress
--   ENABLED = TRUE;

SELECT 'Setup complete!' AS status;
