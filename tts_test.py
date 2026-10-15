import subprocess
import sys

text = (
    "Welcome to Farmer AI Kiosk Bismillah. "
    "I can help you understand farming schemes and "
    "government services. Please speak your question clearly."
)

print("Playing the English voice test...")

subprocess.run(
    [
        sys.executable,
        "-m",
        "piper",
        "-m",
        "en_US-lessac-medium",
        "-f",
        "english_test.wav",
        "--",
        text,
    ],
    check=True,
)

print("Audio saved as english_test.wav")
print("Open the audio file in your project folder to listen.")
