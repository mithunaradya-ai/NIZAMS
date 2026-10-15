import base64
import wave

from bhashini_client.services.asr_service import ASRService
from bhashini_client.services.asr_streaming_client import ASRStreamingClient, int16_pcm_to_float32_bytes

from tests.assertions import INPUT_ERROR, assert_service_output
from tests.result_logger import log_test_result


def _create_wav_file(path, frames, sample_rate=16000):
    with wave.open(str(path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(sample_rate)
        audio_file.writeframes(frames)


def test_asr_service_cases(tmp_path):
    valid_audio_file = tmp_path / "sample.wav"
    silent_audio_file = tmp_path / "silent.wav"
    empty_audio_file = tmp_path / "empty.wav"
    corrupted_audio_file = tmp_path / "corrupted.wav"

    _create_wav_file(valid_audio_file, (b"\x01\x00" * 1600))
    _create_wav_file(silent_audio_file, (b"\x00\x00" * 1600))
    empty_audio_file.write_bytes(b"")
    corrupted_audio_file.write_bytes(b"not-a-valid-wave-file")

    audio_base64 = base64.b64encode(valid_audio_file.read_bytes()).decode("utf-8")

    cases = [
        ("T001", "Normal audio file", str(valid_audio_file), "demo transcription", "Valid Hindi WAV file is accepted, encoded, sent to ASR, and transcription text is returned.", "Working correctly"),
        ("T002", "Empty string", "", INPUT_ERROR, "Validation prevents empty API call.", "Validation handled correctly"),
        ("T003", "Whitespace string", "   ", INPUT_ERROR, "Whitespace is trimmed before processing and rejected when empty.", "Validation handled correctly"),
        ("T004", "Numeric input", 123, INPUT_ERROR, "Numeric input is not valid audio input.", "Validation handled correctly"),
        ("T005", "Valid base64 audio", audio_base64, "demo transcription", "Base64 audio is accepted directly and transcribed.", "Working correctly"),
        ("T006", "Invalid file path", str(tmp_path / "missing.wav"), INPUT_ERROR, "Invalid path is handled safely before API call.", "Validation handled correctly"),
        ("T007", "Silent audio", str(silent_audio_file), INPUT_ERROR, "Silent audio is rejected using a VAD-like check before processing.", "Validation handled correctly"),
        ("T008", "Corrupted wav file", str(corrupted_audio_file), INPUT_ERROR, "Corrupted audio file is rejected before API call.", "Validation handled correctly"),
        ("T009", "Empty audio file", str(empty_audio_file), INPUT_ERROR, "Empty file contains no audio content, so request is rejected.", "Validation handled correctly"),
        ("T009A", "Audio URI", "https://example.com/sample.wav", "demo transcription", "Audio URI input is forwarded directly into the ASR payload.", "Working correctly"),
    ]

    for test_id, test_case_name, input_value, expected_output, logic_reason, remark in cases:
        service = ASRService(handler=None)
        if expected_output != INPUT_ERROR:
            service.handler = type(
                "Handler",
                (),
                {"post": lambda self, payload: {"pipelineResponse": [{"output": [{"source": "demo transcription"}]}]}},
            )()
        actual_output = service.transcribe(input_value, "en")
        log_test_result(
            test_id,
            "ASR",
            input_value,
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark=remark,
        )
        assert_service_output(actual_output, expected_output)


def test_asr_payload_includes_optional_parameters(tmp_path):
    captured = {}
    audio_file = tmp_path / "sample.wav"
    _create_wav_file(audio_file, (b"\x01\x00" * 1600), sample_rate=16000)

    class Handler:
        def post(self, payload):
            captured["payload"] = payload
            return {"pipelineResponse": [{"output": [{"source": "demo transcription"}]}]}

    service = ASRService(Handler())
    actual_output = service.transcribe(
        str(audio_file),
        "hi",
        service_id="bhashini/ai4bharat/conformer-multilingual-asr",
        source_script_code="Deva",
        audio_format="wav",
        sampling_rate=16000,
        encoding="LINEAR16",
        domain="general",
        pre_processors=["vad", "denoiser"],
        post_processors=[{"hotword_list": ["पत्रिका", "रंगकर्म", "फिक्र"]}, "itn", "punctuation"],
    )
    config = captured["payload"]["pipelineTasks"][0]["config"]
    log_test_result(
        "T010",
        "ASR",
        "optional parameter payload",
        "demo transcription",
        actual_output,
        test_case_name="Optional parameters",
        logic_reason="Supported preprocessors and postprocessors are included in ASR payload and transcription still succeeds.",
        remark="Optional parameters working correctly",
    )
    assert actual_output == "demo transcription"
    assert config["serviceId"] == "bhashini/ai4bharat/conformer-multilingual-asr"
    assert config["language"]["sourceLanguage"] == "hi"
    assert config["language"]["sourceScriptCode"] == "Deva"
    assert config["audioFormat"] == "wav"
    assert config["samplingRate"] == 16000
    assert config["encoding"] == "LINEAR16"
    assert config["domain"] == "general"
    assert config["preProcessors"] == ["vad", "denoiser"]
    assert config["postProcessors"] == [{"hotword_list": ["पत्रिका", "रंगकर्म", "फिक्र"]}, "itn", "punctuation"]


def test_asr_rejects_invalid_optional_parameters(tmp_path):
    audio_file = tmp_path / "sample.wav"
    _create_wav_file(audio_file, (b"\x01\x00" * 1600))

    service = ASRService(handler=type("Handler", (), {"post": lambda self, payload: None})())

    cases = [
        ("T012", "Unsupported sampling rate", {"sampling_rate": 22050}, INPUT_ERROR, "Current ASR validation accepts only samplingRate 16000.", "Validation handled correctly"),
        ("T013", "Invalid preprocessor", {"pre_processors": ["invalid-pre"]}, INPUT_ERROR, "Only supported preprocessors like vad and denoiser are allowed.", "Validation handled correctly"),
        ("T014", "Invalid hotword config", {"post_processors": [{"hotword_list": []}]}, INPUT_ERROR, "Hotword config must be non-empty and valid for supported Hindi setup.", "Validation handled correctly"),
        ("T014A", "Unsupported local flac declaration", {"audio_format": "flac"}, INPUT_ERROR, "FLAC is supported only for URI-based ASR requests in the SDK.", "Validation handled correctly"),
    ]

    for test_id, test_case_name, kwargs, expected_output, logic_reason, remark in cases:
        actual_output = service.transcribe(str(audio_file), "hi", **kwargs)
        log_test_result(
            test_id,
            "ASR",
            str(kwargs),
            expected_output,
            actual_output,
            test_case_name=test_case_name,
            logic_reason=logic_reason,
            remark=remark,
        )
        assert_service_output(actual_output, expected_output)


def test_asr_uses_hindi_service_id():
    captured = {}
    import io

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(16000)
        audio_file.writeframes(b"\x01\x00" * 1600)
    audio_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    class Handler:
        def post(self, payload):
            captured["serviceId"] = payload["pipelineTasks"][0]["config"]["serviceId"]
            return {"pipelineResponse": [{"output": [{"source": "demo transcription"}]}]}

    service = ASRService(Handler())
    actual_output = service.transcribe(audio_base64, "hi")
    log_test_result(
        "T011",
        "ASR",
        "hi service id",
        "demo transcription",
        actual_output,
        test_case_name="Hindi service id",
        logic_reason="Explicit Hindi ASR service id works correctly.",
        remark="Working correctly",
    )
    assert actual_output == "demo transcription"
    assert captured["serviceId"] == "ai4bharat/conformer-hi-gpu--t4"


def test_asr_uri_payload_supports_flac():
    captured = {}

    class Handler:
        def post(self, payload):
            captured["payload"] = payload
            return {"pipelineResponse": [{"output": [{"source": "demo transcription"}]}]}

    service = ASRService(Handler())
    actual_output = service.transcribe(
        "https://example.com/sample.flac",
        "en",
        audio_format="flac",
        encoding="FLAC",
    )
    config = captured["payload"]["pipelineTasks"][0]["config"]
    audio_payload = captured["payload"]["inputData"]["audio"][0]
    assert actual_output == "demo transcription"
    assert config["audioFormat"] == "flac"
    assert config["encoding"] == "FLAC"
    assert audio_payload["audioUri"] == "https://example.com/sample.flac"


def test_asr_streaming_config_uses_existing_api_key_and_defaults():
    streaming_client = ASRStreamingClient(api_key="demo-key", source_lang="hi")

    websocket_url = streaming_client.get_websocket_url()
    start_config = streaming_client.get_start_config()

    assert websocket_url == "wss://dhruva-api.bhashini.gov.in/ws/v1/asr/stream?api_key=demo-key"
    assert start_config["type"] == "start"
    assert start_config["controlConfig"]["dataTracking"] is False
    assert start_config["config"]["serviceId"] == "bhashini/ai4b/indic-conformer/grpc"
    assert start_config["config"]["language"]["sourceLanguage"] == "hi"
    assert start_config["config"]["audioFormat"] == "pcm"
    assert start_config["config"]["encoding"] == "raw"
    assert start_config["config"]["samplingRate"] == 16000
    assert start_config["config"]["transcriptionFormat"] == {"value": "transcript"}
    assert start_config["config"]["profanityFilter"] is True
    assert start_config["config"]["postProcessors"] == ["itn", "punctuation"]
    assert start_config["streamingConfig"]["chunkDurationMs"] == 200
    assert start_config["streamingConfig"]["interimResults"] is True


def test_asr_streaming_path_is_explicit_and_does_not_call_http_handler():
    captured = {}

    class Handler:
        api_key = "demo-key"

        def post(self, payload):
            raise AssertionError("HTTP request-response path should not run for explicit streaming calls.")

    class FakeStreamingClient:
        async def transcribe_audio_chunks(self, audio_chunks, **kwargs):
            captured["chunks"] = list(audio_chunks)
            captured["kwargs"] = kwargs
            return "streaming transcription"

    service = ASRService(Handler())
    service._get_streaming_client = lambda **kwargs: FakeStreamingClient()

    actual_output = service.stream_transcribe_sync(
        [b"\x01\x00" * 160],
        "hi",
        post_processors=["itn"],
        receive_timeout=1,
        audio_sample_format="int16",
    )

    assert actual_output == "streaming transcription"
    assert captured["chunks"] == [b"\x01\x00" * 160]
    assert captured["kwargs"]["source_lang"] == "hi"
    assert captured["kwargs"]["post_processors"] == ["itn"]
    assert captured["kwargs"]["receive_timeout"] == 1
    assert captured["kwargs"]["audio_sample_format"] == "int16"


def test_asr_streaming_converts_int16_chunks_to_float32_wire_bytes():
    streaming_client = ASRStreamingClient(api_key="demo-key", source_lang="hi")
    converted = int16_pcm_to_float32_bytes(b"\x00\x00\x00@\x00\xc0")

    assert len(converted) == 12
