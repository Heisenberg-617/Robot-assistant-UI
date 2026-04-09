import os
import base64
import tempfile
from pathlib import Path

from faster_whisper import WhisperModel


class SpeechToTextService:
    def __init__(self):
        self.model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=4)

    def transcribe(self, audio_input: bytes | str) -> str:
        temp_path = None
        try:
            temp_path = self._to_audio_file(audio_input)

            segments, info = self.model.transcribe(
                str(temp_path),
                beam_size=5,              # UPGRADED: Massive accuracy boost for French
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=400,  # Wait longer before cutting off
                    speech_pad_ms=400            # Keep 400ms of audio before/after speech
                ),
                condition_on_previous_text=False,
                temperature=0.0,
                no_speech_threshold=0.6,   # UPGRADED: Stop hallucinating from background noise
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
        # Write to local app folder instead of Windows Temp to avoid Defender scans
        temp_dir = Path("./tmp_audio")
        temp_dir.mkdir(exist_ok=True)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=temp_dir) as handle:
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