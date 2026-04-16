"""Configuration handling for the KeyCRM scraper.

This module loads environment variables from a ``.env`` file (if present) using
``python‑dotenv`` and provides a simple settings object.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load ``.env`` from the project root (or any parent directory).  The file is
# optional – in CI environments variables will be supplied directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    """Simple settings class that reads from environment variables."""

    # --- KeyCRM connection -------------------------------------------------
    keycrm_url: str = os.environ.get("KEYCRM_URL", "")
    keycrm_username: str = os.environ.get("KEYCRM_USERNAME", "")
    keycrm_password: str = os.environ.get("KEYCRM_PASSWORD", "")

    # --- PostgreSQL (Aiven) connection ------------------------------------
    aiven_pg_host: str = os.environ.get("AIVEN_PG_HOST", "")
    aiven_pg_port: int = int(os.environ.get("AIVEN_PG_PORT", "5432"))
    aiven_pg_db: str = os.environ.get("AIVEN_PG_DB", "defaultdb")
    aiven_pg_user: str = os.environ.get("AIVEN_PG_USER", "")
    aiven_pg_password: str = os.environ.get("AIVEN_PG_PASSWORD", "")
    aiven_pg_sslmode: str = os.environ.get("AIVEN_PG_SSLMODE", "require")

    def __init__(self):
        # Validate required fields
        missing = []
        if not self.keycrm_url:
            missing.append("KEYCRM_URL")
        if not self.keycrm_username:
            missing.append("KEYCRM_USERNAME")
        if not self.keycrm_password:
            missing.append("KEYCRM_PASSWORD")
        if not self.aiven_pg_host:
            missing.append("AIVEN_PG_HOST")
        if not self.aiven_pg_user:
            missing.append("AIVEN_PG_USER")
        if not self.aiven_pg_password:
            missing.append("AIVEN_PG_PASSWORD")

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        if self.aiven_pg_sslmode not in {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}:
            raise ValueError(f"Invalid SSL mode: {self.aiven_pg_sslmode}")

    @property
    def pg_dsn(self) -> str:
        """Return a PostgreSQL DSN constructed from the individual components."""
        return (
            f"postgresql://{self.aiven_pg_user}:{self.aiven_pg_password}@"
            f"{self.aiven_pg_host}:{self.aiven_pg_port}/{self.aiven_pg_db}"
            f"?sslmode={self.aiven_pg_sslmode}"
        )


# Cached singleton – importing ``settings`` elsewhere gives the same instance.
settings = Settings()