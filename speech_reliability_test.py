
import pyttsx3
import time

print("Starting voice test...")

for i in range(5):
    print(f"Speaking test {i + 1}...")

    try:
        speaker = pyttsx3.init("sapi5")
        speaker.setProperty("rate", 145)
        speaker.setProperty("volume", 1.0)

        speaker.say(f"Hello! This is voice test number {i + 1}.")
        speaker.runAndWait()
        speaker.stop()
        del speaker

        print("Test completed.")
        time.sleep(1)

    except Exception as error:
        print("Speech error:", error)

print("Voice test finished.")
