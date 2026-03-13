import uuid
from src.workflow import Workflow
from src.services.stt import SpeechToTextService
from src.services.recorder import record

import sys
sys.stdout.reconfigure(encoding='utf-8')


def main():
    # Initialize workflow
    wf = Workflow()

    # Generate a unique conversation ID
    conversation_id = str(uuid.uuid4())  
    
    # Record audio and transcribe via recorder service
    file_path = record(seconds=5)
    stt = SpeechToTextService()
    user_query = stt.transcribe(file_path)

    print("\n=== Testing Workflow ===")
    print("User Query:", user_query)
    print("Conversation ID:", conversation_id)

    # Run workflow
    history = wf.run_text(user_query, conversation_id=conversation_id)

    print("\n=== Chat History ===")

    for message in history:
        role = message["role"].capitalize()
        content = message["content"]
        print(f"{role}: {content}\n")

    print("=== Test Completed ===")


if __name__ == "__main__":
    main()