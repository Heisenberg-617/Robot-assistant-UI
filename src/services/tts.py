import asyncio
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Tuple


class TTSService:
    def __init__(self):
        self.pyttsx3_engine = None

        # last-resort fallback only
        try:
            import pyttsx3
            self.pyttsx3_engine = pyttsx3.init()
            self.pyttsx3_engine.setProperty("rate", 180)
        except Exception:
            self.pyttsx3_engine = None

    def synthesize(self, text: str) -> Tuple[Optional[bytes], str]:
        cleaned_text = " ".join(text.split())
        if not cleaned_text:
            return None, "audio/wav"

        language = self._detect_language(cleaned_text)

        # =====================================
        # French / English -> Edge TTS
        # =====================================
        audio = self._synthesize_with_edge(cleaned_text, language)
        if audio:
            return audio, "audio/mp3"

        # =====================================
        # last resort only
        # =====================================
        audio = self._synthesize_with_pyttsx3(cleaned_text)
        if audio:
            return audio, "audio/wav"

        return None, "audio/wav"

    # ======================================================
    # EDGE TTS FOR ENGLISH AND FRENCH - BEST QUALITY
    # ======================================================
    def _synthesize_with_edge(self, text: str, language: str) -> Optional[bytes]:
        try:
            import edge_tts
        except ImportError:
            return None

        voice_map = {
            "fr": "fr-FR-DeniseNeural",
            "en": "en-US-AriaNeural",
        }

        voice = voice_map.get(language, "fr-FR-DeniseNeural")
        temp_path = Path(tempfile.gettempdir()) / f"edge-{uuid.uuid4()}.mp3"

        async def _run():
            communicate = edge_tts.Communicate(text, voice)
            # Add a timeout so it never hangs for 8.5 seconds again
            await asyncio.wait_for(communicate.save(str(temp_path)), timeout=4.0)

        try:
            # Use new_event_loop() to prevent Streamlit async clashes
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_run())
            
            if not temp_path.exists():
                return None

            audio = temp_path.read_bytes()
            temp_path.unlink(missing_ok=True)
            return audio

        except asyncio.TimeoutError:
            print("[EDGE TTS ERROR] Timed out after 4 seconds")
            return None
        except Exception as e:
            print(f"[EDGE TTS ERROR] {e}")
            return None
        finally:
            # Clean up the loop to prevent memory leaks
            try:
                loop.close()
            except Exception:
                pass


    # ======================================================
    # LAST RESORT WINDOWS ONLY
    # ======================================================
    def _synthesize_with_pyttsx3(self, text: str) -> Optional[bytes]:
        if self.pyttsx3_engine is None:
            return None

        temp_path = Path(tempfile.gettempdir()) / f"tts-{uuid.uuid4()}.wav"

        try:
            self.pyttsx3_engine.save_to_file(text, str(temp_path))
            self.pyttsx3_engine.runAndWait()

            if not temp_path.exists():
                return None

            audio = temp_path.read_bytes()
            temp_path.unlink(missing_ok=True)
            return audio

        except Exception:
            return None

    # ======================================================
    # LANGUAGE DETECTION
    # ======================================================
    def _detect_language(self, text: str) -> str:
        lowered = text.lower()

        if re.search(r"[\u0600-\u06FF]", text):
            return "ar"

        french_words = {
            "bonjour", "merci", "cafétéria",
            "administration", "étage", "salle",
            "accueil"
        }
        english_words = {
            "hello", "thanks", "building",
            "floor", "room"
        }

        fr_score = sum(word in lowered for word in french_words)
        en_score = sum(word in lowered for word in english_words)

        return "fr" if fr_score >= en_score else "en"