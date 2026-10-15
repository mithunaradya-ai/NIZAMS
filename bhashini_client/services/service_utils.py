from __future__ import annotations

from typing import Any


INPUT_ERROR_PREFIX = "Input Error:"
VALIDATION_ERROR_PREFIX = "Validation Error:"
API_ERROR_PREFIX = "API Error:"


def input_error(message: str) -> str:
    return f"{INPUT_ERROR_PREFIX} {message}"


def validation_error(message: str) -> str:
    return f"{VALIDATION_ERROR_PREFIX} {message}"


def api_error(message: str) -> str:
    return f"{API_ERROR_PREFIX} {message}"


def is_error_response(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(
        (INPUT_ERROR_PREFIX, VALIDATION_ERROR_PREFIX, API_ERROR_PREFIX)
    )


def require_text(value: Any, *, field_name: str = "text") -> str:
    if not isinstance(value, str):
        return input_error(
            f"{field_name.capitalize()} input must be provided as a non-empty string."
        )
    cleaned_value = value.strip()
    if not cleaned_value:
        return input_error(
            f"{field_name.capitalize()} input is empty. Please provide a non-empty string."
        )
    return cleaned_value


def require_language(value: Any, *, field_name: str = "language") -> str:
    if not isinstance(value, str):
        return input_error(
            f"{field_name.replace('_', ' ').capitalize()} is required as a language code string."
        )
    cleaned_value = value.strip().lower()
    if not cleaned_value:
        return input_error(
            f"{field_name.replace('_', ' ').capitalize()} is missing. Please provide a valid language code."
        )
    return cleaned_value


def require_identifier(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        return input_error(
            f"{field_name.replace('_', ' ').capitalize()} must be provided as a non-empty string."
        )
    cleaned_value = value.strip()
    if not cleaned_value:
        return input_error(
            f"{field_name.replace('_', ' ').capitalize()} is missing. Please provide a non-empty value."
        )
    return cleaned_value


def require_output_file(value: Any, *, field_name: str = "output_file") -> str:
    return require_identifier(value, field_name=field_name)
