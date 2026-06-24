
# Furhat API Interface
# Connects to Furhat robot for speech, gestures, and listening using furhat-realtime-api

from furhat_realtime_api import FurhatClient
import logging
import threading
import time

class FurhatAPI:
    def __init__(self, ip_address):
        self.furhat = FurhatClient(ip_address)
        self.furhat.set_logging_level(logging.INFO)
        self.furhat.connect()
        self._listen_thread = None
        self._listening = threading.Event()
        self._listen_callback = None
        self._listen_languages = ["en-US"]
        # attention / head-pose monitor
        self._attention_thread = None
        self._attention_stop = threading.Event()
        self._attention_callback = None

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
                    self.furhat._run_coroutine(self.furhat.async_client.request_listen_stop())
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
            self.furhat._run_coroutine(self.furhat.async_client.request_listen_stop())
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

    def start_attention_monitor(self, callback, poll_interval: float = 0.25):
        """Call `callback(event_dict)` when gaze/attention updates arrive.
        event_dict example: {'state': 'towards'|'away'|'left'|'right'|'up'|'down', 'confidence': 0.0..1.0}
        Polls the robot for users/head-pose and calls `callback` when interpreted
        attention state changes. This simplified version only uses polling.
        """
        self._attention_callback = callback

        # If already running, do nothing
        if self._attention_thread and self._attention_thread.is_alive():
            return

        self._attention_stop.clear()
        logging.info("FurhatAPI: starting polling attention monitor")

        def _poll_loop():
            last_state = None
            while not self._attention_stop.is_set():
                try:
                    state = None
                    conf = 0.0

                    # First try users API (gives an 'attending' score)
                    users_raw = None
                    if hasattr(self.furhat, "request_users_once"):
                        try:
                            users_raw = self.furhat.request_users_once()
                        except Exception:
                            users_raw = None
                    if users_raw and isinstance(users_raw, dict):
                        try:
                            users_list = users_raw.get("users") or []
                            if isinstance(users_list, (list, tuple)) and len(users_list) > 0:
                                u = users_list[0]
                                # Try a few possible keys for attending-like values
                                attending = None
                                if isinstance(u, dict):
                                    attending = u.get("attending", u.get("attended", None))
                                if attending is not None:
                                    try:
                                        att_v = float(attending)
                                    except Exception:
                                        att_v = 0.0
                                    # Print only the attending value for calibration
                                    #print(f"FurhatAPI: attending={att_v}")
                                    if att_v >= 0.6:
                                        state = "towards"
                                        conf = min(1.0, 0.5 + att_v * 0.6)
                                    else:
                                        state = "away"
                                        conf = max(0.0, att_v)
                            else:
                                state = "away"
                                conf = 0.1
                        except Exception:
                            logging.exception("FurhatAPI: failed to parse users payload")

                    # Only notify on change
                    if state and state != last_state and self._attention_callback:
                        logging.info(f"FurhatAPI: attention state change -> {state} (conf={conf})")
                        try:
                            self._attention_callback({"state": state, "confidence": conf})
                        except Exception:
                            logging.exception("attention callback failed")
                        last_state = state
                except Exception:
                    logging.exception("attention polling failed")
                time.sleep(poll_interval)

        self._attention_thread = threading.Thread(target=_poll_loop, name="furhat-attention-poll", daemon=True)
        self._attention_thread.start()

    def stop_attention_monitor(self):
        try:
            self._attention_stop.set()
            if self._attention_thread:
                self._attention_thread.join(timeout=0.5)
                self._attention_thread = None
        except Exception:
            pass
