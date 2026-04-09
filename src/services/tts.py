import asyncio
import re
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Tuple


class TTSService:

    def synthesize(self, text: str) -> Tuple[Optional[bytes], str]:
        cleaned_text = " ".join(text.split())
        if not cleaned_text:
            return None, "audio/wav"

        language = self._detect_language(cleaned_text)

        audio = self._synthesize_with_edge(cleaned_text, language)
        if audio:
            return audio, "audio/mp3"

        # FAST FAIL. No pyttsx3. If the network is down, return silence.
        return None, "audio/wav"

    # ======================================================
    # EDGE TTS (REQUIRES INTERNET ACCESS)
    # ======================================================
    def _synthesize_with_edge(self, text: str, language: str) -> Optional[bytes]:
        try:
            import edge_tts
        except ImportError:
            return None

        voice_map = {
            "fr": "fr-FR-VivienneMultilingualNeural",
            "en": "en-US-AndrewMultilingualNeural",
        }

        voice = voice_map.get(language, "en-US-AndrewMultilingualNeural")
        temp_path = Path(tempfile.gettempdir()) / f"edge-{uuid.uuid4()}.mp3"

        async def _run():
            communicate = edge_tts.Communicate(text, voice)
            await asyncio.wait_for(communicate.save(str(temp_path)), timeout=20)

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_run())
            
            if not temp_path.exists():
                return None

            audio = temp_path.read_bytes()
            temp_path.unlink(missing_ok=True)
            return audio

        except asyncio.TimeoutError:
            print("[EDGE TTS ERROR] Timed out - Network may be down or blocked by firewall.")
            return None
        except Exception as e:
            print(f"[EDGE TTS ERROR] {e}")
            return None
        finally:
            try:
                loop.close()
            except Exception:
                pass

    # ======================================================
    # LANGUAGE DETECTION
    # ======================================================
    def _detect_language(self, text: str) -> str:
        if not text:
            return "en"

        french_chars = set("àâäéèêëïîôùûüÿçœæÀÂÄÉÈÊËÏÎÔÙÛÜŸÇŒÆ")
        if any(char in french_chars for char in text):
            return "fr"
        
        lowered = text.lower()
        french_markers = {"bonjour", "merci", "oui", "non", "salle", "étage", "où", "batiment", "aller", "pouvez", "vous"}
        english_markers = {"hello", "thanks", "yes", "no", "room", "floor", "where", "building", "take", "what"}

        fr_score = sum(1 for w in french_markers if w in lowered)
        en_score = sum(1 for w in english_markers if w in lowered)

        return "fr" if fr_score >= en_score else "en"