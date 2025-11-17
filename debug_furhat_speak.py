"""
Debugging script to send a custom utterance to the robot via Furhat API.
"""

from furhat_interface.furhat_api import FurhatAPI

# Set up Furhat API connection (update host/port as needed)
FURHAT_HOST = "localhost"  # Change to robot's IP if needed
FURHAT_PORT = 80

# Initialize API
furhat = FurhatAPI(host=FURHAT_HOST, port=FURHAT_PORT)

# Custom utterance to send
custom_text = "Hello, I am Furhat. This is a debug message."

# Send utterance
response = furhat.say(text=custom_text)
print("Response from Furhat:", response)
