from bhashini_client.services.text_normalization_service import TextNormalizationService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def test_text_normalization_cases():
    base64_like_text = "aSBnb3QgMjA2NTc3OCBydXBlZXMgcHJpemU/"
    cases = [
        ("T121", "Normal text", " i got 2065778 rupees prize?", "I got 2,065,778 rupees prize?", "Valid text is normalized through the text normalization endpoint.", "Working correctly"),
        ("T122", "Empty string", "", INPUT_ERROR, "Empty input is rejected.", "Validation handled correctly"),
        ("T123", "Whitespace string", "   ", INPUT_ERROR, "Whitespace input is rejected.", "Validation handled correctly"),
        ("T124", "Invalid input type", 123, INPUT_ERROR, "Numeric input is not accepted for this text-only service.", "Validation handled correctly"),
        ("T125", "Base64-like text", base64_like_text, "I got 2,065,778 rupees prize?", "Text normalization still accepts plain string inputs that resemble base64.", "Working correctly"),
        ("T126", "Missing language", "hello", INPUT_ERROR, "Source language is required for text normalization.", "Validation handled correctly"),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason, remark in cases:
        service = TextNormalizationService(handler=None)
        if expected_output != INPUT_ERROR:
            service.handler = type(
                "Handler",
                (),
                {"post": lambda self, payload, url=None, headers=None: {"output": [{"target": "I got 2,065,778 rupees prize?"}]}},
            )()
        actual_output = service.normalize(input_value, "" if test_case_name == "Missing language" else "en")
        log_test_result(
            test_id,
            "Text Normalization",
            input_value,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark=remark,
        )
        assert_service_output(actual_output, expected_output)


def test_text_normalization_payload():
    captured = {}

    class Handler:
        def post(self, payload, url=None, headers=None):
            captured["payload"] = payload
            captured["url"] = url
            return {"output": [{"target": "I got 2,065,778 rupees prize?"}]}

    service = TextNormalizationService(Handler())
    actual_output = service.normalize(" i got 2065778 rupees prize?", "en")
    log_test_result(
        "T127",
        "Text Normalization",
        " i got 2065778 rupees prize?",
        "I got 2,065,778 rupees prize?",
        actual_output,
        test_case_name="Payload structure",
        logic_reason="Text normalization payload preserves the cURL endpoint, service id, and language config.",
        remark="Payload working correctly",
    )
    assert actual_output == "I got 2,065,778 rupees prize?"
    assert captured["url"] == "https://dhruva-api.bhashini.gov.in/services/inference/textnormalization"
    assert captured["payload"]["config"]["serviceId"] == "bhashini/textnormalization/gpu-t4"
    assert captured["payload"]["config"]["language"]["sourceLanguage"] == "en"
