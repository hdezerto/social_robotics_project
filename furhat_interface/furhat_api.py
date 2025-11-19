
# Furhat API Interface
# Connects to Furhat robot for speech, gestures, and listening using furhat-realtime-api

from furhat_realtime_api import FurhatClient
import logging
import threading

class FurhatAPI:
    def __init__(self, ip_address):
        self.furhat = FurhatClient(ip_address)
        self.furhat.set_logging_level(logging.INFO)
        self.furhat.connect()
        self._listen_thread = None
        self._listening = threading.Event()
        self._listen_callback = None
        self._listen_languages = ["en-US"]

    def speak(self, text, wait=True, abort=True):
        try:
            self.furhat.request_speak_text(text, wait=wait, abort=abort)
        except Exception as e:
            print(f"Error in speak(): {e}")

    def set_gesture(self, gesture_name, intensity=1.0, duration=1.0, wait=False):
        try:
            self.furhat.request_gesture_start(name=gesture_name, intensity=intensity, duration=duration, wait=wait)
        except Exception as e:
            print(f"Error in set_gesture(): {e}")

    def set_expression(self, expression_name, intensity=1.0):
        """Map high-level facial expressions to Furhat gestures."""
        try:
            self.furhat.request_gesture_start(name=expression_name, intensity=intensity, wait=False)
        except Exception as e:
            print(f"Error in set_expression(): {e}")

    def listen_speech(self, callback, languages=None):
        """Continuously listens for speech and forwards transcripts to the callback."""
        self._listen_callback = callback
        if languages:
            self._listen_languages = languages
        self._listening.set()
        if self._listen_thread and self._listen_thread.is_alive():
            return
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()

    def _listen_loop(self):
        while self._listening.is_set():
            try:
                self.furhat.request_listen_config(languages=self._listen_languages)
                result = self.furhat.request_listen_start()
                transcript = self._extract_transcript(result)
                if transcript and self._listen_callback:
                    self._listen_callback(transcript)
            except Exception as e:
                print(f"Error in listen_speech(): {e}")
            finally:
                try:
                    self.furhat.request_listen_stop()
                except Exception:
                    pass

    def disconnect(self):
        try:
            self.stop_listening()
            self.furhat.disconnect()
        except Exception as e:
            print(f"Error disconnecting: {e}")

    def stop_listening(self):
        self._listening.clear()
        try:
            self.furhat.request_listen_stop()
        except Exception:
            pass
        if self._listen_thread:
            self._listen_thread.join(timeout=1.0)
            self._listen_thread = None

    def _extract_transcript(self, result):
        if not result:
            return None
        if isinstance(result, str):
            return result.strip()
        if isinstance(result, dict):
            for key in ("text", "phrase", "utterance", "message"):
                value = result.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
                if isinstance(value, dict):
                    nested = self._extract_transcript(value)
                    if nested:
                        return nested
        if isinstance(result, (list, tuple)):
            for item in result:
                extracted = self._extract_transcript(item)
                if extracted:
                    return extracted
        return None
