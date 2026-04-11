from cartesia import Cartesia
import os


class TTSService:
    def __init__(self):
        self.client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))

    def synthesize(self, text: str):
        text = " ".join(text.split())
        if not text:
            return None, "audio/wav"

        language = self._detect_language(text)

        voice_id = self._get_voice_id(language)

        response = self.client.tts.generate(
            model_id="sonic-3",
            transcript=text,
            voice={
                "mode": "id",
                "id": voice_id
            },
            output_format={
                "container": "wav",
                "encoding": "pcm_f32le",
                "sample_rate": 44100
            },
        )

        audio_bytes = response.write_to_file("output.wav")

        with open("output.wav", "rb") as f:
            audio = f.read()

        return audio, "audio/wav"

    # ======================================================
    # VOICE SELECTION (your logic preserved)
    # ======================================================
    def _get_voice_id(self, language: str) -> str:
        if language == "en":
            return "a167e0f3-df7e-4d52-a9c3-f949145efdab"
        elif language == "fr":
            return "7c58f4a4-a72c-42fa-a503-41b9408820f3"
        elif language == "ar":
            return "664aec8a-64a4-4437-8a0b-a61aa4f51fe6"
        return "a167e0f3-df7e-4d52-a9c3-f949145efdab"  # Default to English voice

    # ======================================================
    # LANGUAGE DETECTION (your version kept)
    # ======================================================
    def _detect_language(self, text: str) -> str:
        text = text.lower()

        # =========================
        # FREQUENT WORD LISTS
        # =========================

        french_words = {
            "bonjour", "salut", "merci", "oui", "non", "où", "comment",
            "je", "tu", "il", "elle", "nous", "vous", "ils", "est",
            "aller", "faire", "pouvez", "s'il", "vous", "aide", "robot",
            "station", "destination"
        }

        english_words = {
            "hello", "hi", "thanks", "yes", "no", "where", "how",
            "I","i", "you", "he", "she", "we", "they", "is", "are",
            "go", "help", "robot", "station", "floor",
            "can", "please", "navigate", "destination"
        }

        arabic_words = {
            "مرحبا", "السلام", "نعم", "لا", "أين", "كيف", "سلام"
            "أنا", "أنت", "هو", "هي", "نحن", "أنتم",
            "مساعدة", "روبوت", "توجه", "اذهب", "شكرا", "هل"
        }

        # =========================
        # TOKENIZE TEXT
        # =========================
        words = set(text.split())

        # =========================
        # SCORE EACH LANGUAGE
        # =========================
        fr_score = len(words & french_words)
        en_score = len(words & english_words)
        ar_score = len(words & arabic_words)

        # =========================
        # DECISION LOGIC
        # =========================
        if ar_score > fr_score and ar_score > en_score:
            return "ar"
        if fr_score > en_score and fr_score > ar_score:
            return "fr"
        return "en"