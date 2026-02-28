"""Application settings managed via Pydantic."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- App ---
    PROJECT_NAME: str = "FastAPI in Snowflake"
    API_V1_PREFIX: str = "/api/v1"

    # --- Security ---
    JWT_SECRET_KEY: str = "CHANGE-ME-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # --- First superuser (created on startup) ---
    FIRST_SUPERUSER: str = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "changethis"

    # --- Snowflake ---
    SNOWFLAKE_ACCOUNT: str = ""
    SNOWFLAKE_HOST: str = ""  # e.g. orgname-account.snowflakecomputing.com
    SNOWFLAKE_USER: str = ""
    SNOWFLAKE_PASSWORD: str = ""
    SNOWFLAKE_DATABASE: str = "fastapi_db"
    SNOWFLAKE_SCHEMA: str = "fastapi_schema"
    SNOWFLAKE_WAREHOUSE: str = "fastapi_wh"
    SNOWFLAKE_ROLE: str = "fastapi_role"

    # Auth type: "password" for local dev, "oauth" when running inside SPCS
    SNOWFLAKE_AUTH_TYPE: str = "password"

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["*"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
