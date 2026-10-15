"""Tests for the language detection service."""

from bhashini_client.services.language_detection_service import LanguageDetectionService

from .conftest import MockHandler


def test_language_detection_normal_case(record_result):
    handler = MockHandler(
        {
            "pipelineResponse": [
                {
                    "output": [
                        {
                            "langPrediction": [
                                {
                                    "langCode": "hi",
                                    "langScore": 0.99,
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    )
    service = LanguageDetectionService(handler)
    actual = service.detect_language("namaste duniya")
    expected = {"language": "hi", "score": 0.99}
    record_result("LD-001", "Language Detection", "namaste duniya", expected, actual)
    assert actual == expected


def test_language_detection_empty_input(record_result):
    handler = MockHandler({})
    service = LanguageDetectionService(handler)
    actual = service.detect_language("")
    expected = "Invalid input"
    record_result("LD-002", "Language Detection", "", expected, actual)
    assert actual == expected
    assert handler.call_count == 0


def test_language_detection_whitespace_input(record_result):
    handler = MockHandler({})
    service = LanguageDetectionService(handler)
    actual = service.detect_language("   ")
    expected = "Invalid input"
    record_result("LD-003", "Language Detection", "   ", expected, actual)
    assert actual == expected
    assert handler.call_count == 0


def test_language_detection_numeric_input(record_result):
    handler = MockHandler({})
    service = LanguageDetectionService(handler)
    actual = service.detect_language("12345")
    expected = "Invalid input"
    record_result("LD-004", "Language Detection", "12345", expected, actual)
    assert actual == expected
    assert handler.call_count == 0


def test_language_detection_mixed_input(record_result):
    handler = MockHandler(
        {
            "pipelineResponse": [
                {
                    "output": [
                        {
                            "langPrediction": [
                                {
                                    "langCode": "en",
                                    "langScore": 0.76,
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    )
    service = LanguageDetectionService(handler)
    actual = service.detect_language("Invoice 123 ready")
    expected = {"language": "en", "score": 0.76}
    record_result("LD-005", "Language Detection", "Invoice 123 ready", expected, actual)
    assert actual == expected


def test_language_detection_invalid_input_type(record_result):
    handler = MockHandler({})
    service = LanguageDetectionService(handler)
    actual = service.detect_language(None)
    expected = "Invalid input"
    record_result("LD-006", "Language Detection", None, expected, actual)
    assert actual == expected
    assert handler.call_count == 0


def test_language_detection_api_error(record_result):
    handler = MockHandler(None)
    service = LanguageDetectionService(handler)
    actual = service.detect_language("namaste duniya")
    expected = "API Error"
    record_result("LD-007", "Language Detection", "namaste duniya", expected, actual)
    assert actual == expected


def test_language_detection_default_service_id_and_models():
    captured = {}

    class Handler:
        def post(self, payload):
            captured["serviceId"] = payload["pipelineTasks"][0]["config"]["serviceId"]
            return {"pipelineResponse": [{"output": [{"langPrediction": [{"langCode": "en"}]}]}]}

    service = LanguageDetectionService(Handler())
    actual_output = service.detect("Hello world")
    assert actual_output == "en"
    assert captured["serviceId"] == service.DEFAULT_SERVICE_ID
    models = service.get_supported_models(language="hi")
    assert isinstance(models, list)
    assert models
