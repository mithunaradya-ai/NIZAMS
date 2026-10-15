from bhashini_client.services.transliteration_service import TransliterationService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def test_transliteration_service_cases():
    long_text = "namaste " * 30
    cases = [
        ("T032", "Normal text", "namaste", "नमस्ते", "Valid source text is converted into target script."),
        ("T033", "Empty string", "", INPUT_ERROR, "Validation prevents empty transliteration request."),
        ("T034", "Whitespace string", "   ", INPUT_ERROR, "Whitespace is trimmed before processing."),
        ("T035", "Numeric input", 123, INPUT_ERROR, "Numeric input is rejected because transliteration expects text."),
        ("T036", "Mixed input", "naमaste123", "नमस्ते", "Mixed text is accepted and transliterated."),
        ("T037", "Long text", long_text, "नमस्ते", "Long transliteration input is handled cleanly."),
        ("T038", "Invalid input type", ("namaste",), INPUT_ERROR, "Unsupported types are rejected safely."),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason in cases:
        service = TransliterationService(handler=None)
        if test_case_name in {"Normal text", "Mixed input", "Long text"}:
            service.handler = type(
                "Handler",
                (),
                {"post": lambda self, payload: {"pipelineResponse": [{"output": [{"target": "नमस्ते"}]}]}},
            )()
        actual_output = service.transliterate(input_value, "en", "hi")
        log_test_result(
            test_id,
            "Transliteration",
            input_value,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark="Script conversion working correctly" if actual_output == expected_output else "Validation handled correctly",
        )
        assert_service_output(actual_output, expected_output)


def test_transliteration_payload_includes_optional_parameters():
    captured = {}

    class Handler:
        def post(self, payload):
            captured["payload"] = payload
            return {"pipelineResponse": [{"output": [{"target": "नमस्ते"}]}]}

    service = TransliterationService(Handler())
    actual_output = service.transliterate(
        "namaste",
        "en",
        "hi",
        service_id="ai4bharat/indicxlit--cpu-fsv2",
        source_script_code="Latn",
        target_script_code="Deva",
        num_suggestions=1,
        is_sentence=True,
        numeric_transliteration=True,
    )
    config = captured["payload"]["pipelineTasks"][0]["config"]
    log_test_result(
        "T039",
        "Transliteration",
        "namaste with optional parameters",
        "नमस्ते",
        actual_output,
        test_case_name="Optional parameters",
        logic_reason="Script codes and transliteration options are included in the payload.",
        remark="Optional parameters working correctly",
    )
    assert actual_output == "नमस्ते"
    assert config["language"]["sourceScriptCode"] == "Latn"
    assert config["language"]["targetScriptCode"] == "Deva"
    assert config["numSuggestions"] == 1
    assert config["isSentence"] is True
    assert config["numericTransliteration"] is True


def test_transliteration_rejects_invalid_numeric_flag():
    service = TransliterationService(handler=type("Handler", (), {"post": lambda self, payload: None})())
    actual_output = service.transliterate("namaste", "en", "hi", numeric_transliteration="yes")
    assert_service_output(actual_output, INPUT_ERROR)
