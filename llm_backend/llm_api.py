# LLM API Interface
# Communicates with LLM to generate tips and expressions

class LLMAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        # Placeholder: Initialize LLM client here

    def generate_assistant_response(self, question, options, user_request=None, check_relevance=False):
        """
        Generate a helpful assistant response and facial expression for the robot using the LLM.
        Guardrails: Do NOT disclose the correct answer. Always return a response and a facial expression tag.
        If check_relevance is True, always return the response. If False, only return if the LLM found it relevant.
        """
        prompt = (
            f"You are an assistant helping a user answer a multiple-choice question. "
            f"Do NOT disclose the correct answer. "
            f"Instead, provide a helpful response and a suggested facial expression for the robot. "
            f"Also, evaluate if the user's request is a real question about the displayed question/options or just noise/random words. "
            f"Format your response as: RESPONSE: <response>\\nEXPRESSION: <expression>\\nRELEVANT: <True/False>. "
            f"\\nQuestion: {question}\\nOptions: {options}\\nUser request: {user_request if user_request else ''}"
        )
        # Placeholder: Call LLM API with the constructed prompt
        # response = self.client.generate_response(prompt)
        # Example response string:
        # RESPONSE: Here is a helpful hint.
        # EXPRESSION: happy
        # RELEVANT: True

        # For demonstration, use a sample response string
        response = "RESPONSE: This is a placeholder response.\nEXPRESSION: neutral\nRELEVANT: True"

        # Parse the response
        response_text, expression, relevant = None, None, None
        lines = response.split('\n')
        for line in lines:
            if line.startswith("RESPONSE:"):
                response_text = line[len("RESPONSE:"):].strip()
            elif line.startswith("EXPRESSION:"):
                expression = line[len("EXPRESSION:"):].strip()
            elif line.startswith("RELEVANT:"):
                relevant_str = line[len("RELEVANT:"):].strip()
                relevant = relevant_str.lower() == "true"

        if check_relevance:
            # Always return response, expression, relevant
            return response_text, expression, relevant
        else:
            # Only return if relevant
            if relevant:
                return response_text, expression
            else:
                return None, None