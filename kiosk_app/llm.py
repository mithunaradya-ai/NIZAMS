"""Provider-agnostic JSON-only LLM adapters with bounded retries."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from pydantic import BaseModel, ValidationError

from .config import Settings
from .errors import ProviderError

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Contract implemented by all configurable LLM providers."""

    @abstractmethod
    def complete_json(self, system: str, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Return a JSON object matching the supplied schema."""


class HTTPJSONProvider(LLMProvider):
    """Shared bounded-timeout/retry transport for remote JSON model providers."""

    def __init__(self, settings: Settings, api_key: str | None = None) -> None:
        self.settings = settings
        self.api_key = api_key if api_key is not None else settings.llm_api_key

    def _request(self, url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        last_error = "provider request failed"
        for attempt in range(self.settings.retry_attempts):
            request = Request(url, data=body, headers=headers, method="POST")
            try:
                with urlopen(request, timeout=self.settings.request_timeout_seconds) as response:
                    decoded = json.loads(response.read().decode("utf-8"))
                if not isinstance(decoded, dict):
                    raise ProviderError("Provider response was not a JSON object.")
                return decoded
            except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                last_error = type(exc).__name__
                if isinstance(exc, HTTPError) and exc.code < 500 and exc.code != 429:
                    break
                if attempt + 1 < self.settings.retry_attempts:
                    time.sleep(self.settings.retry_backoff_seconds * (2**attempt))
        logger.warning("llm_request_failed provider=%s error_type=%s", type(self).__name__, last_error)
        raise ProviderError(f"LLM provider request failed ({last_error}).")

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderError("LLM provider returned invalid JSON.") from exc
        if not isinstance(parsed, dict):
            raise ProviderError("LLM provider returned a non-object JSON value.")
        return parsed

    @staticmethod
    def _schema_prompt(system: str, schema: dict[str, Any]) -> str:
        return (
            f"{system}\nReturn one JSON object only, matching this JSON Schema exactly:\n"
            f"{json.dumps(schema, ensure_ascii=False, separators=(',', ':'))}"
        )


class GeminiProvider(HTTPJSONProvider):
    """Google Gemini generateContent adapter using Google's REST message format."""

    def complete_json(self, system: str, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        model = quote(self.settings.llm_model, safe="-_.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": self._schema_prompt(system, schema)}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        response = self._request(
            url,
            {"Content-Type": "application/json", "x-goog-api-key": self.api_key},
            payload,
        )
        try:
            text = response["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Gemini response did not contain JSON text.") from exc
        return self._parse_json(text)


class AnthropicProvider(HTTPJSONProvider):
    """Anthropic Messages API adapter."""

    def complete_json(self, system: str, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        url = self.settings.llm_base_url or "https://api.anthropic.com/v1/messages"
        payload = {
            "model": self.settings.llm_model,
            "max_tokens": 1200,
            "system": self._schema_prompt(system, schema),
            "messages": [{"role": "user", "content": prompt}],
        }
        response = self._request(
            url,
            {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            payload,
        )
        try:
            text = next(item["text"] for item in response["content"] if item.get("type") == "text")
        except (KeyError, StopIteration, TypeError) as exc:
            raise ProviderError("Anthropic response did not contain JSON text.") from exc
        return self._parse_json(text)


class OpenAICompatibleProvider(HTTPJSONProvider):
    """Adapter for OpenAI Chat Completions-compatible endpoints."""

    def complete_json(self, system: str, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        base_url = (self.settings.llm_base_url or "https://api.openai.com/v1").rstrip("/")
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": self._schema_prompt(system, schema)},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        response = self._request(
            f"{base_url}/chat/completions",
            {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            payload,
        )
        try:
            text = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("OpenAI-compatible response did not contain JSON text.") from exc
        return self._parse_json(text)


def create_provider(settings: Settings) -> LLMProvider | None:
    """Create the configured provider, or select deterministic offline mode."""
    providers: dict[str, type[HTTPJSONProvider]] = {
        "gemini": GeminiProvider,
        "anthropic": AnthropicProvider,
        "openai-compatible": OpenAICompatibleProvider,
    }
    if settings.llm_provider == "none":
        return None
    try:
        return providers[settings.llm_provider](settings)
    except KeyError as exc:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}") from exc


def structured_completion(provider: LLMProvider, system: str, prompt: str, schema: type[BaseModel]) -> BaseModel:
    """Generate JSON and validate it against the selected Pydantic output schema."""
    try:
        value = provider.complete_json(system, prompt, schema.model_json_schema())
        return schema.model_validate(value)
    except ValidationError as exc:
        raise ProviderError(f"LLM output did not match {schema.__name__}.") from exc
