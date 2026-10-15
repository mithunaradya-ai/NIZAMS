from bhashini_client.services.nmt_service import NMTService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def test_nmt_service_cases():
    long_text = "Hello world " * 100
    cases = [
        ("T015", "Normal text", "Hello", "translated hello", "Valid text is translated correctly."),
        ("T016", "Empty string", "", INPUT_ERROR, "Empty text is rejected before API call."),
        ("T017", "Whitespace string", "   ", INPUT_ERROR, "Whitespace-only text is rejected after trimming."),
        ("T018", "Numeric input", 123, INPUT_ERROR, "Numeric input is rejected because translation expects text."),
        ("T019", "Mixed input", "Hello namaste 123", "translated hello", "Mixed-language text is still treated as valid translation input."),
        ("T020", "Long text", long_text, "translated long text", "Long text is accepted and translated cleanly."),
        ("T021", "Invalid input type", {"text": "Hello"}, INPUT_ERROR, "Unsupported input types are rejected before API call."),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason in cases:
        service = NMTService(handler=None)
        if test_case_name in {"Normal text", "Mixed input"}:
            service.handler = type(
                "Handler",
                (),
                {"post": lambda self, payload: {"pipelineResponse": [{"output": [{"target": "translated hello"}]}]}},
            )()
        elif test_case_name == "Long text":
            service.handler = type(
                "Handler",
                (),
                {"post": lambda self, payload: {"pipelineResponse": [{"output": [{"target": "translated long text"}]}]}},
            )()
        actual_output = service.translate(input_value, "en", "hi")
        log_test_result(
            test_id,
            "NMT",
            input_value,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark="Working correctly" if expected_output == actual_output else "Check translation handling",
        )
        assert_service_output(actual_output, expected_output)


def test_nmt_payload_includes_optional_parameters():
    captured = {}

    class Handler:
        def post(self, payload):
            captured["payload"] = payload
            return {"pipelineResponse": [{"output": [{"target": "Hello"}]}]}

    service = NMTService(Handler())
    actual_output = service.translate(
        "namaste",
        "hi",
        "en",
        service_id="ai4bharat/indictrans-v2-all-gpu--t4",
        source_script_code="Deva",
        target_script_code="Latn",
        glossary={"namaste": "hello"},
        domain="general",
        gender="neutral",
        enable_number_translation=True,
        profanity_filter=False,
        pre_processors=["html"],
        post_processors=["glossary"],
    )
    config = captured["payload"]["pipelineTasks"][0]["config"]
    log_test_result(
        "T022",
        "NMT",
        "hi -> en with optional parameters",
        "Hello",
        actual_output,
        test_case_name="Optional parameters",
        logic_reason="Optional language script codes, glossary, domain, and processors are added to the translation payload.",
        remark="Optional parameters working correctly",
    )
    assert actual_output == "Hello"
    assert config["serviceId"] == "ai4bharat/indictrans-v2-all-gpu--t4"
    assert config["language"]["sourceLanguage"] == "hi"
    assert config["language"]["targetLanguage"] == "en"
    assert config["language"]["sourceScriptCode"] == "Deva"
    assert config["language"]["targetScriptCode"] == "Latn"
    assert config["glossary"] == {"namaste": "hello"}
    assert config["domain"] == "general"
    assert config["gender"] == "neutral"
    assert config["enableNumberTranslation"] is True
    assert config["profanityFilter"] is False
    assert config["preProcessors"] == ["html"]
    assert config["postProcessors"] == ["glossary"]


def test_nmt_uses_updated_default_service_id():
    captured = {}

    class Handler:
        def post(self, payload):
            captured["serviceId"] = payload["pipelineTasks"][0]["config"]["serviceId"]
            return {"pipelineResponse": [{"output": [{"target": "Hello"}]}]}

    service = NMTService(Handler())
    actual_output = service.translate("namaste", "hi", "en")
    log_test_result(
        "T023",
        "NMT",
        "hi-en service id",
        "Hello",
        actual_output,
        test_case_name="Updated default service id",
        logic_reason="The updated default NMT service id should be used for translation requests when no service id is passed.",
        remark="Default service id selected correctly",
    )
    assert actual_output == "Hello"
    assert captured["serviceId"] == "ai4bharat/indictrans-v2-all-gpu--t4"


def test_nmt_rejects_invalid_optional_parameters():
    service = NMTService(handler=type("Handler", (), {"post": lambda self, payload: None})())

    for kwargs in (
        {"pre_processors": ["xml"]},
        {"post_processors": ["punctuation"]},
        {"glossary": {}},
        {"enable_number_translation": "yes"},
        {"profanity_filter": "no"},
        {"post_processors": ["glossary"]},
    ):
        actual_output = service.translate("Hello", "en", "hi", **kwargs)
        assert_service_output(actual_output, INPUT_ERROR)
