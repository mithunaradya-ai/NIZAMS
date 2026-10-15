from bhashini_client.services.image_lang_detection_service import ImageLanguageDetectionService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def test_image_language_detection_cases(tmp_path):
    local_image = tmp_path / "sample.png"
    local_image.write_bytes(b"fake-image")
    base64_input = "ZmFrZS1pbWFnZS1iYXNlNjQ="

    cases = [
        ("T113", "Normal image URI", "https://i.pinimg.com/originals/ed/35/32/ed353250ee99d6717de6d04625ec4384.jpg", "en", "Valid image URI returns a language code.", "Working correctly"),
        ("T114", "Empty string", "", INPUT_ERROR, "Empty image input is rejected.", "Validation handled correctly"),
        ("T115", "Whitespace string", "   ", INPUT_ERROR, "Whitespace image input is rejected.", "Validation handled correctly"),
        ("T116", "Invalid input type", 123, INPUT_ERROR, "Numeric input is not valid image input.", "Validation handled correctly"),
        ("T117", "Base64 input", base64_input, "en", "Base64 image input is accepted and sent as imageContent.", "Working correctly"),
        ("T118", "Invalid file path", str(tmp_path / "missing.png"), INPUT_ERROR, "Invalid local path is rejected.", "Validation handled correctly"),
        ("T119", "Local image path", str(local_image), "en", "Local file paths are base64-encoded and sent as imageContent.", "Working correctly"),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason, remark in cases:
        service = ImageLanguageDetectionService(handler=None)
        if expected_output != INPUT_ERROR:
            service.handler = type(
                "Handler",
                (),
                {"post": lambda self, payload, url=None, headers=None: {"pipelineResponse": [{"output": [{"langPrediction": [{"langCode": "en"}]}]}]}},
            )()
        actual_output = service.detect(input_value)
        log_test_result(
            test_id,
            "Image Language Detection",
            input_value,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark=remark,
        )
        assert_service_output(actual_output, expected_output)


def test_image_language_detection_payload():
    captured = {}

    class Handler:
        def post(self, payload, url=None, headers=None):
            captured["payload"] = payload
            captured["url"] = url
            return {"pipelineResponse": [{"output": [{"langPrediction": [{"langCode": "hi"}]}]}]}

    service = ImageLanguageDetectionService(Handler())
    actual_output = service.detect("https://example.com/image.jpg")
    log_test_result(
        "T120",
        "Image Language Detection",
        "https://example.com/image.jpg",
        "hi",
        actual_output,
        test_case_name="Payload structure",
        logic_reason="Image language detection payload preserves the cURL endpoint, taskType, and service id.",
        remark="Payload working correctly",
    )
    assert actual_output == "hi"
    assert captured["url"] == "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
    assert captured["payload"]["pipelineTasks"][0]["taskType"] == "img-lang-detection"
    assert captured["payload"]["pipelineTasks"][0]["config"]["serviceId"] == "bhashini/iiith/img-lang-detection"
    assert captured["payload"]["inputData"]["image"][0]["imageUri"] == "https://example.com/image.jpg"


def test_image_language_detection_local_image_payload(tmp_path):
    captured = {}
    local_image = tmp_path / "sample.png"
    local_image.write_bytes(b"fake-image")

    class Handler:
        def post(self, payload, url=None, headers=None):
            captured["payload"] = payload
            captured["url"] = url
            return {"pipelineResponse": [{"output": [{"langPrediction": [{"langCode": "en"}]}]}]}

    service = ImageLanguageDetectionService(Handler())
    actual_output = service.detect(str(local_image))
    assert actual_output == "en"
    assert captured["url"] == "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
    assert "imageContent" in captured["payload"]["inputData"]["image"][0]
