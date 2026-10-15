import asyncio
import os
import queue
import threading

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pywebrtc_audio import AudioProcessor

# ==================================================
# CONFIGURATION
# ==================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3.8-live"

MICROPHONE_DEVICE = 1
INPUT_RATE = 16000
OUTPUT_RATE = 24000
BLOCK_SIZE = 640

if not API_KEY:
    raise SystemExit(
        "GEMINI_API_KEY was not found. Check your .env file."
    )

client = genai.Client(api_key=API_KEY)


# ==================================================
# GEMINI LIVE SETTINGS
# ==================================================

LIVE_CONFIG = {
    "response_modalities": ["AUDIO"],
    "input_audio_transcription": {},
    "output_audio_transcription": {},
  
    "system_instruction": (
        
        "You are a helpful and intelligent farmer-assistance "
        "voice assistant. Speak naturally and respectfully. "
        "Use the language the farmer speaks, whenever supported. "
        "Keep normal answers brief, usually 1 to 3 sentences. "
        "Explain in detail when the farmer requests it. "
        "Remember the conversation and understand follow-up "
        "questions. Allow the farmer to change topics naturally. "
        "Avoid robotic greetings, repetition, and unnecessary "
        "lists. Never invent government scheme requirements "
        "or claim to have checked a database that is not connected. "
        "When essential information is missing, ask one short "
        "clarifying question."
        "system_instruction"
    "You are a multilingual farmer-assistance voice assistant. "
    "Always reply in the same language the farmer is speaking. "
    "Support Tamil, Hindi, English"
     "If the farmer switches languages, switch with them. "
    "Never default to English when the farmer speaks another language. "
    "Keep normal answers brief and natural. Give detailed explanations "
    "only when requested. Remember the conversation and answer "
    "follow-up questions in context. Never invent government scheme rules. "
    "Ask a short clarifying question when essential information is missing."
    ),
}


# ==================================================
# MAIN VOICE ASSISTANT
# ==================================================

async def main():
    loop = asyncio.get_running_loop()

    microphone_queue = asyncio.Queue(maxsize=10)
    speaker_queue = queue.Queue(maxsize=150)

    flush_speaker = threading.Event()

    playback_buffer = np.empty((0, 1), dtype=np.int16)
    audio_processor = AudioProcessor(
    sample_rate=INPUT_RATE,
    num_channels=1,
    noise_suppression=True,
    high_pass_filter=True,
    auto_gain_control=True,
    ns_level=1,
)

    input_text_parts = []
    output_text_parts = []

    # ----------------------------------------------
    # MICROPHONE QUEUE
    # ----------------------------------------------

    def enqueue_microphone(audio_bytes):
        while microphone_queue.full():
            try:
                microphone_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        try:
            microphone_queue.put_nowait(audio_bytes)
        except asyncio.QueueFull:
            pass

    # ----------------------------------------------
    # MICROPHONE CALLBACK
    # ----------------------------------------------

    def microphone_callback(
        indata,
        frames,
        time_info,
        status,
    ):
        if status:
            print(f"\nMicrophone status: {status}")

        try:
            # Get microphone audio as a NumPy array.
            raw_audio = indata[:, 0].copy()

            # Reduce background noise and improve voice clarity.
            clean_audio = audio_processor.process(raw_audio)

            audio_bytes = clean_audio.tobytes()

        except Exception as error:
            print(f"\nAudio processing error: {error}")

            # Use original audio if processing fails.
            audio_bytes = indata.copy().tobytes()

        # Send processed audio to Gemini Live.
        loop.call_soon_threadsafe(
            enqueue_microphone,
            audio_bytes,
        )

    # ----------------------------------------------
    # SPEAKER CALLBACK
    # ----------------------------------------------

    def speaker_callback(
        outdata,
        frames,
        time_info,
        status,
    ):
        nonlocal playback_buffer

        outdata.fill(0)

        # Clear audio when Gemini reports an interruption.
        if flush_speaker.is_set():
            playback_buffer = np.empty(
                (0, 1),
                dtype=np.int16,
            )

            while True:
                try:
                    speaker_queue.get_nowait()
                except queue.Empty:
                    break

            flush_speaker.clear()

        position = 0

        while position < frames:

            if len(playback_buffer) == 0:
                try:
                    audio_chunk = speaker_queue.get_nowait()
                except queue.Empty:
                    break

                playback_buffer = np.frombuffer(
                    audio_chunk,
                    dtype=np.int16,
                ).reshape(-1, 1)

            count = min(
                frames - position,
                len(playback_buffer),
            )

            outdata[position:position + count] = (
                playback_buffer[:count]
            )

            playback_buffer = playback_buffer[count:]
            position += count

    # ----------------------------------------------
    # SEND MICROPHONE AUDIO TO GEMINI
    # ----------------------------------------------

    async def send_microphone_audio(session):
        while True:
            audio_bytes = await microphone_queue.get()

            await session.send_realtime_input(
                audio=types.Blob(
                    data=audio_bytes,
                    mime_type="audio/pcm;rate=16000",
                )
            )

    # ----------------------------------------------
    # RECEIVE GEMINI RESPONSES
    # ----------------------------------------------

    
    async def receive_gemini_response(session):
        while True:
            async for response in session.receive():
                content = response.server_content

                if content is None:
                    continue

                if getattr(content, "interrupted", False):
                    flush_speaker.set()
                    print(
                        "\n[Interruption detected. "
                        "Stopping the assistant's speech.]",
                        flush=True,
                    )

                input_transcript = getattr(
                    content, "input_transcription", None
                )

                if input_transcript and input_transcript.text:
                    input_text_parts.append(input_transcript.text)

                output_transcript = getattr(
                    content, "output_transcription", None
                )

                if output_transcript and output_transcript.text:
                    output_text_parts.append(output_transcript.text)

                if content.model_turn:
                    for part in content.model_turn.parts:
                        if part.inline_data and part.inline_data.data:
                            try:
                                speaker_queue.put_nowait(
                                    part.inline_data.data
                                )
                            except queue.Full:
                                print(
                                    "\n[Audio queue full; "
                                    "some audio was skipped.]"
                                )

                if content.turn_complete:
                    farmer_text = "".join(input_text_parts).strip()
                    assistant_text = "".join(output_text_parts).strip()

                    if farmer_text:
                        print(f"\nFarmer: {farmer_text}", flush=True)

                    if assistant_text:
                        print(f"\nFarmer AI: {assistant_text}", flush=True)

                    input_text_parts.clear()
                    output_text_parts.clear()

                    print(
                        "\n[Listening for the next question...]",
                        flush=True,
                    )

            # Start a fresh receive iterator for the next turn.
            await asyncio.sleep(0.01)

        # ==================================================
    # START AUDIO DEVICES AND SESSION WITH RECONNECTION
    # ==================================================

    print("Opening microphone and speaker...")
    print("Please wear headphones to reduce feedback.")

    retry_delay = 2
    max_retry_delay = 30
    consecutive_failures = 0
    max_failures = 5

    try:
        with sd.InputStream(
            device=MICROPHONE_DEVICE,
            samplerate=INPUT_RATE,
            channels=1,
            dtype="int16",
            blocksize=BLOCK_SIZE,
            callback=microphone_callback,
        ):
            with sd.OutputStream(
                samplerate=OUTPUT_RATE,
                channels=1,
                dtype="int16",
                callback=speaker_callback,
            ):
                while True:
                    try:
                        print("\nConnecting to Gemini Live...")

                        # Remove old audio left over from a disconnect.
                        flush_speaker.set()

                        while not microphone_queue.empty():
                            try:
                                microphone_queue.get_nowait()
                            except asyncio.QueueEmpty:
                                break

                        async with client.aio.live.connect(
                            model=MODEL,
                            config=LIVE_CONFIG,
                        ) as session:

                            print("\nConnected! Start speaking.")
                            print("Ask questions naturally.")
                            print("Press Ctrl+C to exit.\n")

                            sender = asyncio.create_task(
                                send_microphone_audio(session)
                            )

                            receiver = asyncio.create_task(
                                receive_gemini_response(session)
                            )

                            try:
                                done, pending = await asyncio.wait(
                                    {sender, receiver},
                                    return_when=asyncio.FIRST_COMPLETED,
                                )

                                for task in pending:
                                    task.cancel()

                                await asyncio.gather(
                                    *pending,
                                    return_exceptions=True,
                                )

                                for task in done:
                                    if task.cancelled():
                                        continue

                                    error = task.exception()
                                    if error:
                                        raise error

                                raise ConnectionError(
                                    "Gemini Live session ended unexpectedly."
                                )

                            finally:
                                for task in (sender, receiver):
                                    if not task.done():
                                        task.cancel()

                                await asyncio.gather(
                                    sender,
                                    receiver,
                                    return_exceptions=True,
                                )

                    except asyncio.CancelledError:
                        raise

                    except Exception as error:
                        consecutive_failures += 1
                        flush_speaker.set()

                        print(
                            f"\nGemini connection lost: "
                            f"{type(error).__name__}: {error}"
                        )

                        if consecutive_failures >= max_failures:
                            print(
                                "\nStopped after 5 consecutive failures. "
                                "Check your internet, API key, and quota "
                                "before running the program again."
                            )
                            break

                        print(
                            f"Retrying in {retry_delay} seconds "
                            f"(attempt {consecutive_failures} "
                            f"of {max_failures})..."
                        )

                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, max_retry_delay)

    except KeyboardInterrupt:
        print("\nVoice assistant stopped.")

    finally:
        try:
            client.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye.")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye.")