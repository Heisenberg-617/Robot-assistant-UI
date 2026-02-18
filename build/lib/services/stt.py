import assemblyai as aai  
from dotenv import load_dotenv
import os

load_dotenv(override=True)

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

class SpeechToTextService:

    def __init__(self):
        self.config = aai.TranscriptionConfig(
            speech_models=['universal-3-pro'],
            language_detection=True,
            speaker_labels=True,
        )
        self.transcriber = aai.Transcriber()

    def transcribe(self, audio_bytes: bytes) -> str:
        transcript = self.transcriber.transcribe(
            data=audio_bytes,
            config=self.config
        )
        return transcript.text

