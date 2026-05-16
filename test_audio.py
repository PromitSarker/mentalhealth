import urllib.request
import json
import base64
import time
import subprocess
import os
import signal

def test_apis():
    # Load .env
    from dotenv import load_dotenv
    load_dotenv()
    
    # start uvicorn
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    process = subprocess.Popen([".venv/bin/python", "-m", "uvicorn", "app.main:app", "--port", "8082"], env=env)
    time.sleep(2) # wait for server to start

    try:
        # test STT
        print("Testing STT...")
        stt_payload = {
            "audio_data": base64.b64encode(b"test audio").decode("utf-8"),
            "language": "en-GB"
        }
        stt_req = urllib.request.Request(
            "http://localhost:8082/ai/audio/stt",
            data=json.dumps(stt_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(stt_req) as response:
                stt_res = json.loads(response.read().decode("utf-8"))
                print("STT Response:", stt_res)
        except urllib.error.HTTPError as e:
            print("STT Failed:", e.read().decode("utf-8"))

        # test TTS
        print("\nTesting TTS...")
        tts_payload = {
            "text": "Hello world",
            "voice": "en-GB-Neural2-A"
        }
        tts_req = urllib.request.Request(
            "http://localhost:8082/ai/audio/tts",
            data=json.dumps(tts_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(tts_req) as response:
                tts_res = json.loads(response.read().decode("utf-8"))
                audio_b64 = tts_res.get("audio_data", "")
                print(f"TTS Response: (audio_data length {len(audio_b64)})")
                
                if audio_b64:
                    with open("output.wav", "wb") as f:
                        f.write(base64.b64decode(audio_b64))
                    print("SUCCESS: Audio saved to output.wav!")
        except urllib.error.HTTPError as e:
            print("TTS Failed:", e.read().decode("utf-8"))

    finally:
        process.send_signal(signal.SIGINT)
        process.wait()

if __name__ == "__main__":
    test_apis()
