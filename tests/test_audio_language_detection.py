import base64
import wave

from bhashini_client.services.audio_language_detection_service import AudioLanguageDetectionService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def _create_wav_file(path, frames, sample_rate=16000):
    with wave.open(str(path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(sample_rate)
        audio_file.writeframes(frames)


def test_audio_language_detection_cases(tmp_path):
    valid_audio_file = tmp_path / "sample.wav"
    corrupted_audio_file = tmp_path / "corrupted.wav"

    _create_wav_file(valid_audio_file, (b"\x01\x00" * 48000))
    corrupted_audio_file.write_bytes(b"not-a-valid-wave-file")

    audio_base64 = base64.b64encode(valid_audio_file.read_bytes()).decode("utf-8")

    cases = [
        ("T071", "Normal audio file", str(valid_audio_file), "hi", "Valid WAV audio is accepted and the top predicted language code is returned.", "Working correctly"),
        ("T072", "Empty string", "", INPUT_ERROR, "Validation prevents empty audio language detection requests.", "Validation handled correctly"),
        ("T073", "Whitespace string", "   ", INPUT_ERROR, "Whitespace-only audio input is rejected after trimming.", "Validation handled correctly"),
        ("T074", "Invalid file path", str(tmp_path / "missing.wav"), INPUT_ERROR, "Missing audio files are rejected safely before API call.", "Validation handled correctly"),
        ("T075", "Numeric input", 123, INPUT_ERROR, "Numeric input is not accepted for audio language detection.", "Validation handled correctly"),
        ("T076", "Valid base64 audio", audio_base64, "hi", "Base64 WAV audio is accepted directly and language detection succeeds.", "Working correctly"),
        ("T077", "Corrupted wav file", str(corrupted_audio_file), INPUT_ERROR, "Corrupted audio is rejected during WAV validation.", "Validation handled correctly"),
        ("T077A", "Audio URI", "https://example.com/audio.wav", "hi", "Audio URI is accepted for language detection without local decoding.", "Working correctly"),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason, remark in cases:
        service = AudioLanguageDetectionService(handler=None)
        if expected_output != INPUT_ERROR:
            service.handler = type(
                "Handler",
                (),
                {"post": lambda self, payload: {"pipelineResponse": [{"output": [{"langPrediction": [{"langCode": "hi"}]}]}]}},
            )()
        actual_output = service.detect(input_value)
        log_test_result(
            test_id,
            "Audio Language Detection",
            input_value,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark=remark,
        )
        assert_service_output(actual_output, expected_output)


def test_audio_language_detection_service_id_and_fallback(tmp_path):
    captured_service_ids = []
    audio_file = tmp_path / "sample.wav"
    _create_wav_file(audio_file, (b"\x01\x00" * 48000))

    class Handler:
        def post(self, payload):
            service_id = payload["pipelineTasks"][0]["config"]["serviceId"]
            captured_service_ids.append(service_id)
            if service_id == "bhashini/iitmandi/audio-lang-detection/gpu":
                return None
            return {"pipelineResponse": [{"output": [{"langPrediction": [{"langCode": "en"}]}]}]}

    service = AudioLanguageDetectionService(Handler())
    actual_output = service.detect(str(audio_file))
    log_test_result(
        "T078",
        "Audio Language Detection",
        str(audio_file),
        "en",
        actual_output,
        test_case_name="Fallback service id",
        logic_reason="When the primary audio language detection model fails, the fallback service id is attempted and parsed cleanly.",
        remark="Fallback handling working correctly",
    )
    assert actual_output == "en"
    assert captured_service_ids == [
        "bhashini/iitmandi/audio-lang-detection/gpu",
        "bhashini/ald",
    ]


def test_audio_language_detection_models_listing():
    service = AudioLanguageDetectionService(handler=type("Handler", (), {"post": lambda self, payload: None})())
    models = service.get_supported_models(language="hi")
    assert isinstance(models, list)
    assert models
