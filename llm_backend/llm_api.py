# LLM API Interface
# Communicates with LLM to generate tips and expressions
from mistralai import Mistral
import ast

class LLMAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model = "open-mistral-7b" #"mistral-small-latest"
        self.client = Mistral(api_key=api_key)


    def get_tip_and_expression(self, question, options, user_request=None, fake_response=True):
        # For demo, return a dummy tip and expression
        if fake_response:
            tip = "Consider eliminating obviously wrong answers."
            expression = "smile"
            return tip, expression

        chat_response = self.client.chat.complete(
            model= self.model,
            messages = [
                {
                    "role": "system",
                    "content": "You are a furhat robot providing assistance to a user who is \
                        answering a quiz. It is very important that you do not give away the \
                        answer to the quiz directly, \
                        instead give strategic advice on how the user could think. Please \
                        write a response with max 20 words to the given question in the following format: \
                        {\"tip\": <tip>, \"expression\": <expression>}, where tip is \
                        your advice to the user in a format that works for text-to-speech, \
                        and expression if you chosen appropriate expression out of the \
                        following:\
                            BigSmile, Blink, BrowFrown, BrowRaise, CloseEyes, ExpressAnger \
                            ExpressDisgust, ExpressFear, ExpressSad, GazeAway, Nod, Oh \
                            OpenEyes, Roll, Shake, Smile, Surprise, Thoughtful, Wink"                        
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
