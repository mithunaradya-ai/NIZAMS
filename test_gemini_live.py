import asyncio
import os

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise SystemExit(
        "GEMINI_API_KEY was not found. Check your .env file."
    )

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.8-live"


async def main():
    print("Connecting to Gemini Live...")

    try:
        config = {
            "response_modalities": ["AUDIO"],
            "output_audio_transcription": {},
            "system_instruction": (
                "You are a friendly farmer-assistance voice assistant. "
                "Speak naturally, clearly, and briefly. "
                "Give a simple greeting to the farmer."
            ),
        }

        audio_chunks = []
        transcript_parts = []

        async with asyncio.timeout(60):
            async with client.aio.live.connect(
                model=MODEL,
                config=config,
            ) as session:

                print("Connected! Requesting a spoken answer...")

                await session.send_client_content(
                    turns={
                        "role": "user",
                        "parts": [
                            {
                                "text": (
                                    "Greet a farmer and ask how "
                                    "you can help today."
                                )
                            }
                        ],
                    },
                    turn_complete=True,
                )

                async for response in session.receive():
                    content = response.server_content

                    if not content:
                        continue

                    if content.output_transcription:
                        transcript = content.output_transcription.text
                        if transcript:
                            transcript_parts.append(transcript)

                    if content.model_turn:
                        for part in content.model_turn.parts:
                            if part.inline_data and part.inline_data.data:
                                audio_chunks.append(part.inline_data.data)

                    if content.turn_complete:
                        break

        print("\nGemini's response:")
        print("".join(transcript_parts) or "No transcript received.")

        if audio_chunks:
            audio_data = b"".join(audio_chunks)
            samples = np.frombuffer(audio_data, dtype=np.int16)

            print("\nPlaying Gemini's voice...")
            sd.play(samples, samplerate=24000)
            sd.wait()

            print("Voice test completed successfully.")
        else:
            print("No audio received. Check the API response.")

    except TimeoutError:
        print("Timed out. Check your internet connection and retry.")

    except Exception as error:
        print(f"Gemini Live test failed: {type(error).__name__}: {error}")


if __name__ == "__main__":
    asyncio.run(main())