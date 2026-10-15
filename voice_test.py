
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel

MICROPHONE_DEVICE = 1
SAMPLE_RATE = 16000
DURATION = 7

print("Loading Whisper model...")
model = WhisperModel("base", device="cpu", compute_type="int8")

print("\nFarmer AI Kiosk Bismillah")
print("Speak clearly for 7 seconds.")
print("Try: My name is Nizam. I am testing my farmer kiosk.")

audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32",
    device=MICROPHONE_DEVICE
)
sd.wait()

audio = audio.flatten()
print("\nRecorded audio volume:", round(float(np.max(np.abs(audio))), 4))
print("Recognizing speech...")

segments, info = model.transcribe(
    audio,
    beam_size=5,
    vad_filter=False,
    language="en"
)

recognized_text = " ".join(
    segment.text.strip() for segment in segments
)

if recognized_text:
    print("\nYou said:", recognized_text)
else:
    print("\nNo speech recognized. Try speaking louder and closer to the microphone.")
