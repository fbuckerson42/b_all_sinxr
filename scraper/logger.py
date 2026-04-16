"""Centralised logging configuration using Loguru.

The scraper emits JSON‑structured logs to ``logs/scraper.log``.  The log file
rotates daily and retains the last 7 days.  A convenience ``log`` object is
exported so that other modules can simply ``from .logger import log``.
"""

from pathlib import Path
from loguru import logger

# Ensure the logs directory exists
LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / "scraper.log"

# Remove the default stderr sink to avoid duplicate output in CI environments
logger.remove()

# Add a file sink – JSON format makes it easy to ship to ELK/Datadog later.
logger.add(
    log_file,
    rotation="00:00",          # rotate at midnight
    retention="7 days",        # keep a week of logs
    serialize=True,            # JSON output
    level="INFO",
)

# Also keep pretty human‑readable output on the console during interactive runs.
logger.add(
    sink=lambda msg: print(msg, end=""),
    level="INFO",
    colorize=True,
    backtrace=True,
    diagnose=True,
)

# Export the configured logger instance for easy import.
log = logger
