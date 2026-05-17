"""Load /repos/claude-config/.env into os.environ. Call load() at startup."""

from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def load() -> None:
    """Load .env into os.environ. File values override preexisting shell env."""
    load_dotenv(ENV_FILE, override=True)
