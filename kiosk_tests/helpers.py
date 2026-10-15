"""Shared test fixtures for provider and repository boundaries."""

from __future__ import annotations

from pathlib import Path

from kiosk_app.bhashini import SDKResult
from kiosk_app.config import Settings
from kiosk_app.schemas import SchemeRecord


def settings(**overrides) -> Settings:
    values = {
        "cache_directory": Path("test-cache"),
        "max_retrieval_results": 5,
    }
    values.update(overrides)
    return Settings(**values)


def sample_record(**overrides) -> SchemeRecord:
    values = {
        "scheme_id": "sample-1",
        "title": "Verified sample scheme",
        "summary": "Support is described by the record.",
        "benefits": ["Record benefit."],
        "eligibility": ["Record eligibility."],
        "documents": ["Record document."],
        "how_to_apply": ["Record application step."],
        "categories": ["farmers"],
    }
    values.update(overrides)
    return SchemeRecord(**values)


class FakeBhashini:
    """No-network stand-in using the SDK gateway's actual typed-result shape."""

    def __init__(self, transcript: str = "I need farmer support.") -> None:
        self.transcript = transcript

    def transcribe(self, _audio: bytes, _language: str) -> SDKResult[str]:
        return SDKResult(value=self.transcript)

    def translate(self, text: str, _source: str, _target: str) -> SDKResult[str]:
        return SDKResult(value=text)

    def synthesize(self, _text: str, _language: str) -> SDKResult[bytes]:
        return SDKResult(value=b"RIFFmockwav")
