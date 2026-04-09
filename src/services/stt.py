import os
import base64
import tempfile
from pathlib import Path

from faster_whisper import WhisperModel


class SpeechToTextService:
    def __init__(self):
        self.language = (os.getenv("VOICE_LANGUAGE_CODE", "fr").strip() or "fr")
        self.model = WhisperModel("base", device="cpu", compute_type="int8")

    def transcribe(self, audio_input: bytes | str) -> str:
        temp_path = None
        try:
            temp_path = self._to_audio_file(audio_input)

            segments, info = self.model.transcribe(
                str(temp_path),
                language=self.language,
                beam_size=1,
                vad_filter=True,
                condition_on_previous_text=False,
                temperature=0.0,
            )

            text = " ".join(segment.text.strip() for segment in segments).strip()
            return text

        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def transcribe_to_file(self, audio_input: bytes | str, file_path: str) -> str:
        transcript = self.transcribe(audio_input)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(transcript)
        return transcript

    def _to_audio_file(self, audio_input: bytes | str) -> Path:
        if isinstance(audio_input, (bytes, bytearray)):
            return self._write_temp_audio_file(bytes(audio_input))

        s = audio_input.strip()

        p = Path(s)
        if p.exists():
            return p

        if s.startswith("data:audio/") and "," in s:
            s = s.split(",", 1)[1]

        try:
            raw = base64.b64decode(s, validate=True)
            return self._write_temp_audio_file(raw)
        except Exception as e:
            raise ValueError(
                "audio_input must be raw bytes, an existing file path, or base64 audio data."
            ) from e

    def _write_temp_audio_file(self, audio_bytes: bytes) -> Path:
        suffix = self._guess_audio_suffix(audio_bytes)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            handle.write(audio_bytes)
            return Path(handle.name)

    def _guess_audio_suffix(self, audio_bytes: bytes) -> str:
        if audio_bytes.startswith(b"RIFF"):
            return ".wav"
        if audio_bytes.startswith(b"\x1a\x45\xdf\xa3"):
            return ".webm"
        if audio_bytes.startswith(b"OggS"):
            return ".ogg"
        if audio_bytes.startswith(b"ID3") or audio_bytes[:2] == b"\xff\xfb":
            return ".mp3"
        if b"ftyp" in audio_bytes[:32]:
            return ".m4a"
        return ".webm"