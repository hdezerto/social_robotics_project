# Furhat API Interface
# Connects to Furhat robot for speech and expressions

class FurhatAPI:
    def __init__(self):
        pass

    def speak(self, text):
        print(f"Furhat speaks: {text}")

    def set_expression(self, expression):
        print(f"Furhat sets expression: {expression}")
