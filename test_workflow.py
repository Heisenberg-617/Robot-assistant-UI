import uuid
from src.workflow import Workflow
import sys
sys.stdout.reconfigure(encoding='utf-8')

def main():
    # Initialize workflow
    wf = Workflow()

    conversation_id = "9b388ac4-7a9a-498b-b233-ad011266281p"  # Generate a unique conversation ID
    
    user_query = "Take me to the student lounge"  # Example user query that should trigger the navigation tool

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