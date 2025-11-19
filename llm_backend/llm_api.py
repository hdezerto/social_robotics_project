# LLM API Interface
# Communicates with LLM to generate tips and expressions
from mistralai import Mistral
import ast

class LLMAPI:
    def __init__(self, api_key, allowed_expressions=None):
        self.api_key = api_key
        self.model = "open-mistral-7b" #"mistral-small-latest"
        self.client = Mistral(api_key=api_key)


    def generate_assistant_response(self, question, options, user_request=None, check_relevance=False, fake_response=True):
        # For demo, return a dummy tip and expression
        if fake_response:
            tip = "Consider eliminating obviously wrong answers."
            expression = "smile"
            return tip, expression

        if check_relevance:
            system_prompt = f"""
            Is the user text related to asking for help or to quiz questions? 
            Respond with ONLY "True" if yes, and else ONLY "False".
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

            if chat_response.choices[0].message.content == "False":
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

        response_string = chat_response.choices[0].message.content
        response_dict = ast.literal_eval(response_string)

        return response_dict["tip"], response_dict["expression"]
