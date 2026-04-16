"""Configuration handling for the KeyCRM scraper.

This module loads environment variables from a ``.env`` file (if present) using
``python‑dotenv`` and validates them with a Pydantic ``BaseSettings`` model.
All settings are accessed through the ``settings`` singleton defined at the
bottom of the file.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from pydantic import Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load ``.env`` from the project root (or any parent directory).  The file is
# optional – in CI environments variables will be supplied directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)


class Settings(BaseSettings):
    # --- KeyCRM connection -------------------------------------------------
    keycrm_url: str = Field(..., env="KEYCRM_URL")
    keycrm_username: str = Field(..., env="KEYCRM_USERNAME")
    keycrm_password: str = Field(..., env="KEYCRM_PASSWORD")

    # --- PostgreSQL (Aiven) connection ------------------------------------
    aiven_pg_host: str = Field(..., env="AIVEN_PG_HOST")
    aiven_pg_port: int = Field(5432, env="AIVEN_PG_PORT")
    aiven_pg_db: str = Field(..., env="AIVEN_PG_DB")
    aiven_pg_user: str = Field(..., env="AIVEN_PG_USER")
    aiven_pg_password: str = Field(..., env="AIVEN_PG_PASSWORD")
    aiven_pg_sslmode: str = Field("require", env="AIVEN_PG_SSLMODE")

    class Config:
        case_sensitive = False
        env_file = str(ENV_PATH)
        env_prefix = ""

    @validator("aiven_pg_sslmode")
    def _validate_sslmode(cls, v: str) -> str:
        if v not in {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}:
            raise ValueError("Invalid SSL mode for PostgreSQL connection")
        return v

    @property
    def pg_dsn(self) -> str:
        """Return a PostgreSQL DSN constructed from the individual components."""
        return (
            f"postgresql://{self.aiven_pg_user}:{self.aiven_pg_password}@"
            f"{self.aiven_pg_host}:{self.aiven_pg_port}/{self.aiven_pg_db}"
            f"?sslmode={self.aiven_pg_sslmode}"
        )


# Cached singleton – importing ``settings`` elsewhere gives the same validated
# instance without re‑reading the environment multiple times.
settings = Settings()
