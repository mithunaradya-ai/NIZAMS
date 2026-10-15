"""Pre-generate translations and TTS for non-personal, static kiosk phrases."""

from __future__ import annotations

from kiosk_app.api import create_app
from kiosk_app.cache import STATIC_PHRASES_EN
from kiosk_app.config import LANGUAGES, Settings


def main() -> None:
    settings = Settings.from_env()
    application = create_app(settings)
    pipeline = application.state.pipeline
    for language in LANGUAGES:
        for phrase_id in STATIC_PHRASES_EN:
            result = pipeline.speak_static(phrase_id, language.code)
            if not result["audio_base64"]:
                raise RuntimeError(
                    f"Could not create static phrase {phrase_id} for language {language.code}."
                )
    print(f"Generated {len(LANGUAGES) * len(STATIC_PHRASES_EN)} static language/audio entries.")


if __name__ == "__main__":
    main()
