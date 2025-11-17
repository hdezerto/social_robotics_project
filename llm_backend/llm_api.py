# LLM API Interface
# Communicates with LLM to generate tips and expressions

class LLMAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        # Placeholder: Initialize LLM client here

    def generate_assistant_response(self, question, options, user_request=None):
        """
        Generate a helpful assistant response and facial expression for the robot using the LLM.
        Guardrails: Do NOT disclose the correct answer. Always return a response and a facial expression tag.
        """
        prompt = (
            f"You are an assistant helping a user answer a multiple-choice question. "
            f"Do NOT disclose the correct answer. "
            f"Instead, provide a helpful response and a suggested facial expression for the robot. "
            f"Format your response as: RESPONSE: <response>\\nEXPRESSION: <expression>. "
            f"\\nQuestion: {question}\\nOptions: {options}\\nUser request: {user_request if user_request else ''}"
        )
        # Placeholder: Call LLM API with the constructed prompt
        # Example:
        # response = self.client.generate_response(prompt)
        # Parse response to extract response and expression
        # response_text = ...
        # expression = ...
        # return response_text, expression