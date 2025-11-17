# Furhat API Interface
# Connects to Furhat robot for speech and expressions


import requests
import websocket
import threading
import json

class FurhatAPI:
    def __init__(self, ip_address):
        self.base_url = f"http://{ip_address}:80/api"
        self.ws_url = f"ws://{ip_address}:80/api/ws"
        self.ws = None
        self.speech_callback = None

    def speak(self, text):
        url = f"{self.base_url}/tts/say"
        payload = {"text": text}
        requests.post(url, json=payload)

    def set_expression(self, expression):
        url = f"{self.base_url}/face/set"
        payload = {"emotion": expression}
        requests.post(url, json=payload)

    def listen_speech(self, callback):
        """
        Starts a background WebSocket listener for speech recognition events.
        Calls `callback(transcript)` whenever speech is recognized.
        """
        self.speech_callback = callback
        def on_message(ws, message):
            data = json.loads(message)
            if data.get("eventName") == "SpeechRecognized":
                transcript = data["data"]["text"]
                if self.speech_callback:
                    self.speech_callback(transcript)
        def on_error(ws, error):
            print("WebSocket error:", error)
        def on_close(ws):
            print("WebSocket closed")
        def on_open(ws):
            print("WebSocket connection opened")
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        threading.Thread(target=self.ws.run_forever, daemon=True).start()
