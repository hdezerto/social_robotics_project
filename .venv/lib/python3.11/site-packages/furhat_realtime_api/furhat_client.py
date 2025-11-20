import asyncio
from typing import Dict, Any, Optional
from .async_furhat_client import AsyncFurhatClient
from .events import Events  
from threading import Thread

class FurhatClient:
    def __init__(self, host: str, auth_key: Optional[str] = None):
        self._loop = asyncio.new_event_loop()
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.async_client = AsyncFurhatClient(host, auth_key)

    def set_logging_level(self, level: int):
        self.async_client.set_logging_level(level)

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _run_coroutine(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def connect(self):
        self._run_coroutine(self.async_client.connect())

    def disconnect(self):
        return self._run_coroutine(self.async_client.disconnect())

    ## Furhat Event Protocol ##

    # SPEAK

    def request_speak_text(self, text: str, wait: bool = True, abort: bool = True):
        self._run_coroutine(self.async_client.request_speak_text(text=text, abort=abort, wait=wait))

    def request_speak_audio(self, url: str, text: str = "AUDIO", lipsync: bool = True, abort: bool = False, wait: bool = False):
        self._run_coroutine(self.async_client.request_speak_audio(url=url, text=text, lipsync=lipsync, wait=wait))

    def request_speak_stop(self):
        self._run_coroutine(self.async_client.request_speak_stop())

    # LISTEN

    def request_listen_config(self, languages: list = ["en-US"], phrases: list = None):
        self._run_coroutine(self.async_client.request_listen_config(languages=languages, phrases=phrases))

    def request_listen_start(self, partial: bool = False, concat: bool = True, stop_no_speech: bool = True, stop_robot_start: bool = True, stop_user_end: bool = True, resume_robot_end: bool = False, no_speech_timeout: float = 8.0, end_speech_timeout: float = 1.0):
        event = {
            "type": Events.request_listen_start,
            "partial": partial,
            "concat": concat,
            "stop_no_speech": stop_no_speech,
            "stop_robot_start": stop_robot_start,
            "stop_user_end": stop_user_end,
            "resume_robot_end": resume_robot_end,
            "no_speech_timeout": no_speech_timeout,
            "end_speech_timeout": end_speech_timeout
        }
        listen_result = self._run_coroutine(self.async_client.send_event_and_wait(
                event, return_type=[Events.response_hear_end, Events.response_listen_end], timeout=30.0))
        return listen_result.get("text", "")

    # VOICE

    def request_voice_status(self):
        return self._run_coroutine(self.async_client.request_voice_status())
    
    def request_voice_config(self, 
                                   voice_id: Optional[str] = None,
                                   name: Optional[str] = None,
                                   gender: Optional[str] = None,
                                   language: Optional[str] = None,
                                   provider: Optional[str] = None,
                                   input_language: bool = True):
        return self._run_coroutine(self.async_client.request_voice_config(
            voice_id=voice_id,
            name=name,
            gender=gender,
            language=language,
            provider=provider,
            input_language=input_language
        ))

    # ATTENTION

    def request_attend_user(self, user_id: str = "closest"):
        return self._run_coroutine(self.async_client.request_attend_user(user_id))

    def request_attend_location(self, x: float, y: float, z: float):
        return self._run_coroutine(self.async_client.request_attend_location(x, y, z))

    # GESTURES

    def request_gesture_start(self, name: str, intensity: float = 1.0, duration: float = 1.0, wait: bool = False):
        return self._run_coroutine(self.async_client.request_gesture_start(name=name, intensity=intensity, duration=duration, wait=wait))

    # FACE

    def request_face_params(self, params: dict):
        """Set facial animation parameters directly"""
        return self._run_coroutine(self.async_client.request_face_params(params))

    def request_face_headpose(self, yaw: float, pitch: float, roll: float, relative: bool):
        """Override automatic head pose and directly control the head pose of the robot"""
        return self._run_coroutine(self.async_client.request_face_headpose(yaw, pitch, roll, relative))

    def request_face_config(self, face_id: Optional[str], visibility: Optional[bool], microexpressions: Optional[bool]):
        """Set the current mask and character (face_id), and/or face visibility"""
        return self._run_coroutine(self.async_client.request_face_config(face_id, visibility, microexpressions))

    def request_face_status(self, face_id: bool = True, face_list: bool = True):
        """Get current and available masks and characters (face_id)"""
        return self._run_coroutine(self.async_client.request_face_status(face_id, face_list))

    def request_face_reset(self):
        """Resets all facial parameters to default"""
        return self._run_coroutine(self.async_client.request_face_reset())

    # LED

    def request_led_set(self, color: str):
        """Set the color of the LED"""
        return self._run_coroutine(self.async_client.request_led_set(color))

    # USERS

    def request_users_once(self):
        """Get the current user status"""
        return self._run_coroutine(self.async_client.request_users_once())
    
    # CAMERA

    def request_camera_once(self):
        """Get a camera snapshot"""
        return self._run_coroutine(self.async_client.request_camera_once())