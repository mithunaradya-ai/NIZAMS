import base64

from kiosk_app.bhashini import BhashiniGateway, SDKResult
from kiosk_app.errors import BhashiniCallError
from kiosk_tests.helpers import settings


class FakeSDK:
    def __init__(self, response):
        self.response = response
        self.tts_service = self.TTSService(self)

    def nmt(self, *_args, **_kwargs):
        return self.response

    def asr(self, *_args, **_kwargs):
        return self.response

    class TTSService:
        def __init__(self, parent):
            self.parent = parent

        def synthesize(self, *_args, **_kwargs):
            if isinstance(self.parent.response, str):
                return self.parent.response
            return base64.b64encode(b"RIFFtest").decode("ascii")


def model_lookup(service, language=None):
    return [{"serviceId": f"{service}-{language}"}]


def test_sdk_string_errors_become_domain_errors():
    for prefix in ("Input Error:", "Validation Error:", "API Error:"):
        gateway = BhashiniGateway(
            settings(),
            client=FakeSDK(f"{prefix} failed"),
            models_lookup=model_lookup,
        )
        result = gateway.translate("hello", "en", "hi")
        assert isinstance(result, SDKResult)
        assert result.error == f"{prefix} failed"
        try:
            result.unwrap()
        except BhashiniCallError as error:
            assert str(error) == f"{prefix} failed"
        else:
            raise AssertionError("SDK error string was not raised on unwrap.")


def test_dynamic_translation_is_not_retained_between_requests():
    calls = []

    class Client(FakeSDK):
        def nmt(self, text, source, target, **kwargs):
            calls.append((text, source, target, kwargs["service_id"]))
            return "வணக்கம்"

    gateway = BhashiniGateway(settings(), client=Client(None), models_lookup=model_lookup)
    assert gateway.translate("hello", "en", "ta").unwrap() == "வணக்கம்"
    assert gateway.translate("hello", "en", "ta").unwrap() == "வணக்கம்"
    assert len(calls) == 2


def test_tts_returns_audio_in_memory_without_a_temporary_file():
    gateway = BhashiniGateway(settings(), client=FakeSDK(None), models_lookup=model_lookup)
    assert gateway.synthesize("hello", "en").unwrap() == b"RIFFtest"
