import uuid
from src.workflow import Workflow
from src.services.stt import SpeechToTextService
from src.services.recorder import record

import sys
sys.stdout.reconfigure(encoding='utf-8')


def main():
    # Initialize workflow and STT
    wf = Workflow()
    stt = SpeechToTextService()

    # Generate a single conversation ID
    conversation_id = str(uuid.uuid4())

    print("\n=== Continuous Workflow Test ===")
    print("Conversation ID:", conversation_id)
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            print("Recording...")

            # Record audio
            file_path = record(seconds=5)

            # Transcribe
            user_query = stt.transcribe(file_path)

            # Stop if nothing recognized
            if not user_query or user_query.strip() == "":
                print("\nNo recognizable speech detected. Ending conversation.")
                break

            print("\nUser Query:", user_query)

            # Run workflow with SAME conversation ID
            history = wf.run_text(user_query, conversation_id=conversation_id)

            print("\n=== Chat History ===")
            last_message = history[-1]
            print(f"\nAssistant: {last_message['content']}\n")

    except KeyboardInterrupt:
        print("\n\nStopped by user (Ctrl+C).")

    print("\n=== Test Completed ===")


if __name__ == "__main__":
    main()