# LLM API Interface
# Communicates with LLM to generate tips and expressions
from mistralai import Mistral
import ast
import re
import json

class LLMAPI:
    def __init__(self, api_key, allowed_expressions=None):
        self.api_key = api_key
        self.model = "open-mistral-7b"#"mistral-small-latest"
        self.client = Mistral(api_key=api_key)

    def llm_generate_response(self, question, options, user_request, category = None):

        print("Question sent to LLM: ", user_request)

        response = None
        expression = None

        if category is None:
            category = self.interpret_text(question, options, user_request).lower()
            print("Question categorized as: ", category)

        if(category == "hint"):
            response = "hint"
            expression = "Smile"
        if(category == "fact"):
            response, expression = self.generate_question_response(question, options, user_request)
        if(category == "answer"):
            response = "I'm sorry, I can't give you the answer to the question."
            expression = "BrowFrown"
        if(category == "greeting"):
            response, expression = self.generate_greeting_response(user_request)

        return response, expression

    def provide_hint(self):
        return "", ""

    def generate_question_response(self, question, options, user_request):

        format = '{"tip": <tip>, "expression": <expression>}'
        system_prompt = f"""
            You are a Furhat robot helping a user with a quiz question: "{question}" with options "{options}".

            User question: {user_request}.

            Answer the user's question, but do NOT reveal the correct quiz answer.
            Respond in max 20 words in the following format: {format}. With:
            - tip: response to the question/advice for answering the quiz
            - expression: one of [BigSmile, Blink, BrowFrown, BrowRaise, CloseEyes, ExpressAnger, ExpressDisgust, ExpressFear, ExpressSad, GazeAway, Nod, Oh, OpenEyes, Roll, Shake, Smile, Surprise, Thoughtful, Wink]
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

        response_string = chat_response.choices[0].message.content
        response_dict = ast.literal_eval(response_string)

        print("response: ", response_dict["tip"])
        print("expression: ", response_dict["expression"])
        return response_dict["tip"], response_dict["expression"]

    def generate_greeting_response(self, greeting):
        format = '{"tip": <tip>, "expression": <expression>}'
        system_prompt = f"""
            You are a Furhat robot acting as a quiz master.
            Respond in max 20 words in the following format: {format}.

            With:
            - response: response to the user text
            - expression: one of [BigSmile, Blink, BrowFrown, BrowRaise, CloseEyes, ExpressAnger, ExpressDisgust, ExpressFear, ExpressSad, GazeAway, Nod, Oh, OpenEyes, Roll, Shake, Smile, Surprise, Thoughtful, Wink]

            User text: {greeting}
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
                    "content": greeting,
                },
            ]
        )

        response_string = chat_response.choices[0].message.content
        response_dict = ast.literal_eval(response_string)

        print("response: ", response_dict["tip"])
        print("expression: ", response_dict["expression"])
        return response_dict["tip"], response_dict["expression"]

    def interpret_text(self, question, options, user_request):

        format = '{"explanation": <explanation>, "category": <category>}'

        system_prompt = f"""
        You are a quiz master helping the user with the following quiz question: {question} and
        answers {options}. Please interpret the user_text and categorize it into one of following.
        Respond with the an explanation and the category (hint, fact, answer, irrelevant):
        - hint: The user is asking for a hint, a tip or help to answer the question.
        - answer: Answering the user's question would directly or indirectly give away the quiz answer. If in doubt, pick this option. This includes any question which directly or indir3ectly asks for the answer of the quiz question.
        - fact: The user is asking a question indirectly or directly related to any of the topics in the the quiz question or answer options. Most types of what/how/where/when questions should be in this category. Make sure the answering the question wouldn't give away the quiz answer! Then it should be "answer".
        - greeting: The user is saying hello, thank you or something similar.
        - irrelevant: Any other category.

        Use the following format:{format}

        Here is the user text: {user_request}
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
                    "content": user_request
                }
            ]
        )

        response = chat_response.choices[0].message.content
        response_dict = ast.literal_eval(response)

        print("LLM check relevance reasoning:", response_dict["explanation"])

        return response_dict["category"]
