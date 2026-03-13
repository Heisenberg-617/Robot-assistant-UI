import pyaudio
import wave
import os
from src.services.stt import SpeechToTextService

def record(seconds, base_dir="data/audios"):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000 

    os.makedirs(base_dir, exist_ok=True)

    existing_files = [f for f in os.listdir(base_dir) if f.endswith(".wav")]
    next_number = len(existing_files) + 1

    output_filename = f"audio_{next_number}.wav"
    file_path = os.path.join(base_dir, output_filename)

    p = pyaudio.PyAudio()

    print(f"--- Recording for {seconds} seconds... ---")

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []
    for _ in range(0, int(RATE / CHUNK * seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("--- Recording finished. Saving to file... ---")

    # Cleanup hardware
    stream.stop_stream()
    stream.close()
    p.terminate()
  
    # --- SAVE TO WAV FILE ---
    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    
    print(f"File saved at: {file_path}")
    
    return file_path