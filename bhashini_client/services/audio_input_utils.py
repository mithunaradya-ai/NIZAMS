import audioop
import base64
import io
import os
import wave

from .service_utils import input_error


def convert_audio_file_to_base64(file_path):
    if not isinstance(file_path, str):
        return input_error("Audio file path must be provided as a string.")

    cleaned_path = file_path.strip()
    if not cleaned_path:
        return input_error("Audio file path is empty. Please provide a valid WAV file path.")

    if not os.path.isfile(cleaned_path):
        return input_error("The provided audio file path does not exist.")

    if os.path.getsize(cleaned_path) == 0:
        return input_error("The audio file is empty. Please provide a file that contains audio data.")

    with open(cleaned_path, "rb") as audio_file:
        encoded_audio = base64.b64encode(audio_file.read()).decode("utf-8")

    return {
        "audioContent": encoded_audio,
        "message": "The provided local audio file was not base64. It has been converted to base64.",
        "inputPath": cleaned_path,
    }


def preprocess_audio_input(
    input_data,
    *,
    require_wav=True,
    sampling_rate=16000,
    require_mono=False,
    min_duration_seconds=None,
    require_speech=False,
):
    if input_data is None:
        return input_error(
            "Audio input is missing. Please provide a WAV file path, base64 audio, or raw audio bytes."
        )

    if isinstance(input_data, bytes):
        if not input_data:
            return input_error("Audio bytes are empty. Please provide a non-empty audio payload.")
        return _build_audio_payload(
            input_data,
            audio_format="wav",
            sampling_rate=sampling_rate,
            require_wav=require_wav,
            require_mono=require_mono,
            min_duration_seconds=min_duration_seconds,
            require_speech=require_speech,
        )

    if not isinstance(input_data, str):
        return input_error(
            "Audio input type is invalid. Please provide a file path, base64 string, or raw audio bytes."
        )

    cleaned_input = input_data.strip()
    if not cleaned_input:
        return input_error("Audio input is empty. Please provide a valid audio file or base64 audio.")

    if os.path.isfile(cleaned_input):
        if require_wav and not cleaned_input.lower().endswith(".wav"):
            return input_error("Only WAV audio files are supported for this service.")
        if os.path.getsize(cleaned_input) == 0:
            return input_error("The audio file is empty. Please provide a file that contains audio data.")
        with open(cleaned_input, "rb") as audio_file:
            return _build_audio_payload(
                audio_file.read(),
                audio_format="wav",
                sampling_rate=sampling_rate,
                require_wav=require_wav,
                require_mono=require_mono,
                min_duration_seconds=min_duration_seconds,
                require_speech=require_speech,
            )

    try:
        decoded_audio = base64.b64decode(cleaned_input, validate=True)
    except Exception:
        return input_error(
            "Audio input is neither a valid file path nor a valid base64-encoded audio string."
        )

    return _build_audio_payload(
        decoded_audio,
        audio_format="wav",
        sampling_rate=sampling_rate,
        require_wav=require_wav,
        require_mono=require_mono,
        min_duration_seconds=min_duration_seconds,
        require_speech=require_speech,
        original_base64=cleaned_input,
    )


def preprocess_audio_or_uri_input(
    input_data,
    *,
    require_wav=True,
    sampling_rate=16000,
    require_mono=False,
    min_duration_seconds=None,
    require_speech=False,
):
    if input_data is None or not isinstance(input_data, str):
        return input_error(
            "Audio input is missing. Please provide a WAV file path, base64 audio, or a supported audio URI."
        )

    cleaned_input = input_data.strip()
    if not cleaned_input:
        return input_error("Audio input is empty. Please provide a valid audio file, URI, or base64 audio.")

    if _looks_like_uri(cleaned_input):
        return {"audioUri": cleaned_input}

    return preprocess_audio_input(
        cleaned_input,
        require_wav=require_wav,
        sampling_rate=sampling_rate,
        require_mono=require_mono,
        min_duration_seconds=min_duration_seconds,
        require_speech=require_speech,
    )


def _build_audio_payload(
    audio_bytes,
    *,
    audio_format,
    sampling_rate,
    require_wav,
    require_mono,
    min_duration_seconds,
    require_speech,
    original_base64=None,
):
    if not audio_bytes:
        return input_error("Audio content is empty. Please provide audio with audible speech.")

    audio_preparation = _inspect_and_prepare_wav(
        audio_bytes,
        expected_sampling_rate=sampling_rate,
        require_wav=require_wav,
        require_mono=require_mono,
        min_duration_seconds=min_duration_seconds,
        require_speech=require_speech,
    )
    if isinstance(audio_preparation, str):
        return audio_preparation

    normalized_audio_bytes = audio_preparation["audio_bytes"]
    audio_metadata = audio_preparation["metadata"]
    message = audio_preparation.get("message")

    payload = {
        "audioContent": base64.b64encode(normalized_audio_bytes).decode("utf-8")
        if original_base64 is None or message
        else original_base64,
        "audioFormat": audio_format,
        "samplingRate": sampling_rate,
        "metadata": audio_metadata,
    }
    if message:
        payload["message"] = message
    return payload


def _inspect_and_prepare_wav(
    audio_bytes,
    *,
    expected_sampling_rate,
    require_wav,
    require_mono,
    min_duration_seconds,
    require_speech,
):
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as audio_stream:
            frame_count = audio_stream.getnframes()
            channels = audio_stream.getnchannels()
            sample_width = audio_stream.getsampwidth()
            frame_rate = audio_stream.getframerate() 
            if frame_count == 0:
                return input_error(
                    "The audio file does not contain any frames. Please provide an audio file with speech."
                )
            if require_mono and channels != 1:
                return input_error(
                    f"This service expects mono audio with 1 channel, but received {channels} channels."
                )
            duration_seconds = frame_count / float(frame_rate)
            if min_duration_seconds is not None and duration_seconds < min_duration_seconds:
                return input_error(
                    f"Minimum audio duration for this service is {min_duration_seconds:.0f} seconds, but received {duration_seconds:.2f} seconds."
                )
            frame_bytes = audio_stream.readframes(frame_count)
            if require_speech and not _contains_speech(frame_bytes, sample_width):
                return input_error(
                    "No speech was detected in the provided audio. Please provide audio with clear spoken content."
                )
            normalized_audio_bytes = audio_bytes
            normalized_rate = frame_rate
            message = None
            was_resampled = False

            if expected_sampling_rate is not None and frame_rate != expected_sampling_rate:
                converted_frames, _state = audioop.ratecv(
                    frame_bytes,
                    sample_width,
                    channels,
                    frame_rate,
                    expected_sampling_rate,
                    None,
                )
                normalized_audio_bytes = _encode_wav_bytes(
                    converted_frames,
                    channels=channels,
                    sample_width=sample_width,
                    sampling_rate=expected_sampling_rate,
                )
                normalized_rate = expected_sampling_rate
                was_resampled = True
                message = (
                    f"Input audio was {frame_rate} Hz. It has been converted to "
                    f"{expected_sampling_rate} Hz before sending it to the service."
                )

            return {
                "audio_bytes": normalized_audio_bytes,
                "metadata": {
                    "channels": channels,
                    "sample_width": sample_width,
                    "sampling_rate": normalized_rate,
                    "original_sampling_rate": frame_rate,
                    "duration_seconds": duration_seconds,
                    "was_resampled": was_resampled,
                },
                "message": message,
            }
    except wave.Error:
        if require_wav:
            return input_error(
                "The audio content is not a valid WAV file. Please provide a readable WAV file encoded at the expected format."
            )
        return input_error("The provided audio content could not be parsed.")
    except Exception:
        return input_error("The provided audio content could not be parsed.")


def _contains_speech(frame_bytes, sample_width):
    if not frame_bytes:
        return False
    try:
        rms_value = audioop.rms(frame_bytes, sample_width)
        return rms_value > 0
    except Exception:
        return any(frame_bytes)


def _looks_like_uri(input_value):
    lowered = input_value.lower()
    return lowered.startswith("http://") or lowered.startswith("https://")


def _encode_wav_bytes(frame_bytes, *, channels, sample_width, sampling_rate):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio_stream:
        audio_stream.setnchannels(channels)
        audio_stream.setsampwidth(sample_width)
        audio_stream.setframerate(sampling_rate)
        audio_stream.writeframes(frame_bytes)
    return buffer.getvalue()
