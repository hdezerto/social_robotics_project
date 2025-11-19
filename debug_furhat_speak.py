from furhat_realtime_api import FurhatClient
import logging

# 👇 IMPORTANT: only the IP, no port here
ROBOT_IP = "172.26.128.1"

# If you set an API key in the Realtime API page, put it here.
# If you allowed access without auth, keep this as None.
API_KEY = None  # e.g. "my-secret-key"

furhat = FurhatClient(ROBOT_IP, API_KEY)
furhat.set_logging_level(logging.INFO)

print("Connecting...")
furhat.connect()
print("Connected!")

furhat.request_speak_text(
    "Hello! I am Furhat, your host for 'Who Wants to Be a Furllionaire'. "
    "When you are ready to start the game, say: start game.",
    wait=True
)

# Configure listening (adjust language if needed)
furhat.request_listen_config(languages=["en-US"])

print("Listening for 'start game'...")
heard = furhat.request_listen_start(
    partial=False,
    concat=True,
    stop_no_speech=True,
    no_speech_timeout=8.0
)

print("ASR result:", repr(heard))

if heard and "start" in heard.lower():
    reply = "Great! Let's pretend the game is starting now."
else:
    reply = "I didn't quite catch 'start game', but thanks for talking to me!"

furhat.request_speak_text(reply, wait=True)

furhat.disconnect()
print("Disconnected.")