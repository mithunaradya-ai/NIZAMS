import json
from io import BytesIO

import pytest

import kiosk_app.llm as llm
from kiosk_app.llm import AnthropicProvider, GeminiProvider, OpenAICompatibleProvider
from kiosk_tests.helpers import settings


class FakeResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return self.body


@pytest.mark.parametrize(
    ("provider_type", "response", "expected_url"),
    [
        (GeminiProvider, {"candidates": [{"content": {"parts": [{"text": '{"ok":true}'}]}}]}, "generateContent"),
        (AnthropicProvider, {"content": [{"type": "text", "text": '{"ok":true}'}]}, "/v1/messages"),
        (OpenAICompatibleProvider, {"choices": [{"message": {"content": '{"ok":true}'}}]}, "/chat/completions"),
    ],
)
def test_provider_adapters_parse_structured_json(monkeypatch, provider_type, response, expected_url):
    requests = []

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        return FakeResponse(response)

    monkeypatch.setattr(llm, "urlopen", fake_urlopen)
    configuration = settings(
        llm_api_key="test-key",
        llm_model="test-model",
        llm_base_url="https://llm.example/v1" if provider_type is OpenAICompatibleProvider else "",
    )
    provider = provider_type(configuration)
    assert provider.complete_json("system", "prompt", {"type": "object"}) == {"ok": True}
    assert expected_url in requests[0][0].full_url
    assert requests[0][1] == configuration.request_timeout_seconds
