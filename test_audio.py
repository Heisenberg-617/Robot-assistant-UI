import pyaudio
import wave
import os
from src.services.stt import SpeechToTextService

def record_and_test(seconds, output_filename="test_audio.wav"):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000 

    p = pyaudio.PyAudio()

    print(f"--- Recording for {seconds} seconds... ---")

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []
    for i in range(0, int(RATE / CHUNK * seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("--- Recording finished. Saving to file... ---")

    # Cleanup hardware
    stream.stop_stream()
    stream.close()
    
    # --- SAVE TO WAV FILE ---
    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    
    p.terminate()

    # Get the absolute path to ensure the service finds it
    file_path = os.path.abspath(output_filename)
    print(f"File saved at: {file_path}")

    # --- PROCESS VIA SERVICE ---
    stt = SpeechToTextService()
    text = stt.transcribe(file_path)
    
    print(f"\nRESULT:\n{text}")
    
    # Optional: clean up the file after testing
    # os.remove(file_path)

if __name__ == "__main__":
    record_and_test(seconds=10)