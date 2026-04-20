# Robot Assistant Chatbot

A Streamlit-based campus robot assistant UI for robotics project. This project combines conversational AI, voice interaction, document retrieval, and navigation support into a single local UI.

## What this project does

- Provides a chat and voice assistant for campus visitors
- Supports document search over internal knowledge sources
- Resolves campus destination requests and prepares navigation payloads
- Uses AssemblyAI for speech-to-text and Cartesia for text-to-speech
- Hosts a Streamlit front-end with a custom voice orb component

## Repository structure

- `main.py` - CLI entrypoint showing how to launch the app
- `streamlit_app.py` - Streamlit application bootstrap
- `pyproject.toml` - Python dependency configuration
- `src/ui/app.py` - Streamlit UI structure and navigation workflow
- `src/workflow.py` - text/audio workflow orchestration
- `src/services/` - LLM, navigation, RAG, STT, and TTS services
- `src/components/` - custom voice assistant component
- `data/` - campus locations and document sources
- `vector_db/` - persisted vector embeddings for RAG search
- `memories/` - conversation history storage

## Requirements

- Python 3.11+
- `OPENAI_API_KEY`
- `ASSEMBLYAI_API_KEY`
- `CARTESIA_API_KEY`

## Setup

```powershell
cd d:\AI\robot-assistant-chatbot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

## Configuration

Create a `.env` file at the repository root with:

```text
OPENAI_API_KEY=sk-...
ASSEMBLYAI_API_KEY=...
CARTESIA_API_KEY=...
APP_MEMORY_BASE=./memories
ROBOT_NAVIGATION_API_URL=
```

## Run the app

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run streamlit_app.py
```

Open the URL shown by Streamlit in your browser.

## How it works

### Workflow

- `Workflow` builds both text and audio workflows
- `ChatWorkflow` handles chat conversation state
- `AudioWorkflow` performs STT, LLM generation, and TTS playback
- Conversation history is persisted in `memories/`

### LLM service

- `LLMService` uses a Groq-based chat model with tools
- `document_retriever` performs knowledge retrieval from the RAG database
- `navigation_tool` resolves location requests and starts navigation flow

### Navigation service

- `NavigationService` reads campus locations from `data/locations.json`
- It resolves fuzzy destination requests and prepares navigation payloads
- Robot command dispatch is currently a placeholder until `ROBOT_NAVIGATION_API_URL` is configured

### RAG service

- `RAGService` uses OpenAI embeddings and Chroma vector search
- Ingests documents from `data/` and stores vector data in `vector_db/`

### Voice support

- `SpeechToTextService` uses AssemblyAI to transcribe user audio
- `TTSService` uses Cartesia to generate WAV audio responses
- `src/components/voice_assistant.py` renders the custom voice orb component in Streamlit

## Useful commands

```powershell
# Run the application
streamlit run streamlit_app.py

# Rebuild the RAG index after updating documents
python -c "from src.services.rag import RAGService; RAGService().ingest_files(['data/cleaned_emines_docs.json'])"
```

## Notes

- The UI is optimized for French campus users, but the assistant replies in the language of the latest user message.
- `ROBOT_NAVIGATION_API_URL` is optional and only needed when connecting to a live robot navigation endpoint.

## License

See `LICENSE` for license details.
