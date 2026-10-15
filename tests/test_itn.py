from bhashini_client.services.itn_service import InverseTextNormalizationService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def test_inverse_text_normalization_cases():
    base64_like_text = "aSBnb3QgZml2ZSB0aG91c2FuZCBydXBlZXMgcHJpemU="
    cases = [
        ("T128", "Normal text", " i got five thousand rupees prize", "I got 5000 rupees prize", "Valid spoken-number text is normalized into numeric form.", "Working correctly"),
        ("T129", "Empty string", "", INPUT_ERROR, "Empty input is rejected.", "Validation handled correctly"),
        ("T130", "Whitespace string", "   ", INPUT_ERROR, "Whitespace input is rejected.", "Validation handled correctly"),
        ("T131", "Invalid input type", 123, INPUT_ERROR, "Numeric input is not accepted for this text-only service.", "Validation handled correctly"),
        ("T132", "Base64-like text", base64_like_text, "I got 5000 rupees prize", "ITN still accepts plain string inputs that resemble base64.", "Working correctly"),
        ("T133", "Missing language", "hello", INPUT_ERROR, "Source language is required for ITN.", "Validation handled correctly"),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason, remark in cases:
        service = InverseTextNormalizationService(handler=None)
        if expected_output != INPUT_ERROR:
            service.handler = type(
                "Handler",
                (),
                {"post": lambda self, payload, url=None, headers=None: {"output": [{"target": "I got 5000 rupees prize"}]}},
            )()
        actual_output = service.normalize(input_value, "" if test_case_name == "Missing language" else "en")
        log_test_result(
            test_id,
            "Inverse Text Normalization",
            input_value,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark=remark,
        )
        assert_service_output(actual_output, expected_output)


def test_inverse_text_normalization_payload():
    captured = {}

    class Handler:
        def post(self, payload, url=None, headers=None):
            captured["payload"] = payload
            captured["url"] = url
            return {"output": [{"target": "I got 5000 rupees prize"}]}

    service = InverseTextNormalizationService(Handler())
    actual_output = service.normalize(" i got five thousand rupees prize", "en")
    log_test_result(
        "T134",
        "Inverse Text Normalization",
        " i got five thousand rupees prize",
        "I got 5000 rupees prize",
        actual_output,
        test_case_name="Payload structure",
        logic_reason="ITN payload preserves the cURL endpoint, service id, and language config.",
        remark="Payload working correctly",
    )
    assert actual_output == "I got 5000 rupees prize"
    assert captured["url"] == "https://dhruva-api.bhashini.gov.in/services/inference/itn"
    assert captured["payload"]["config"]["serviceId"] == "bhashini/itn/gpu-t4"
    assert captured["payload"]["config"]["language"]["sourceLanguage"] == "en"
