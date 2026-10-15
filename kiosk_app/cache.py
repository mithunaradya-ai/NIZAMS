"""Disk cache restricted to pre-approved, non-personal static phrases."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

STATIC_PHRASES_EN = {
    "greeting": "Welcome. Ask me about government schemes.",
    "connection_error": "Sorry, there is a connection problem. Please try again.",
    "no_results": "No matching scheme information was found in the available records.",
}


def _key(text: str, language: str, voice: str = "") -> str:
    raw = f"{text}\0{language}\0{voice}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class StaticPhraseCache:
    """Persist only static UI translations and audio; never user question or answer data."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory / "static-phrases"
        self.directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def is_static_english(text: str) -> bool:
        return text in STATIC_PHRASES_EN.values()

    def get_translation(self, text: str, language: str) -> str | None:
        if not self.is_static_english(text):
            return None
        path = self.directory / f"{_key(text, language)}.json"
        if not path.is_file():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        return value["translation"]

    def store_translation(self, text: str, language: str, translation: str) -> None:
        if self.is_static_english(text):
            path = self.directory / f"{_key(text, language)}.json"
            path.write_text(
                json.dumps({"translation": translation}, ensure_ascii=False),
                encoding="utf-8",
            )

    def get_audio(self, text: str, language: str, voice: str = "female") -> bytes | None:
        if not any(text == phrase for phrase in STATIC_PHRASES_EN.values()):
            return None
        path = self.directory / f"{_key(text, language, voice)}.wav"
        return path.read_bytes() if path.is_file() else None

    def store_audio(self, text: str, language: str, audio: bytes, voice: str = "female") -> None:
        if any(text == phrase for phrase in STATIC_PHRASES_EN.values()):
            (self.directory / f"{_key(text, language, voice)}.wav").write_bytes(audio)
