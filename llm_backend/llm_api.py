# LLM API Interface
# Communicates with LLM to generate tips and expressions

class LLMAPI:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_tip_and_expression(self, question, options, user_request=None):
        # For demo, return a dummy tip and expression
        tip = "Consider eliminating obviously wrong answers."
        expression = "smile"
        return tip, expression
