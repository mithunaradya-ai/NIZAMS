
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import ollama

# Settings
MICROPHONE_DEVICE = 1
SAMPLE_RATE = 16000
RECORD_SECONDS = 7
AI_MODEL = "qwen2.5:3b"

print("=" * 45)
print("  ASSALAMU ALAIKUM!")
print("  FARMER AI KIOSK BISMILLAH")
print("=" * 45)

print("\nLoading speech recognition model...")
whisper = WhisperModel("small", device="cpu", compute_type="int8")

print("\nChecking your local AI model...")
try:
    ollama.show(AI_MODEL)
    print("AI model is ready!")
except Exception as error:
    print("Could not connect to Ollama.")
    print("Make sure Ollama is running and the model is installed.")
    print("Details:", error)
    raise SystemExit

messages = [
    {
        "role": "system",
        "content": (
            "You are Farmer AI Kiosk Bismillah, a helpful assistant "
            "for Indian farmers. Answer simply and respectfully. "
            "Reply in the same language as the farmer's question. "
            "Never invent government scheme rules, eligibility, "
            "benefits, or deadlines. If you are unsure, say so. "
            "You provide guidance only and never submit applications. "
            "This prototype does not yet have verified government "
            "knowledge retrieval, so recommend official sources "
            "for confirmation."
        ),
    }
]

print("\nVoice chatbot ready!")
print("Press Enter to ask a question.")
print("Type exit and press Enter to stop.\n")

while True:
    command = input("Press Enter to speak, or type exit: ").strip()

    if command.lower() == "exit":
        print("Thank you for using Farmer AI Kiosk Bismillah!")
        break

    print(f"\nSpeak now for {RECORD_SECONDS} seconds...")

    try:
        audio = sd.rec(
            int(RECORD_SECONDS * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=MICROPHONE_DEVICE,
        )
        sd.wait()

        audio = audio.flatten()

        if np.max(np.abs(audio)) < 0.005:
            print("I couldn't hear you. Check your microphone and try again.\n")
            continue

        print("Recognizing your speech...")

        segments, info = whisper.transcribe(
            audio,
            beam_size=5,
            vad_filter=False,
            language=None,
        )

        question = " ".join(
            segment.text.strip() for segment in segments
        ).strip()

        if not question:
            print("I couldn't recognize your words. Please try again.\n")
            continue

        print("\nYou said:", question)
        print("\nThinking...")

        messages.append({"role": "user", "content": question})

        response = ollama.chat(
            model=AI_MODEL,
            messages=messages,
        )

        answer = response["message"]["content"]
        messages.append({"role": "assistant", "content": answer})

        print("\nFarmer AI:", answer, "\n")

    except Exception as error:
        print("\nSomething went wrong:", error)
        print("Please try again.\n")

