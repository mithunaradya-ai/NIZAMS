
import ollama

print("=" * 45)
print("  ASSALAMU ALAIKUM!")
print("  FARMER AI KIOSK BISMILLAH")
print("=" * 45)

print("\nYour local AI assistant is ready!")
print("Type 'exit' to stop.\n")

while True:
    farmer_question = input("Farmer: ").strip()

    if farmer_question.lower() == "exit":
        print("Thank you for using Farmer AI Kiosk!")
        break

    if not farmer_question:
        print("Please enter a question.")
        continue

    print("\nThinking...\n")

    try:
        response = ollama.chat(
            model="qwen2.5:3b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Farmer AI Kiosk Bismillah, "
                        "a helpful multilingual assistant for Indian farmers. "
                        "Answer in the language used by the farmer. "
                        "Use simple, respectful language. "
                        "Never invent government scheme rules, eligibility, "
                        "benefits, or deadlines. If you are unsure, say so. "
                        "This is an early prototype without verified knowledge "
                        "retrieval, so direct users to official sources "
                        "for confirmation."
                    ),
                },
                {"role": "user", "content": farmer_question},
            ],
        )

        print("Farmer AI:", response["message"]["content"])
        print()

    except Exception as error:
        print("Could not connect to the AI.")
        print("Details:", error)
