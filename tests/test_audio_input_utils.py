import base64
import io
import wave

from bhashini_client.services.audio_input_utils import convert_audio_file_to_base64, preprocess_audio_input


def _create_wav_file(path, frames, sample_rate=16000):
    with wave.open(str(path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(sample_rate)
        audio_file.writeframes(frames)


def test_convert_audio_file_to_base64_from_local_wav(tmp_path):
    audio_file = tmp_path / "sample.wav"
    _create_wav_file(audio_file, (b"\x01\x00" * 1600))

    result = convert_audio_file_to_base64(str(audio_file))

    assert result["inputPath"] == str(audio_file)
    assert result["message"].startswith("The provided local audio file was not base64.")
    assert base64.b64decode(result["audioContent"])


def test_convert_audio_file_to_base64_rejects_empty_file(tmp_path):
    audio_file = tmp_path / "empty.wav"
    audio_file.write_bytes(b"")

    result = convert_audio_file_to_base64(str(audio_file))

    assert isinstance(result, str)
    assert result.startswith("Input Error:")


def test_preprocess_audio_input_resamples_non_16000_wav(tmp_path):
    audio_file = tmp_path / "resample.wav"
    _create_wav_file(audio_file, (b"\x01\x00" * 3200), sample_rate=48000)

    result = preprocess_audio_input(
        str(audio_file),
        require_wav=True,
        sampling_rate=16000,
        require_speech=True,
    )

    assert result["samplingRate"] == 16000
    assert result["metadata"]["original_sampling_rate"] == 48000
    assert result["metadata"]["sampling_rate"] == 16000
    assert result["metadata"]["was_resampled"] is True
    assert "converted to 16000 Hz" in result["message"]
    decoded_audio = base64.b64decode(result["audioContent"])
    with wave.open(io.BytesIO(decoded_audio), "rb") as audio_stream:
        assert audio_stream.getframerate() == 16000
