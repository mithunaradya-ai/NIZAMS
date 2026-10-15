import base64
import wave

from bhashini_client.services.voice_cloning_service import VoiceCloningService

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def _create_wav_file(path, frames, sample_rate=16000):
    with wave.open(str(path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(sample_rate)
        audio_file.writeframes(frames)


def test_voice_cloning_cases(tmp_path):
    ref_audio_file = tmp_path / "reference.wav"
    _create_wav_file(ref_audio_file, (b"\x01\x00" * 3200))
    corrupted_audio_file = tmp_path / "corrupted.wav"
    corrupted_audio_file.write_bytes(b"")
    ref_audio_base64 = base64.b64encode(ref_audio_file.read_bytes()).decode("utf-8")
    output_file = tmp_path / "voice_clone_output.wav"
    cloned_audio_base64 = base64.b64encode(b"generated-audio-bytes").decode("utf-8")

    cases = [
        ("T105", "Normal voice cloning", str(ref_audio_file), str(output_file), "Valid text, refText, and reference audio generate a cloned audio file.", "Working correctly"),
        ("T106", "Empty text", "", INPUT_ERROR, "Empty source text is rejected.", "Validation handled correctly"),
        ("T107", "Whitespace text", "   ", INPUT_ERROR, "Whitespace source text is rejected.", "Validation handled correctly"),
        ("T108", "Invalid ref audio type", 123, INPUT_ERROR, "Invalid reference audio type is rejected.", "Validation handled correctly"),
        ("T109", "Valid base64 ref audio", ref_audio_base64, str(output_file), "Base64 reference audio is accepted.", "Working correctly"),
        ("T110", "Invalid file path", str(tmp_path / "missing.wav"), INPUT_ERROR, "Invalid reference audio path is rejected.", "Validation handled correctly"),
        ("T111", "Empty ref audio file", str(corrupted_audio_file), INPUT_ERROR, "Empty reference audio file is rejected.", "Validation handled correctly"),
    ]

    for test_id, test_case_name, ref_audio_input, expected_output, logic_reason, remark in cases:
        service = VoiceCloningService(handler=None)
        if output_file.exists():
            output_file.unlink()
        if expected_output != INPUT_ERROR:
            service.handler = type(
                "Handler",
                (),
                {"post": lambda self, payload, url=None, headers=None: {"audio": [{"audioContent": cloned_audio_base64}]}},
            )()
        actual_output = service.clone_voice(
            "ఒక విషయం మీరు బహుశా ఎక్కువగా ఇష్టపడతారు.",
            "मुझे लगता है कि ए आई डेवलपमेंट एक कॉरपोरेशन है।",
            ref_audio_input,
            source_lang="te",
            output_file=str(output_file),
        )
        log_test_result(
            test_id,
            "Voice Cloning",
            ref_audio_input,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark=remark,
        )
        assert_service_output(actual_output, expected_output)


def test_voice_cloning_payload_and_headers(tmp_path):
    captured = {}
    ref_audio_file = tmp_path / "reference.wav"
    _create_wav_file(ref_audio_file, (b"\x01\x00" * 3200))
    output_file = tmp_path / "voice_clone_output.wav"
    generated_audio = base64.b64encode(b"generated-audio").decode("utf-8")

    class Handler:
        def post(self, payload, url=None, headers=None):
            captured["payload"] = payload
            captured["url"] = url
            captured["headers"] = headers
            return {"audio": [{"audioContent": generated_audio}]}

    service = VoiceCloningService(Handler())
    actual_output = service.clone_voice(
        "ఒక విషయం మీరు బహుశా ఎక్కువగా ఇష్టపడతారు.",
        "मुझे लगता है कि ए आई डेवलपमेंट एक कॉरपोरेशन है।",
        str(ref_audio_file),
        source_lang="te",
        output_file=str(output_file),
    )
    log_test_result(
        "T112",
        "Voice Cloning",
        str(ref_audio_file),
        str(output_file),
        actual_output,
        test_case_name="Payload structure",
        logic_reason="Voice cloning payload preserves the cURL endpoint, service id, language config, and x-auth-source header.",
        remark="Payload working correctly",
    )
    assert actual_output == str(output_file)
    assert captured["url"] == "https://dhruva-api.bhashini.gov.in/services/inference/tts/voice-cloning"
    assert captured["payload"]["config"]["serviceId"] == "bhashini/ai4b/indicf5-tts"
    assert captured["payload"]["config"]["language"]["sourceLanguage"] == "te"
    assert captured["headers"]["x-auth-source"] == "API_KEY"
