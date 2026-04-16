# KeyCRM Scraper

A reliable, Playwright‑based scraper for **KeyCRM** that logs in, applies filters, extracts all orders and stores them in an Aiven‑hosted PostgreSQL database.

## Features

- Synchronous Playwright with explicit waits and tenacity retries
- Page Object Model (POM) for clean separation of page logic
- CLI with `--headless` (default for automation) and `--no-headless` (for debugging)
- Structured logging via Loguru (JSON output)
- PostgreSQL upsert logic for idempotent runs
- GitHub Actions workflow for scheduled runs

## Requirements

- Python 3.12+
- Playwright
- PostgreSQL database (tested with Aiven)

## Installation

```bash
# Clone the repo
git clone <repo-url>
cd keycrm-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Configuration

1. Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

2. Edit `.env` with your:
   - KeyCRM URL, username, password
   - Aiven PostgreSQL connection details

## Usage

```bash
# Run in headless mode (default for automation)
python -m scraper.cli --headless

# Run with visible browser (for debugging)
python -m scraper.cli --no-headless

# Limit number of orders (for testing)
python -m scraper.cli --headless --limit 50
```

## GitHub Actions

The scraper can run automatically via GitHub Actions:

1. Go to your repository settings → Secrets and variables → Actions
2. Add the following secrets:
   - `KEYCRM_URL`
   - `KEYCRM_USERNAME`
   - `KEYCRM_PASSWORD`
   - `AIVEN_PG_HOST`
   - `AIVEN_PG_PORT`
   - `AIVEN_PG_DB`
   - `AIVEN_PG_USER`
   - `AIVEN_PG_PASSWORD`
   - `AIVEN_PG_SSLMODE` (usually `require`)

3. The workflow runs daily at 6 AM UTC (can be triggered manually)

## Security

- **NEVER** commit `.env` or any file with credentials
- All sensitive data is stored in GitHub Secrets
- The `.gitignore` excludes environment files and logs
- Credentials are only used at runtime, never logged

## Project Layout

```
keycrm-scraper/
├── .env.example          # Template for environment variables
├── .gitignore            # Excludes sensitive files
├── .github/
│   └── workflows/
│       └── scrape.yml    # GitHub Actions workflow
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project metadata
├── README.md
└── scraper/
    ├── cli.py            # CLI entry point
    ├── config.py         # Loads environment variables
    ├── logger.py         # Loguru setup
    ├── db/
    │   ├── models.py     # Pydantic models
    │   └── repository.py # Database operations
    ├── pages/            # Page Object Model
    └── scraper/
        └── keycrm_scraper.py # Main workflow
```

## License

MIT