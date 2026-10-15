import argparse
import audioop
import json
import wave

from bhashini_client import BhashiniClient
from bhashini_client.services.asr_streaming_client import VADProcessor


def wav_chunks(path, *, sample_rate=16000, chunk_ms=200, vad=False):
    with wave.open(path, "rb") as audio:
        channels = audio.getnchannels()
        sample_width = audio.getsampwidth()
        frame_rate = audio.getframerate()
        audio_bytes = audio.readframes(audio.getnframes())
        if channels == 2:
            audio_bytes = audioop.tomono(audio_bytes, sample_width, 0.5, 0.5)
            channels = 1
        if channels != 1:
            raise ValueError(f"Streaming ASR expects mono or stereo audio, but received {channels} channels.")
        if sample_width != 2:
            audio_bytes = audioop.lin2lin(audio_bytes, sample_width, 2)
            sample_width = 2
        if frame_rate != sample_rate:
            print(f"AUDIO_RESAMPLE: received {frame_rate} Hz, converting to {sample_rate} Hz for ASR streaming.")
            audio_bytes, _ = audioop.ratecv(audio_bytes, sample_width, channels, frame_rate, sample_rate, None)
        frames_per_chunk = int(sample_rate * chunk_ms / 1000)
        bytes_per_chunk = frames_per_chunk * sample_width
        vad_processor = VADProcessor(chunk_duration_ms=chunk_ms) if vad else None
        for index in range(0, len(audio_bytes), bytes_per_chunk):
            chunk = audio_bytes[index:index + bytes_per_chunk]
            if vad_processor:
                state = vad_processor.process_chunk(chunk)
                if state not in {"START", "CONTINUE"}:
                    continue
            yield chunk


def main():
    parser = argparse.ArgumentParser(description="Run a real ASR streaming test with a local WAV file.")
    parser.add_argument("--audio", required=True, help="Path to a 16 kHz mono 16-bit PCM WAV file.")
    parser.add_argument("--lang", default="hi", help="ASR source language code. Default: hi")
    parser.add_argument("--chunk-ms", type=int, default=200, help="Chunk duration in milliseconds. Default: 200")
    parser.add_argument("--timeout", type=int, default=10, help="Receive timeout after sending audio. Default: 10")
    parser.add_argument("--details", action="store_true", help="Print raw backend messages along with the final transcript.")
    parser.add_argument("--vad", action="store_true", help="Send only speech chunks using the same VAD style as the mentor script.")
    parser.add_argument("--service-id", default=None, help="Optional ASR streaming service id override.")
    parser.add_argument("--no-postprocessors", action="store_true", help="Send streaming audio without ITN/punctuation postprocessors.")
    parser.add_argument("--audio-sample-format", default="int16", choices=["int16", "float32", "raw"], help="Input chunk format before SDK sends it. Default converts int16 WAV chunks to mentor-compatible float32 stream bytes.")
    args = parser.parse_args()

    client = BhashiniClient()
    chunks = list(wav_chunks(args.audio, chunk_ms=args.chunk_ms, vad=args.vad))
    print(f"STREAMING_CHUNKS_SENT: {len(chunks)}")
    result = client.asr_stream_sync(
        chunks,
        args.lang,
        service_id=args.service_id,
        post_processors=[] if args.no_postprocessors else ["itn", "punctuation"],
        receive_timeout=args.timeout,
        chunk_delay_seconds=args.chunk_ms / 1000.0,
        return_details=args.details,
        audio_sample_format=args.audio_sample_format,
    )
    print("ASR_STREAMING_RESULT:")
    if isinstance(result, (dict, list)):
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result)


if __name__ == "__main__":
    main()
