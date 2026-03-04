import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ROOT_ENV_PATH)


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


OLLAMA_BASE_URL = _required_env("OLLAMA_BASE_URL")
DEFAULT_MODEL = _required_env("DEFAULT_MODEL")
AVAILABLE_MODELS = _csv_env("AVAILABLE_MODELS", [DEFAULT_MODEL])
if DEFAULT_MODEL not in AVAILABLE_MODELS:
	AVAILABLE_MODELS = [DEFAULT_MODEL, *AVAILABLE_MODELS]

ALLOWED_ORIGINS = _csv_env("PRECIS_ALLOWED_ORIGINS", [])
if not ALLOWED_ORIGINS:
	raise RuntimeError("Missing required environment variable: PRECIS_ALLOWED_ORIGINS")

API_KEY = _required_env("PRECIS_API_KEY")

MAX_SUMMARY_TOKENS = int(
	os.getenv("MAX_SUMMARY_TOKENS", os.getenv("PRECIS_MAX_SUMMARY_TOKENS", "120"))
)
TEMPERATURE = float(
	os.getenv("TEMPERATURE", os.getenv("PRECIS_TEMPERATURE", "0.2"))
)
MAX_UPLOAD_BYTES = int(os.getenv("PRECIS_MAX_UPLOAD_BYTES", "10485760"))
MAX_TRANSCRIPT_CHARS = int(os.getenv("PRECIS_MAX_TRANSCRIPT_CHARS", "120000"))
