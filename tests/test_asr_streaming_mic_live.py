import argparse
import asyncio
import json

from bhashini_client.services.asr_streaming_client import (
    ASRStreamingClient,
    VADProcessor,
    int16_pcm_to_float32_bytes,
)


async def run_mic_stream(args):
    try:
        import pyaudio
        import websockets
    except ImportError as exc:
        missing = getattr(exc, "name", None) or str(exc)
        print(f"Missing dependency: {missing}")
        print("Install microphone dependencies first, for example: python -m pip install pyaudio websockets")
        return

    streaming_client = ASRStreamingClient(source_lang=args.lang, chunk_duration_ms=args.chunk_ms)
    websocket_url = streaming_client.get_websocket_url()
    if isinstance(websocket_url, str) and websocket_url.startswith("Input Error:"):
        print(websocket_url)
        return

    start_config = streaming_client.get_start_config(
        source_lang=args.lang,
        post_processors=[] if args.no_postprocessors else ["itn", "punctuation"],
    )
    if isinstance(start_config, str) and start_config.startswith("Input Error:"):
        print(start_config)
        return

    samples_per_chunk = int(streaming_client.sample_rate * args.chunk_ms / 1000)
    vad = VADProcessor(chunk_duration_ms=args.chunk_ms) if args.vad else None
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=streaming_client.sample_rate,
        input=True,
        frames_per_buffer=samples_per_chunk,    )

    chunks_sent = 0
    stop_event = asyncio.Event()

    print("MIC_STREAMING_STARTED")
    print("Speak now. Press Ctrl+C to stop.")

    async def receive_messages(websocket):
        nonlocal stop_event
        async for message in websocket:
            response = json.loads(message)
            if response.get("type") == "ready":
                print(f"READY session={response.get('sessionId')} model={response.get('modelName')}")
            elif response.get("type") == "transcript":
                text = (response.get("output") or [{}])[0].get("source", "")
                label = "FINAL" if response.get("isFinal") else "INTERIM"
                print(f"{label}: {text}")
                if response.get("isFinal"):
                    stop_event.set()
            elif response.get("type") == "error":
                print("ERROR:")
                print(response.get("message") or response)
                stop_event.set()
            elif response.get("type") == "end":
                print("END")
                stop_event.set()

    try:
        async with websockets.connect(websocket_url) as websocket:
            await websocket.send(json.dumps(start_config))
            receiver_task = asyncio.create_task(receive_messages(websocket))
            while not stop_event.is_set():
                chunk = stream.read(samples_per_chunk, exception_on_overflow=False)
                if vad:
                    state = vad.process_chunk(chunk)
                    if state not in {"START", "CONTINUE"}:
                        await asyncio.sleep(args.chunk_ms / 1000)
                        continue
                await websocket.send(int16_pcm_to_float32_bytes(chunk))
                await asyncio.sleep(args.chunk_ms / 1000)
                chunks_sent += 1
                if args.max_seconds and chunks_sent * args.chunk_ms >= args.max_seconds * 1000:
                    stop_event.set()
            try:
                await websocket.send(json.dumps({"type": "end"}))
            except Exception:
                pass
            try:
                await asyncio.wait_for(receiver_task, timeout=args.timeout)
            except asyncio.TimeoutError:
                receiver_task.cancel()
    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        print(f"MIC_CHUNKS_SENT: {chunks_sent}")


def main():
    parser = argparse.ArgumentParser(description="Live microphone ASR streaming demo.")
    parser.add_argument("--lang", default="hi", help="ASR source language code. Default: hi")
    parser.add_argument("--chunk-ms", type=int, default=200, help="Chunk duration in milliseconds. Default: 200")
    parser.add_argument("--timeout", type=int, default=10, help="Wait time for final backend messages. Default: 10")
    parser.add_argument("--max-seconds", type=int, default=8, help="Maximum seconds to record. Default: 8")
    parser.add_argument("--vad", action="store_true", help="Send only speech chunks using VAD.")
    parser.add_argument("--no-postprocessors", action="store_true", help="Disable ITN/punctuation postprocessors.")
    args = parser.parse_args()
    asyncio.run(run_mic_stream(args))


if __name__ == "__main__":
    main()
