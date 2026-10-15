import base64
import wave

from bhashini_client.services.speaker_enrollment_service import SpeakerEnrollmentService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def _create_wav_file(path, frames, sample_rate=16000):
    with wave.open(str(path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(sample_rate)
        audio_file.writeframes(frames)


def test_speaker_enrollment_cases(tmp_path):
    valid_audio_file = tmp_path / "sample.wav"
    corrupted_audio_file = tmp_path / "corrupted.wav"
    _create_wav_file(valid_audio_file, (b"\x01\x00" * 1600))
    corrupted_audio_file.write_bytes(b"not-a-valid-wave-file")
    audio_base64 = base64.b64encode(valid_audio_file.read_bytes()).decode("utf-8")

    cases = [
        ("T087", "Normal audio file", str(valid_audio_file), "speaker-123", "Valid WAV audio returns a speaker id.", "Working correctly"),
        ("T088", "Empty string", "", INPUT_ERROR, "Empty audio is rejected.", "Validation handled correctly"),
        ("T089", "Whitespace string", "   ", INPUT_ERROR, "Whitespace audio is rejected.", "Validation handled correctly"),
        ("T090", "Invalid file path", str(tmp_path / "missing.wav"), INPUT_ERROR, "Missing file path is rejected.", "Validation handled correctly"),
        ("T091", "Numeric input", 123, INPUT_ERROR, "Numeric input is not valid audio input.", "Validation handled correctly"),
        ("T092", "Valid base64 audio", audio_base64, "speaker-123", "Base64 audio is accepted for enrollment.", "Working correctly"),
        ("T093", "Corrupted wav file", str(corrupted_audio_file), INPUT_ERROR, "Corrupted audio is rejected before API call.", "Validation handled correctly"),
        ("T094", "Audio URI", "https://example.com/enrol.wav", "speaker-123", "Audio URI is accepted for enrollment.", "Working correctly"),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason, remark in cases:
        service = SpeakerEnrollmentService(handler=None)
        if expected_output != INPUT_ERROR:
            service.handler = type(
                "Handler",
                (),
                {"post": lambda self, payload, url=None, headers=None: {"pipelineResponse": [{"output": [{"speakerId": "speaker-123"}]}]}},
            )()
        actual_output = service.enroll(input_value, "demo-speaker")
        log_test_result(
            test_id,
            "Speaker Enrollment",
            input_value,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark=remark,
        )
        assert_service_output(actual_output, expected_output)


def test_speaker_enrollment_payload(tmp_path):
    captured = {}
    audio_file = tmp_path / "sample.wav"
    _create_wav_file(audio_file, (b"\x01\x00" * 1600))

    class Handler:
        def post(self, payload, url=None, headers=None):
            captured["payload"] = payload
            return {"pipelineResponse": [{"output": [{"speakerId": "speaker-999"}]}]}

    service = SpeakerEnrollmentService(Handler())
    actual_output = service.enroll(str(audio_file), "testData1108")
    config = captured["payload"]["pipelineTasks"][0]["config"]
    log_test_result(
        "T095",
        "Speaker Enrollment",
        str(audio_file),
        "speaker-999",
        actual_output,
        test_case_name="Payload structure",
        logic_reason="Speaker enrollment payload preserves the cURL taskType, service id, and speakerName field.",
        remark="Payload working correctly",
    )
    assert actual_output == "speaker-999"
    assert config["serviceId"] == "bhashini/iitdharwad/speaker-enrollment"
    assert config["speakerName"] == "testData1108"
