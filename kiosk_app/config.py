"""Environment-backed kiosk configuration."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Language:
    code: str
    name: str
    native_name: str
    icon: str


LANGUAGES = (
    Language("ta", "Tamil", "தமிழ்", "🪷"),
    Language("ml", "Malayalam", "മലയാളം", "🌴"),
    Language("kn", "Kannada", "ಕನ್ನಡ", "🌾"),
    Language("te", "Telugu", "తెలుగు", "🌻"),
    Language("hi", "Hindi", "हिन्दी", "🪔"),
    Language("mr", "Marathi", "मराठी", "🚜"),
    Language("en", "English", "English", "🌐"),
)

SCHEME_CATEGORIES = (
    "farmers",
    "women",
    "students",
    "health",
    "housing",
    "pensions",
    "employment",
)


def _load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE entries without replacing environment variables."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip("\"'")
        if name and name not in os.environ:
            os.environ[name] = value


def _integer(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc


def _float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} must be a number.") from exc


def _overrides() -> dict[str, dict[str, str]]:
    raw = os.environ.get("BHASHINI_MODEL_OVERRIDES", "{}")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("BHASHINI_MODEL_OVERRIDES must be a JSON object.") from exc
    if not isinstance(value, dict) or any(
        not isinstance(language, str)
        or not isinstance(services, dict)
        or any(not isinstance(service, str) or not isinstance(model, str) for service, model in services.items())
        for language, services in value.items()
    ):
        raise ValueError("BHASHINI_MODEL_OVERRIDES must map language codes to service/model IDs.")
    return value


@dataclass(frozen=True)
class Settings:
    """Runtime settings; secrets are read only from process environment or .env."""

    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8080
    bhashini_api_key: str = ""
    bhashini_model_overrides: dict[str, dict[str, str]] = field(default_factory=dict)
    llm_provider: str = "none"
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = ""
    mongo_uri: str = ""
    mongo_database: str = "scheme_kiosk"
    mongo_collection: str = "schemes"
    request_timeout_seconds: float = 12.0
    retry_attempts: int = 2
    retry_backoff_seconds: float = 0.3
    idle_timeout_seconds: int = 90
    cache_directory: Path = Path("data/cache")
    max_audio_bytes: int = 12 * 1024 * 1024
    max_retrieval_results: int = 5

    @classmethod
    def from_env(cls, dotenv_path: Path | None = None) -> "Settings":
        """Read settings from .env and the process environment."""
        _load_dotenv(dotenv_path or Path(".env"))
        settings = cls(
            environment=os.environ.get("KIOSK_ENV", "development").strip().lower(),
            host=os.environ.get("KIOSK_HOST", "127.0.0.1").strip(),
            port=_integer("KIOSK_PORT", 8080),
            bhashini_api_key=os.environ.get("BHASHINI_API_KEY", "").strip(),
            bhashini_model_overrides=_overrides(),
            llm_provider=os.environ.get("LLM_PROVIDER", "none").strip().lower(),
            llm_api_key=os.environ.get("LLM_API_KEY", "").strip(),
            llm_model=os.environ.get("LLM_MODEL", "").strip(),
            llm_base_url=os.environ.get("LLM_BASE_URL", "").strip(),
            mongo_uri=os.environ.get("MONGO_URI", "").strip(),
            mongo_database=os.environ.get("MONGO_DATABASE", "scheme_kiosk").strip(),
            mongo_collection=os.environ.get("MONGO_COLLECTION", "schemes").strip(),
            request_timeout_seconds=_float("REQUEST_TIMEOUT_SECONDS", 12.0),
            retry_attempts=_integer("RETRY_ATTEMPTS", 2),
            retry_backoff_seconds=_float("RETRY_BACKOFF_SECONDS", 0.3),
            idle_timeout_seconds=_integer("IDLE_TIMEOUT_SECONDS", 90),
            cache_directory=Path(os.environ.get("CACHE_DIRECTORY", "data/cache")),
            max_audio_bytes=_integer("MAX_AUDIO_BYTES", 12 * 1024 * 1024),
            max_retrieval_results=_integer("MAX_RETRIEVAL_RESULTS", 5),
        )
        if settings.llm_provider not in {"none", "gemini", "anthropic", "openai-compatible"}:
            raise ValueError("LLM_PROVIDER must be none, gemini, anthropic, or openai-compatible.")
        if settings.request_timeout_seconds <= 0 or settings.retry_attempts < 1:
            raise ValueError("Timeout must be positive and retry attempts must be at least one.")
        if settings.port < 1 or settings.port > 65535:
            raise ValueError("KIOSK_PORT must be between 1 and 65535.")
        if settings.max_audio_bytes < 1 or settings.max_retrieval_results < 1:
            raise ValueError("Audio size and retrieval result limits must be positive.")
        if settings.environment == "production" and not settings.mongo_uri:
            raise ValueError("MONGO_URI is required in production; the development mock is not production data.")
        if settings.llm_provider != "none" and not settings.llm_api_key:
            raise ValueError("LLM_API_KEY is required when an LLM provider is selected.")
        if settings.llm_provider != "none" and not settings.llm_model:
            raise ValueError("LLM_MODEL is required when an LLM provider is selected.")
        return settings


def language_for(code: str) -> Language:
    """Return a configured language or reject an unsupported code."""
    for language in LANGUAGES:
        if language.code == code:
            return language
    raise ValueError(f"Unsupported language code: {code}")
