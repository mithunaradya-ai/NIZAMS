import base64
from pathlib import Path

from bhashini_client.services.tts_service import TTSService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def test_tts_service_cases(tmp_path):
    output_file = tmp_path / "output.wav"
    audio_base64 = base64.b64encode(b"wave-bytes").decode("utf-8")
    long_text = "Hello world " * 50
    cases = [
        ("T024", "Normal text", "Hello", str(output_file), "Valid text is converted into an audio file."),
        ("T025", "Empty string", "", INPUT_ERROR, "Validation prevents empty API call."),
        ("T026", "Whitespace string", "   ", INPUT_ERROR, "Whitespace is trimmed before processing."),
        ("T027", "Numeric input", 123, INPUT_ERROR, "Numeric input is rejected because TTS expects text input."),
        ("T028", "Mixed input", "Hello नमस्ते 123", str(output_file), "Mixed text is synthesized as valid input."),
        ("T029", "Long text", long_text, str(output_file), "Long text is accepted and decoded into audio."),
        ("T030", "Invalid input type", ["Hello"], INPUT_ERROR, "Unsupported input type is rejected safely."),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason in cases:
        service = TTSService(handler=None)
        current_output = str(output_file)
        if output_file.exists():
            output_file.unlink()
        if expected_output != INPUT_ERROR:
            service.handler = type(
                "Handler",
                (),
                {
                    "post": lambda self, payload: {
                        "pipelineResponse": [{"audio": [{"audioContent": audio_base64}]}]
                    }
                },
            )()
        actual_output = service.synthesize(input_value, "en", output_file=current_output)
        expected_result = expected_output if expected_output not in {str(output_file)} else current_output
        log_test_result(
            test_id,
            "TTS",
            input_value,
            expected_result,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark="Base64 audio decoded successfully" if actual_output == current_output else "Validation handled correctly",
        )
        assert_service_output(actual_output, expected_result)
        if isinstance(actual_output, str) and actual_output.endswith(".wav"):
            assert Path(actual_output).exists()


def test_tts_payload_includes_optional_parameters(tmp_path):
    captured = {}
    output_file = tmp_path / "voice.wav"
    audio_base64 = base64.b64encode(b"voice-bytes").decode("utf-8")

    class Handler:
        def post(self, payload):
            captured["payload"] = payload
            return {"pipelineResponse": [{"audio": [{"audioContent": audio_base64}]}]}

    service = TTSService(Handler())
    actual_output = service.synthesize(
        "Hello",
        "en",
        gender="female",
        output_file=str(output_file),
        service_id="Bhashini/IITM/TTS",
        source_script_code="Latn",
        audio_format="wav",
        sampling_rate=16000,
        encoding="LINEAR16",
        supported_voice="female",
        domain="general",
        speed=1.1,
        speaker_name="demo-speaker",
        profanity_filter=False,
        text_normalization=True,
    )
    config = captured["payload"]["pipelineTasks"][0]["config"]
    log_test_result(
        "T031",
        "TTS",
        "Hello with optional parameters",
        str(output_file),
        actual_output,
        test_case_name="Optional parameters",
        logic_reason="Text to speech payload includes script code, audio settings, supported voice, and domain.",
        remark="Optional parameters working correctly",
    )
    assert actual_output == str(output_file)
    assert config["serviceId"] == "Bhashini/IITM/TTS"
    assert config["language"]["sourceScriptCode"] == "Latn"
    assert config["audioFormat"] == "wav"
    assert config["samplingRate"] == 16000
    assert config["encoding"] == "LINEAR16"
    assert config["supportedVoice"] == "female"
    assert config["domain"] == "general"
    assert config["speed"] == 1.1
    assert config["speakerName"] == "demo-speaker"
    assert config["profanityFilter"] is False


def test_tts_can_return_base64():
    audio_base64 = base64.b64encode(b"voice-bytes").decode("utf-8")

    class Handler:
        def post(self, payload):
            return {"pipelineResponse": [{"audio": [{"audioContent": audio_base64}]}]}

    service = TTSService(Handler())
    actual_output = service.synthesize("Hello", "en", return_base64=True)
    assert actual_output == audio_base64


def test_tts_rejects_invalid_optional_parameters():
    service = TTSService(handler=type("Handler", (), {"post": lambda self, payload: None})())
    assert_service_output(service.synthesize("Hello", "en", speed=0), INPUT_ERROR)
    assert_service_output(service.synthesize("Hello", "en", speaker_name="   "), INPUT_ERROR)
    assert_service_output(service.synthesize("Hello", "en", profanity_filter="no"), INPUT_ERROR)
