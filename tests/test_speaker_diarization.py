import base64
import wave

from bhashini_client.services.speaker_diarization_service import SpeakerDiarizationService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def _create_wav_file(path, frames, sample_rate=16000):
    with wave.open(str(path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(sample_rate)
        audio_file.writeframes(frames)


def test_speaker_diarization_cases(tmp_path):
    valid_audio_file = tmp_path / "sample.wav"
    corrupted_audio_file = tmp_path / "corrupted.wav"

    _create_wav_file(valid_audio_file, (b"\x01\x00" * 1600))
    corrupted_audio_file.write_bytes(b"not-a-valid-wave-file")

    audio_base64 = base64.b64encode(valid_audio_file.read_bytes()).decode("utf-8")
    expected_segments = [
        {"speaker": "speaker1", "timestamps": [{"start_time": 0.0, "duration": 1.25}]},
        {"speaker": "speaker2", "timestamps": [{"start_time": 1.25, "duration": 0.75}]},
    ]

    cases = [
        ("T079", "Normal audio file", str(valid_audio_file), expected_segments, "Valid WAV audio returns speakers with timestamps.", "Working correctly"),
        ("T080", "Empty string", "", INPUT_ERROR, "Validation prevents empty speaker diarization requests.", "Validation handled correctly"),
        ("T081", "Whitespace string", "   ", INPUT_ERROR, "Whitespace-only audio input is rejected after trimming.", "Validation handled correctly"),
        ("T082", "Invalid file path", str(tmp_path / "missing.wav"), INPUT_ERROR, "Missing audio files are rejected safely before API call.", "Validation handled correctly"),
        ("T083", "Numeric input", 123, INPUT_ERROR, "Numeric input is not accepted for speaker diarization.", "Validation handled correctly"),
        ("T084", "Valid base64 audio", audio_base64, expected_segments, "Base64 WAV audio is accepted directly and diarization succeeds.", "Working correctly"),
        ("T085", "Corrupted wav file", str(corrupted_audio_file), INPUT_ERROR, "Corrupted audio is rejected during WAV validation.", "Validation handled correctly"),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason, remark in cases:
        service = SpeakerDiarizationService(handler=None)
        if expected_output != INPUT_ERROR:
            service.handler = type(
                "Handler",
                (),
                {
                    "post": lambda self, payload: {
                        "pipelineResponse": [
                            {
                                "output": [
                                    {
                                        "speaker_labels": [
                                            {"speaker1": [{"start_time": 0.0, "duration": 1.25}]},
                                            {"speaker2": [{"start_time": 1.25, "duration": 0.75}]},
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                },
            )()
        actual_output = service.diarize(input_value)
        log_test_result(
            test_id,
            "Speaker Diarization",
            input_value,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark=remark,
        )
        assert_service_output(actual_output, expected_output)


def test_speaker_diarization_optional_preprocessors(tmp_path):
    captured = {}
    audio_file = tmp_path / "sample.wav"
    _create_wav_file(audio_file, (b"\x01\x00" * 1600))

    class Handler:
        def post(self, payload):
            captured["payload"] = payload
            return {
                "pipelineResponse": [
                    {
                        "output": [
                            {
                                "speaker_labels": [
                                    {"speaker1": [{"start_time": 0.0, "duration": 2.0}]}
                                ]
                            }
                        ]
                    }
                ]
            }

    service = SpeakerDiarizationService(Handler())
    actual_output = service.diarize(
        str(audio_file),
        service_id="bhashini/iisc/speaker-diarization",
        pre_processors=["vad", "denoiser"],
    )
    config = captured["payload"]["pipelineTasks"][0]["config"]
    expected_output = [{"speaker": "speaker1", "timestamps": [{"start_time": 0.0, "duration": 2.0}]}]
    log_test_result(
        "T086",
        "Speaker Diarization",
        str(audio_file),
        expected_output,
        actual_output,
        test_case_name="Optional preprocessors",
        logic_reason="Speaker diarization payload includes the selected service id and supported preprocessors.",
        remark="Optional parameters working correctly",
    )
    assert actual_output == expected_output
    assert config["serviceId"] == "bhashini/iisc/speaker-diarization"
    assert config["preProcessors"] == ["vad", "denoiser"]
