import base64
import wave

from bhashini_client.services.speaker_verification_service import SpeakerVerificationService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def _create_wav_file(path, frames, sample_rate=16000):
    with wave.open(str(path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(sample_rate)
        audio_file.writeframes(frames)


def test_speaker_verification_cases(tmp_path):
    valid_audio_file = tmp_path / "sample.wav"
    corrupted_audio_file = tmp_path / "corrupted.wav"
    _create_wav_file(valid_audio_file, (b"\x01\x00" * 1600))
    corrupted_audio_file.write_bytes(b"not-a-valid-wave-file")
    audio_base64 = base64.b64encode(valid_audio_file.read_bytes()).decode("utf-8")

    cases = [
        ("T096", "Normal audio file", str(valid_audio_file), True, "Valid verification input returns a boolean result.", "Working correctly"),
        ("T097", "Empty string", "", INPUT_ERROR, "Empty audio is rejected.", "Validation handled correctly"),
        ("T098", "Whitespace string", "   ", INPUT_ERROR, "Whitespace audio is rejected.", "Validation handled correctly"),
        ("T099", "Invalid file path", str(tmp_path / "missing.wav"), INPUT_ERROR, "Missing file path is rejected.", "Validation handled correctly"),
        ("T100", "Numeric input", 123, INPUT_ERROR, "Numeric input is not valid audio input.", "Validation handled correctly"),
        ("T101", "Valid base64 audio", audio_base64, True, "Base64 audio is accepted for verification.", "Working correctly"),
        ("T102", "Corrupted wav file", str(corrupted_audio_file), INPUT_ERROR, "Corrupted audio is rejected before API call.", "Validation handled correctly"),
        ("T103", "Audio URI", "https://example.com/verify.wav", True, "Audio URI is accepted for verification.", "Working correctly"),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason, remark in cases:
        service = SpeakerVerificationService(handler=None)
        if expected_output != INPUT_ERROR:
            service.handler = type(
                "Handler",
                (),
                {"post": lambda self, payload, url=None, headers=None: {"pipelineResponse": [{"output": [{"verified": True, "score": 0.98}]}]}},
            )()
        actual_output = service.verify(input_value, "speaker-id-123")
        log_test_result(
            test_id,
            "Speaker Verification",
            input_value,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark=remark,
        )
        assert_service_output(actual_output, expected_output)


def test_speaker_verification_payload():
    captured = {}

    class Handler:
        def post(self, payload, url=None, headers=None):
            captured["payload"] = payload
            return {"pipelineResponse": [{"output": [{"score": 0.88}]}]}

    service = SpeakerVerificationService(Handler())
    actual_output = service.verify("https://example.com/speaker.wav", "a64c1f88-2e47-46df-9ec0-17d231e2e80e")
    config = captured["payload"]["pipelineTasks"][0]["config"]
    log_test_result(
        "T104",
        "Speaker Verification",
        "https://example.com/speaker.wav",
        0.88,
        actual_output,
        test_case_name="Payload structure",
        logic_reason="Speaker verification payload preserves the cURL taskType, service id, and speakerId field.",
        remark="Payload working correctly",
    )
    assert actual_output == 0.88
    assert config["serviceId"] == "bhashini/iitdharwad/speaker-verification"
    assert config["speakerId"] == "a64c1f88-2e47-46df-9ec0-17d231e2e80e"


def test_speaker_verification_nested_response():
    class Handler:
        def post(self, payload, url=None, headers=None):
            return {
                "pipelineResponse": [
                    {
                        "output": [
                            {
                                "result": {
                                    "verification": {
                                        "isVerified": True,
                                        "confidence": 0.97,
                                    }
                                }
                            }
                        ]
                    }
                ]
            }

    service = SpeakerVerificationService(Handler())
    actual_output = service.verify("https://example.com/speaker.wav", "speaker-id-123")
    assert actual_output is True
