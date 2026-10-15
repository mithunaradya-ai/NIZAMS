"""Typed, model-aware boundary around the bundled Bhashini SDK."""

from __future__ import annotations

import base64
import logging
import time
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from .config import LANGUAGES, Settings
from .errors import BhashiniCallError

logger = logging.getLogger(__name__)
T = TypeVar("T")
SDK_ERROR_PREFIXES = ("Input Error:", "Validation Error:", "API Error:")


@dataclass(frozen=True)
class SDKResult(Generic[T]):
    """A successful SDK value; unwrap converts SDK string errors into domain errors."""

    value: T | None = None
    error: str | None = None

    def unwrap(self) -> T:
        if self.error is not None:
            raise BhashiniCallError(self.error)
        if self.value is None:
            raise BhashiniCallError("API Error: Bhashini returned an empty result.")
        return self.value


def _result(value: T) -> SDKResult[T]:
    if isinstance(value, str) and value.startswith(SDK_ERROR_PREFIXES):
        return SDKResult(error=value)
    return SDKResult(value=value)


class BhashiniGateway:
    """Selects and caches SDK model IDs and converts SDK errors into typed results."""

    def __init__(
        self,
        settings: Settings,
        *,
        client=None,
        models_lookup: Callable | None = None,
    ) -> None:
        if client is None or models_lookup is None:
            try:
                from bhashini_client import BhashiniClient, get_available_models
            except ImportError as exc:
                raise RuntimeError(
                    "The Bhashini SDK dependencies are missing. Install kiosk_requirements.txt "
                    "in the kiosk runtime; the bundled Python 3.15 environment is intentionally unchanged."
                ) from exc
            client = client or BhashiniClient(api_key=settings.bhashini_api_key or None)
            models_lookup = models_lookup or get_available_models
        self.client = client
        self.models_lookup = models_lookup
        self.settings = settings
        self._models: dict[tuple[str, str, str], str] = {}
        self._select_startup_models()

    def _select_startup_models(self) -> None:
        for language in LANGUAGES:
            self._select_model("asr", language.code)
            self._select_model("tts", language.code)
            if language.code != "en":
                self._select_model("nmt", language.code, "en")
                self._select_model("nmt", "en", language.code)

    def _select_model(self, service: str, source: str, target: str = "") -> str:
        key = (service, source, target)
        if key in self._models:
            return self._models[key]
        overrides = self.settings.bhashini_model_overrides.get(source, {})
        target_overrides = self.settings.bhashini_model_overrides.get(target, {})
        override = overrides.get(service) or target_overrides.get(service)
        if override:
            models = self.models_lookup(service, language=(source, target) if service == "nmt" else source)
            if isinstance(models, str) or not any(model.get("serviceId") == override for model in models):
                raise ValueError(f"Configured Bhashini {service} model is unsupported for language {source}.")
            selected = override
        else:
            language_filter = (source, target) if service == "nmt" else source
            models = self.models_lookup(service, language=language_filter)
            if isinstance(models, str) or not models:
                raise ValueError(f"No Bhashini {service} model is available for language {source}.")
            selected = models[0]["serviceId"]
        self._models[key] = selected
        return selected

    def _call(self, call: Callable[[], T]) -> SDKResult[T]:
        result: SDKResult[T] | None = None
        for attempt in range(self.settings.retry_attempts):
            result = _result(call())
            if result.error is None or not result.error.startswith("API Error:"):
                return result
            if attempt + 1 < self.settings.retry_attempts:
                time.sleep(self.settings.retry_backoff_seconds * (2**attempt))
        return result or SDKResult(error="API Error: Bhashini returned no result.")

    def transcribe(self, audio_wav: bytes, language: str) -> SDKResult[str]:
        model = self._select_model("asr", language)
        return self._call(lambda: self.client.asr(audio_wav, language, service_id=model))

    def translate(self, text: str, source: str, target: str) -> SDKResult[str]:
        if source == target:
            return SDKResult(value=text)
        model = self._select_model("nmt", source, target)
        return self._call(lambda: self.client.nmt(text, source, target, service_id=model))

    def synthesize(self, text: str, language: str) -> SDKResult[bytes]:
        model = self._select_model("tts", language)
        response = self._call(
            lambda: self.client.tts_service.synthesize(
                text,
                language,
                service_id=model,
                return_base64=True,
            )
        )
        if response.error is not None:
            return SDKResult(error=response.error)
        try:
            audio = base64.b64decode(response.unwrap(), validate=True)
        except BhashiniCallError as exc:
            return SDKResult(error=str(exc))
        except (ValueError, TypeError) as exc:
            logger.warning("bhashini_tts_payload_invalid error_type=%s", type(exc).__name__)
            return SDKResult(error="API Error: TTS returned invalid audio data.")
        if not audio:
            return SDKResult(error="API Error: TTS returned empty audio data.")
        return SDKResult(value=audio)
