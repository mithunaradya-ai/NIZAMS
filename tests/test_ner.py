from bhashini_client.services.ner_service import NERService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def test_ner_service_cases():
    expected_entities = {
        "entities": [
            {"entity": "Narendra", "label": "PERSON"},
            {"entity": "Delhi", "label": "PLACE"},
        ]
    }
    long_text = "Narendra Modi visited Delhi. " * 20
    cases = [
        ("T048", "Normal text", "Narendra Modi visited Delhi.", expected_entities, "Entity tagging extracts person and location terms."),
        ("T049", "Empty string", "", INPUT_ERROR, "Validation prevents empty NER request."),
        ("T050", "Whitespace string", "   ", INPUT_ERROR, "Whitespace is trimmed before entity extraction."),
        ("T051", "Numeric input", 123, INPUT_ERROR, "Numeric input is rejected because NER expects text input."),
        ("T052", "Mixed input", "Narendra मोदी Delhi", expected_entities, "Mixed text is still processed for named entities."),
        ("T053", "Long text", long_text, expected_entities, "Long text is accepted for entity tagging."),
        ("T054", "Invalid input type", ["Narendra"], INPUT_ERROR, "Unsupported input type is rejected safely."),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason in cases:
        service = NERService(handler=None)
        if test_case_name in {"Normal text", "Mixed input", "Long text"}:
            service.handler = type(
                "Handler",
                (),
                {
                    "post": lambda self, payload: {
                        "pipelineResponse": [
                            {
                                "output": [
                                    {
                                        "entities": [
                                            {"entity": "Narendra", "label": "PERSON"},
                                            {"entity": "Delhi", "label": "PLACE"},
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                },
            )()
        actual_output = service.recognize_entities(input_value, "en")
        log_test_result(
            test_id,
            "NER",
            input_value,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark="NER working correctly" if actual_output == expected_output else "Validation handled correctly",
        )
        assert_service_output(actual_output, expected_output)


def test_ner_payload_includes_optional_parameters():
    captured = {}

    class Handler:
        def post(self, payload):
            captured["payload"] = payload
            return {"pipelineResponse": [{"output": [{"entities": [{"entity": "Narendra", "label": "PERSON"}]}]}]}

    service = NERService(Handler())
    actual_output = service.recognize_entities(
        "Narendra Modi",
        "en",
        service_id="bhashini/aukbc/ner",
        source_script_code="Latn",
    )
    config = captured["payload"]["pipelineTasks"][0]["config"]
    expected_output = {"entities": [{"entity": "Narendra", "label": "PERSON"}]}
    log_test_result(
        "T055",
        "NER",
        "Narendra Modi with optional parameters",
        expected_output,
        actual_output,
        test_case_name="Optional parameters",
        logic_reason="Entity tagging payload includes service id, script code, and domain.",
        remark="Optional parameters working correctly",
    )
    assert actual_output == expected_output
    assert config["serviceId"] == "bhashini/aukbc/ner"
    assert config["language"]["sourceScriptCode"] == "Latn"


def test_ner_model_listing():
    service = NERService(handler=type("Handler", (), {"post": lambda self, payload: None})())
    models = service.get_supported_models(language="hi")
    assert isinstance(models, list)
    assert models
