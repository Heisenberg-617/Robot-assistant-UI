import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src.workflow import Workflow


class VoiceBridgeServer:
    def __init__(self, memory_base: str = "./memories"):
        self.workflow = Workflow(memory_base=memory_base)
        self._server = ThreadingHTTPServer(("0.0.0.0", 0), self._build_handler())
        self.port = self._server.server_port
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def _build_handler(self):
        workflow = self.workflow

        class Handler(BaseHTTPRequestHandler):
            def do_OPTIONS(self):
                self.send_response(204)
                self._send_cors_headers()
                self.end_headers()

            def do_POST(self):
                if self.path.rstrip("/") != "/voice":
                    self.send_error(404)
                    return

                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length)

                try:
                    payload = json.loads(raw_body.decode("utf-8"))
                    audio_base64 = str(payload.get("audio_base64", ""))
                    audio_bytes = base64.b64decode(audio_base64)
                    conversation_id = payload.get("conversation_id")
                    result = workflow.run_audio(audio_bytes, conversation_id=conversation_id)
                    response_payload = {
                        "response": _state_value(result, "response") or "",
                        "transcription": _state_value(result, "transcription") or "",
                        "response_audio_base64": _encode_audio(_state_value(result, "response_audio")),
                        "response_audio_mime_type": _state_value(result, "response_audio_format", "audio/mp3")
                        or "audio/mp3",
                    }
                    self.send_response(200)
                    self._send_cors_headers()
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps(response_payload).encode("utf-8"))
                except Exception as exc:
                    self.send_response(500)
                    self._send_cors_headers()
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"error": str(exc) or "Voice processing failed."}).encode("utf-8")
                    )

            def log_message(self, format, *args):
                return

            def _send_cors_headers(self):
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")

        return Handler


def _state_value(result, key: str, default=None):
    if isinstance(result, dict):
        return result.get(key, default)
    return getattr(result, key, default)


def _encode_audio(audio_bytes: bytes | None) -> str | None:
    if not audio_bytes:
        return None
    return base64.b64encode(audio_bytes).decode("ascii")
