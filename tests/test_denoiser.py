import base64
import wave

from bhashini_client.services.denoiser_service import DenoiserService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def _create_wav_file(path, frames, sample_rate=16000):
    with wave.open(str(path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(sample_rate)
        audio_file.writeframes(frames)


def test_denoiser_cases(tmp_path):
    valid_audio_file = tmp_path / "sample.wav"
    corrupted_audio_file = tmp_path / "corrupted.wav"
    output_file = tmp_path / "denoised_output.wav"
    _create_wav_file(valid_audio_file, (b"\x01\x00" * 1600))
    corrupted_audio_file.write_bytes(b"not-a-valid-wave-file")
    audio_base64 = base64.b64encode(valid_audio_file.read_bytes()).decode("utf-8")
    cleaned_audio = base64.b64encode(b"cleaned-audio").decode("utf-8")

    cases = [
        ("T135", "Normal audio file", str(valid_audio_file), str(output_file), "Valid WAV audio is denoised into an output audio file.", "Working correctly"),
        ("T136", "Empty string", "", INPUT_ERROR, "Empty audio is rejected.", "Validation handled correctly"),
        ("T137", "Whitespace string", "   ", INPUT_ERROR, "Whitespace audio is rejected.", "Validation handled correctly"),
        ("T138", "Invalid file path", str(tmp_path / "missing.wav"), INPUT_ERROR, "Missing file path is rejected.", "Validation handled correctly"),
        ("T139", "Numeric input", 123, INPUT_ERROR, "Numeric input is not valid audio input.", "Validation handled correctly"),
        ("T140", "Valid base64 audio", audio_base64, str(output_file), "Base64 audio is accepted for denoising.", "Working correctly"),
        ("T141", "Corrupted wav file", str(corrupted_audio_file), INPUT_ERROR, "Corrupted audio is rejected before API call.", "Validation handled correctly"),
        ("T142", "Audio URI", "https://example.com/noisy.wav", str(output_file), "Audio URI is accepted for denoising.", "Working correctly"),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason, remark in cases:
        service = DenoiserService(handler=None)
        if output_file.exists():
            output_file.unlink()
        if expected_output != INPUT_ERROR:
            service.handler = type(
                "Handler",
                (),
                {"post": lambda self, payload, url=None, headers=None: {"audio": [{"audioContent": cleaned_audio}]}},
            )()
        actual_output = service.denoise(input_value, output_file=str(output_file))
        log_test_result(
            test_id,
            "Denoiser",
            input_value,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark=remark,
        )
        assert_service_output(actual_output, expected_output)


def test_denoiser_payload():
    captured = {}

    class Handler:
        def post(self, payload, url=None, headers=None):
            captured["payload"] = payload
            captured["url"] = url
            return {"audio": [{"audioUri": "https://example.com/denoised.wav"}]}

    service = DenoiserService(Handler())
    actual_output = service.denoise("https://example.com/noisy.wav")
    log_test_result(
        "T143",
        "Denoiser",
        "https://example.com/noisy.wav",
        "https://example.com/denoised.wav",
        actual_output,
        test_case_name="Payload structure",
        logic_reason="Denoiser payload preserves the cURL endpoint and service id while accepting audioUri input.",
        remark="Payload working correctly",
    )
    assert actual_output == "https://example.com/denoised.wav"
    assert captured["url"] == "https://dhruva-api.bhashini.gov.in/services/inference/denoiser"
    assert captured["payload"]["config"]["serviceId"] == "bhashini/facebook/denoiser--gpu-t4"
