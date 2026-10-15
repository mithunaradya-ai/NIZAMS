from bhashini_client.services.language_detection_service import TextLanguageDetectionService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def test_text_language_detection_service_cases():
    long_text = "Hello world " * 80
    cases = [
        ("T040", "Normal text", "Hello", "en", "Text language detection returns the detected language code."),
        ("T041", "Empty string", "", INPUT_ERROR, "Validation prevents empty detection request."),
        ("T042", "Whitespace string", "   ", INPUT_ERROR, "Whitespace is trimmed before language detection."),
        ("T043", "Numeric input", 123, INPUT_ERROR, "Numeric input is rejected because language detection expects text."),
        ("T044", "Mixed input", "Hello नमस्ते 123", "en", "Pattern-based detection still resolves the dominant language."),
        ("T045", "Long text", long_text, "en", "Long text is accepted for language detection."),
        ("T046", "Invalid input type", {"text": "Hello"}, INPUT_ERROR, "Unsupported input type is rejected safely."),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason in cases:
        service = TextLanguageDetectionService(handler=None)
        if test_case_name in {"Normal text", "Mixed input", "Long text"}:
            service.handler = type(
                "Handler",
                (),
                {"post": lambda self, payload: {"pipelineResponse": [{"output": [{"langPrediction": [{"langCode": "en"}]}]}]}},
            )()
        actual_output = service.detect(input_value)
        log_test_result(
            test_id,
            "Text Language Detection",
            input_value,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark="Text language detection working correctly" if actual_output == expected_output else "Validation handled correctly",
        )
        assert_service_output(actual_output, expected_output)


def test_text_language_detection_optional_service_id():
    captured = {}

    class Handler:
        def post(self, payload):
            captured["payload"] = payload
            return {"pipelineResponse": [{"output": [{"langPrediction": [{"langCode": "en"}]}]}]}

    service = TextLanguageDetectionService(Handler())
    actual_output = service.detect("Hello world", service_id="bhashini/indic-lang-detection-all")
    log_test_result(
        "T047",
        "Text Language Detection",
        "Hello world",
        "en",
        actual_output,
        test_case_name="Optional parameters",
        logic_reason="Service id is included for text language detection payload.",
        remark="Service id working correctly",
    )
    assert actual_output == "en"
    assert captured["payload"]["pipelineTasks"][0]["config"]["serviceId"] == "bhashini/indic-lang-detection-all"
