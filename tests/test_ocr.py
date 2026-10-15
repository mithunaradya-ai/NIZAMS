from bhashini_client.services.ocr_service import OCRService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def test_ocr_service_cases(tmp_path):
    image_file = tmp_path / "sample.png"
    handwritten_image = tmp_path / "handwritten.png"
    empty_image = tmp_path / "empty.png"
    image_file.write_bytes(b"fake-image")
    handwritten_image.write_bytes(b"handwritten-image")
    empty_image.write_bytes(b"")

    cases = [
        ("T056", "Normal image", str(image_file), "DEMO TEXT", "Printed image text is extracted cleanly."),
        ("T057", "Empty string", "", INPUT_ERROR, "Validation prevents empty OCR request."),
        ("T058", "Whitespace string", "   ", INPUT_ERROR, "Whitespace image path is rejected."),
        ("T059", "Numeric input", 123, INPUT_ERROR, "OCR expects an image path, not numeric input."),
        ("T060", "Invalid file path", str(tmp_path / "missing.png"), INPUT_ERROR, "Invalid image path is handled safely."),
        ("T061", "Empty image file", str(empty_image), INPUT_ERROR, "Empty image file is rejected before API call."),
        ("T062", "Handwritten image", str(handwritten_image), "DEMO TEXT", "Handwritten OCR is treated as a valid advanced case."),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason in cases:
        service = OCRService(handler=None)
        if test_case_name in {"Normal image", "Handwritten image"}:
            service.handler = type(
                "Handler",
                (),
                {"post": lambda self, payload: {"pipelineResponse": [{"output": [{"source": "DEMO TEXT"}]}]}},
            )()
        actual_output = service.extract_text(input_value, "en")
        log_test_result(
            test_id,
            "OCR",
            input_value,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark="OCR working correctly" if actual_output == expected_output else "Validation handled correctly",
        )
        assert_service_output(actual_output, expected_output)


def test_ocr_payload_includes_optional_parameters(tmp_path):
    captured = {}
    image_file = tmp_path / "sample.png"
    image_file.write_bytes(b"printed-image")

    class Handler:
        def post(self, payload):
            captured["payload"] = payload
            return {"pipelineResponse": [{"output": [{"source": "DEMO TEXT"}]}]}

    service = OCRService(Handler())
    actual_output = service.extract_text(
        str(image_file),
        "en",
        service_id="bhashini/iiith-bhasha-ocr",
        source_script_code="Latn",
        domain="general",
        text_detection="False",
    )
    config = captured["payload"]["pipelineTasks"][0]["config"]
    log_test_result(
        "T063",
        "OCR",
        str(image_file),
        "DEMO TEXT",
        actual_output,
        test_case_name="Optional parameters",
        logic_reason="OCR payload includes service id, script code, domain, and text detection mode.",
        remark="Optional parameters working correctly",
    )
    assert actual_output == "DEMO TEXT"
    assert config["serviceId"] == "bhashini/iiith-bhasha-ocr"
    assert config["language"]["sourceScriptCode"] == "Latn"
    assert config["domain"] == "general"
    assert config["textDetection"] == "False"
