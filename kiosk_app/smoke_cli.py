"""Run the same voice-question pipeline against a 16 kHz WAV file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .api import create_app
from .config import Settings
from .pipeline import ChatPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Test the schemes kiosk pipeline using a WAV file.")
    parser.add_argument("wav_file", type=Path, help="WAV file containing a spoken question")
    parser.add_argument("--language", required=True, choices=("ta", "ml", "kn", "te", "hi", "mr", "en"))
    arguments = parser.parse_args()
    audio = arguments.wav_file.read_bytes()
    application = create_app(Settings.from_env())
    pipeline: ChatPipeline = application.state.pipeline
    result = pipeline.answer_audio(audio, arguments.language)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
