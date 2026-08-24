import os
from pathlib import Path

from dotenv import load_dotenv


# Load .env robustly for both local dev and Docker flattened layout.
# Local:  backend/config.py -> parents[1] = repo root / .env
# Docker: /app/config.py (flattened) or /app/backend/config.py (package) -> CWD = /app
for _candidate in [
    Path(__file__).resolve().parents[1] / ".env",  # repo root when running locally
    Path.cwd() / ".env",                           # Docker WORKDIR /app
    Path(__file__).resolve().parent / ".env",      # adjacent to config.py
    Path(__file__).resolve().parents[0] / ".env",
]:
    if _candidate.is_file():
        load_dotenv(_candidate, override=False)
        break
else:
    # Still call load_dotenv to pick up env vars injected by Docker/compose
    load_dotenv(override=False)


def _csv_env(name: str, default: list[str]) -> list[str]:
	raw = os.getenv(name, "")
	if not raw.strip():
		return default
	values = [value.strip() for value in raw.split(",") if value.strip()]
	return values or default


def _required_env(name: str) -> str:
	value = os.getenv(name, "").strip()
	if not value:
		raise RuntimeError(f"Missing required environment variable: {name}")
	return value


OLLAMA_BASE_URL = (os.getenv("OLLAMA_BASE_URL") or "").strip() or "http://127.0.0.1:11434"
DEFAULT_MODEL = (os.getenv("DEFAULT_MODEL") or "").strip() or "phi4-mini:latest"
AVAILABLE_MODELS = _csv_env("AVAILABLE_MODELS", [DEFAULT_MODEL])
if DEFAULT_MODEL not in AVAILABLE_MODELS:
	AVAILABLE_MODELS = [DEFAULT_MODEL, *AVAILABLE_MODELS]

ALLOWED_ORIGINS = _csv_env(
    "PRECIS_ALLOWED_ORIGINS",
    ["http://localhost:5173", "http://localhost:5555", "http://localhost:7860"],
)

API_KEY = os.getenv("PRECIS_API_KEY") or None

MAX_SUMMARY_TOKENS = int(
	os.getenv("MAX_SUMMARY_TOKENS", os.getenv("PRECIS_MAX_SUMMARY_TOKENS", "120"))
)
TEMPERATURE = float(
	os.getenv("TEMPERATURE", os.getenv("PRECIS_TEMPERATURE", "0.2"))
)
MAX_UPLOAD_BYTES = int(os.getenv("PRECIS_MAX_UPLOAD_BYTES", "10485760"))
MAX_TRANSCRIPT_CHARS = int(os.getenv("PRECIS_MAX_TRANSCRIPT_CHARS", "120000"))
