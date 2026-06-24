import logging
import os

from furhat_realtime_api import FurhatClient


# Only the IP, no port.
ROBOT_IP = os.getenv("FURHAT_IP", "127.0.0.1")

# If you set an API key in the Realtime API page, set FURHAT_API_KEY.
API_KEY = os.getenv("FURHAT_API_KEY") or None

furhat = FurhatClient(ROBOT_IP, API_KEY)
furhat.set_logging_level(logging.INFO)

print("Connecting...")
furhat.connect()
print("Connected!")

furhat.request_speak_text(
    "Hello! I am Furhat, your host for 'Who Wants to Be a Furllionaire'. "
    "When you are ready to start the game, say: start game.",
    wait=True,
)

furhat.request_listen_config(languages=["en-US"])

print("Listening for 'start game'...")
heard = furhat.request_listen_start(
    partial=False,
    concat=True,
    stop_no_speech=True,
    no_speech_timeout=8.0,
)

print("ASR result:", repr(heard))

if heard and "start" in heard.lower():
    reply = "Great! Let's pretend the game is starting now."
else:
    reply = "I didn't quite catch 'start game', but thanks for talking to me!"

furhat.request_speak_text(reply, wait=True)

furhat.disconnect()
print("Disconnected.")
