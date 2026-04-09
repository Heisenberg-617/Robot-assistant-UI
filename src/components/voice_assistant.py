from functools import lru_cache

import streamlit as st


VOICE_ASSISTANT_HTML = """
<div class="voice-assistant-root">
  <button class="voice-orb" type="button" aria-label="Voice assistant microphone">
    <span class="voice-orb-icon">🎙️</span>
  </button>
  <div class="voice-status">Prêt</div>
  <div class="voice-hint">Touchez l'orbe pour parler, puis touchez à nouveau pour envoyer.</div>
</div>
"""


VOICE_ASSISTANT_CSS = """
.voice-assistant-root {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.7rem;
  padding: 0.35rem 0 0.8rem 0;
}

.voice-orb {
  width: 170px;
  height: 170px;
  border: none;
  border-radius: 999px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.98), rgba(255, 255, 255, 0.18) 28%, transparent 29%),
    linear-gradient(145deg, #1f2937 0%, #111827 58%, #020617 100%);
  color: white;
  box-shadow:
    0 0 0 18px rgba(15, 23, 42, 0.06),
    0 24px 60px rgba(15, 23, 42, 0.28);
  transition: transform 180ms ease, box-shadow 180ms ease, filter 180ms ease;
}

.voice-orb:hover {
  transform: scale(1.02);
  filter: brightness(1.03);
}

.voice-orb:active {
  transform: scale(0.98);
}

.voice-orb.listening {
  animation: voice-pulse 1.3s infinite ease-in-out;
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.98), rgba(255, 255, 255, 0.18) 28%, transparent 29%),
    linear-gradient(145deg, #2563eb 0%, #1d4ed8 55%, #0f172a 100%);
  box-shadow:
    0 0 0 18px rgba(37, 99, 235, 0.12),
    0 24px 60px rgba(37, 99, 235, 0.26);
}

.voice-orb.processing,
.voice-orb.speaking {
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.98), rgba(255, 255, 255, 0.18) 28%, transparent 29%),
    linear-gradient(145deg, #38bdf8 0%, #2563eb 52%, #0f172a 100%);
}

.voice-orb-icon {
  font-size: 3.25rem;
  line-height: 1;
}

.voice-status {
  color: #0f172a;
  font-size: 1.08rem;
  font-weight: 800;
  text-align: center;
}

.voice-hint {
  color: #64748b;
  font-size: 0.93rem;
  text-align: center;
  line-height: 1.45;
  max-width: 20rem;
}

@keyframes voice-pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.03); }
  100% { transform: scale(1); }
}
"""


VOICE_ASSISTANT_JS = """
export default function(component) {
    const { parentElement, data, setTriggerValue } = component;
    const orb = parentElement.querySelector('.voice-orb');
    const status = parentElement.querySelector('.voice-status');
    const hint = parentElement.querySelector('.voice-hint');

    if (!orb || !status || !hint) {
        return;
    }

    let mediaRecorder = component.__mediaRecorder || null;
    let mediaStream = component.__mediaStream || null;
    let chunks = component.__chunks || [];
    let currentAudio = component.__currentAudio || null;
    let isBusy = component.__isBusy || false;
    let lastRequestNonce = component.__lastRequestNonce || null;

    const resetVisualState = () => {
        orb.classList.remove('listening', 'processing', 'speaking');
        status.textContent = 'Prêt';
        hint.textContent = "Touchez l'orbe pour parler, puis touchez à nouveau pour envoyer.";
    };

    const setVisualState = (mode, label, hintText) => {
        orb.classList.remove('listening', 'processing', 'speaking');
        if (mode) {
            orb.classList.add(mode);
        }
        status.textContent = label;
        hint.textContent = hintText;
    };

    const blobToBase64 = (blob) =>
        new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                const result = String(reader.result || '');
                resolve(result.includes(',') ? result.split(',')[1] : '');
            };
            reader.onerror = () => reject(reader.error);
            reader.readAsDataURL(blob);
        });

    const stopTracks = () => {
        if (mediaStream) {
            mediaStream.getTracks().forEach((track) => track.stop());
            mediaStream = null;
            component.__mediaStream = null;
        }
    };

    const apiUrl = () => {
        const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
        const hostname = window.location.hostname || '127.0.0.1';
        return `${protocol}//${hostname}:${data.api_port}/voice`;
    };

    const sendRecording = async (blob, mimeType) => {
        const audioBase64 = await blobToBase64(blob);
        const nonce = Date.now();
        lastRequestNonce = nonce;
        component.__lastRequestNonce = nonce;
        isBusy = true;
        component.__isBusy = true;
        setVisualState('processing', 'Traitement...', 'Le robot prépare sa réponse.');

        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 45000);

        try {
            const response = await fetch(apiUrl(), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    audio_base64: audioBase64,
                    mime_type: mimeType,
                    conversation_id: data.conversation_id,
                }),
                signal: controller.signal,
            });

            const payload = await response.json();
            if (!response.ok) {
                throw new Error(payload.error || 'Le traitement vocal a échoué.');
            }

            setTriggerValue('voice_result', {
                nonce,
                response: payload.response || '',
                transcription: payload.transcription || '',
            });

            if (!payload.response_audio_base64) {
                isBusy = false;
                component.__isBusy = false;
                setVisualState('', 'Réponse prête', 'Le robot a répondu sans audio.');
                return;
            }

            if (currentAudio) {
                currentAudio.pause();
                currentAudio = null;
            }

            currentAudio = new Audio(`data:${payload.response_audio_mime_type || 'audio/mp3'};base64,${payload.response_audio_base64}`);
            component.__currentAudio = currentAudio;
            setVisualState('speaking', 'Réponse vocale', 'Le robot vous répond maintenant.');

            currentAudio.onended = () => {
                isBusy = false;
                component.__isBusy = false;
                resetVisualState();
                setTriggerValue('playback_finished', nonce);
            };

            currentAudio.onerror = () => {
                isBusy = false;
                component.__isBusy = false;
                setVisualState('', 'Lecture bloquée', 'La réponse audio est prête, mais la lecture a échoué.');
                setTriggerValue('error', 'Audio playback failed.');
            };

            await currentAudio.play();
        } catch (error) {
            isBusy = false;
            component.__isBusy = false;
            setVisualState('', 'Erreur vocale', 'Réessayez après quelques secondes.');
            setTriggerValue('error', String(error));
        } finally {
            window.clearTimeout(timeout);
        }
    };

    const startRecording = async () => {
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Microphone access is not supported by this browser.');
            }

            mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            component.__mediaStream = mediaStream;

            let mimeType = '';
            if (window.MediaRecorder && MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                mimeType = 'audio/webm;codecs=opus';
            } else if (window.MediaRecorder && MediaRecorder.isTypeSupported('audio/webm')) {
                mimeType = 'audio/webm';
            }

            mediaRecorder = mimeType ? new MediaRecorder(mediaStream, { mimeType }) : new MediaRecorder(mediaStream);
            component.__mediaRecorder = mediaRecorder;
            chunks = [];
            component.__chunks = chunks;

            mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    chunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                try {
                    const actualMimeType = mediaRecorder.mimeType || 'audio/webm';
                    const blob = new Blob(chunks, { type: actualMimeType });
                    stopTracks();
                    await sendRecording(blob, actualMimeType);
                } catch (error) {
                    isBusy = false;
                    component.__isBusy = false;
                    setVisualState('', 'Capture impossible', 'Veuillez réessayer.');
                    setTriggerValue('error', String(error));
                }
            };

            mediaRecorder.start();
            setVisualState('listening', 'J’écoute...', "Touchez encore l'orbe quand vous avez terminé.");
        } catch (error) {
            setVisualState('', 'Micro bloqué', 'Autorisez le microphone puis réessayez.');
            setTriggerValue('error', String(error));
        }
    };

    const stopRecording = async () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
        }
    };

    orb.onclick = async () => {
        if (isBusy) {
            return;
        }

        if (mediaRecorder && mediaRecorder.state === 'recording') {
            await stopRecording();
        } else {
            await startRecording();
        }
    };

    if (data.reset_token && data.reset_token !== component.__resetToken) {
        component.__resetToken = data.reset_token;
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
            component.__currentAudio = null;
        }
        isBusy = false;
        component.__isBusy = false;
        resetVisualState();
    }

    if (!isBusy && !(mediaRecorder && mediaRecorder.state === 'recording')) {
        resetVisualState();
    }

    return () => {
        if (currentAudio) {
            currentAudio.pause();
        }
        stopTracks();
    };
}
"""


@lru_cache(maxsize=1)
def _get_voice_component():
    return st.components.v2.component(
        "voice_assistant_orb",
        html=VOICE_ASSISTANT_HTML,
        css=VOICE_ASSISTANT_CSS,
        js=VOICE_ASSISTANT_JS,
    )


def voice_assistant_orb(*, key: str, data: dict | None = None):
    component = _get_voice_component()
    return component(
        key=key,
        data=data or {},
        default={
            "voice_result": None,
            "playback_finished": None,
            "error": None,
        },
        height="content",
        on_voice_result_change=lambda: None,
        on_playback_finished_change=lambda: None,
        on_error_change=lambda: None,
    )
