# LLM API Interface
# Communicates with LLM to generate tips and expressions
from mistralai import Mistral
import ast

class LLMAPI:
    def __init__(self, api_key, allowed_expressions=None):
        self.api_key = api_key
        self.model = "open-mistral-7b"#"mistral-small-latest"
        self.client = Mistral(api_key=api_key)


    def generate_assistant_response(self, question, options, user_request=None, check_relevance=False, fake_response=False):
        # For demo, return a dummy tip and expression
        print("Received request: ", user_request)
        if fake_response or self.api_key is None:
            tip = "Consider eliminating obviously wrong answers."
            expression = "smile"
            if self.api_key is None:
                print("No api key configured. Faking response. Check readme for how to configure it.")
            return tip, expression

        if check_relevance:

            if not("hint" in user_request or "help" in user_request):

                system_prompt = f"""
                You evaluate whether a user’s text is related to a quiz question or any of its answer options.
                Input fields: 
                - question: {question}, 
                - options: {options},
                - user_text: {user_request}
                Output:
                1) repeat user_text on the first line,
                2) give a 1–2 sentence explanation on the second line.
                3) "True" or "False" on the third line,

                Decision rules:
                - Return True if user_text directly or indirectly refers to the question topic or any option.
                - Indirect references count: synonyms, paraphrases, named entities, or “where/who/what”-type questions about an option.
                - If an option appears in user_text (e.g., option "London" and user_text "Where is London?"), return True.
                - Return False only if there is no meaningful lexical or conceptual overlap with the question or options.
                - If uncertain, prefer True.
                """

                chat_response = self.client.chat.complete(
                    model= self.model,
                    messages = [
                        {
                            "role": "system",
                            "content": system_prompt,                   
                        },
                        {
                            "role": "user",
                            "content": user_request,
                        },
                    ]
                )

                print("RELEVANCE: ", chat_response.choices[0].message.content)
                    
                if "False" in chat_response.choices[0].message.content:
                    return None, None
        
        format = '{"tip": <tip>, "expression": <expression>}'
        
        system_prompt = f"""
            You are a Furhat robot helping a user with a quiz question: "{question}" with options "{options}". 
            
            Give the user strategic advice only, do not reveal the answer. 
            Respond in max 20 words in the following format: {format}. With:
            - tip: advice for text-to-speech 
            - expression: one of [BigSmile, Blink, BrowFrown, BrowRaise, CloseEyes, ExpressAnger, ExpressDisgust, ExpressFear, ExpressSad, GazeAway, Nod, Oh, OpenEyes, Roll, Shake, Smile, Surprise, Thoughtful, Wink] 
            """
        
        if user_request is None:
           user_request = "Help me with the question!"

        chat_response = self.client.chat.complete(
            model= self.model,
            messages = [
                {
                    "role": "system",
                    "content": system_prompt,                   
                },
                {
                    "role": "user",
                    "content": user_request,
                },
            ]
        )

        print("Prompt sent")

        response_string = chat_response.choices[0].message.content
        response_dict = ast.literal_eval(response_string)

        print("response: ", response_dict["tip"])
        print("expression: ", response_dict["expression"])
        return response_dict["tip"], response_dict["expression"]
