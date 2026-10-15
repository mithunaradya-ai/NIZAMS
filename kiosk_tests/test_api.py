import base64
import io
import wave

from fastapi.testclient import TestClient

from kiosk_app.api import create_app
from kiosk_app.observability import StageMetrics
from kiosk_app.repository import InMemorySchemeRepository
from kiosk_tests.helpers import FakeBhashini, settings


def _wav_bytes():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\x00\x00" * 1600)
    return buffer.getvalue()


def _app(tmp_path):
    return create_app(
        settings(cache_directory=tmp_path),
        repository=InMemorySchemeRepository(),
        provider=None,
        bhashini=FakeBhashini(),
        metrics=StageMetrics(),
    )


def test_health_and_config_do_not_cache_session_responses(tmp_path):
    with TestClient(_app(tmp_path)) as client:
        health = client.get("/health")
        config = client.get("/api/config")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert config.headers["cache-control"].startswith("no-store")
    assert {item["code"] for item in config.json()["languages"]} == {
        "ta", "ml", "kn", "te", "hi", "mr", "en",
    }


def test_typed_browse_and_voice_routes_share_pipeline(tmp_path):
    wav = _wav_bytes()
    with TestClient(_app(tmp_path)) as client:
        typed = client.post(
            "/api/chat",
            json={"text": "farmers", "language": "en", "category": "farmers"},
        )
        browse = client.post("/api/browse", json={"category": "farmers", "language": "en"})
        voice = client.post(
            "/api/chat/voice",
            json={"audio_base64": base64.b64encode(wav).decode("ascii"), "language": "en"},
        )
    assert typed.status_code == 200
    assert browse.status_code == 200
    assert voice.status_code == 200
    assert voice.json()["transcript"] == "I need farmer support."
    assert typed.json()["answer"]["schemes"][0]["development_sample"] is True
