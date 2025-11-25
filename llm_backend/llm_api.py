# LLM API Interface
# Communicates with LLM to generate tips and expressions
from mistralai import Mistral
import ast

class LLMAPI:
    def __init__(self, api_key, allowed_expressions=None):
        self.api_key = api_key
        self.model = "open-mistral-7b"#"mistral-small-latest"
        self.client = Mistral(api_key=api_key)

    def llm_generate_response(self, question, options, user_request, category = None):
        
        response = None
        expression = None

        if category is None:
            category = self.interpret_text(self, question, options, user_request).lower()

        if(category == "hint"):
            response = self.provide_hint()
            expression = "Smile"
        if(category == "fact"):
            response, expression = self.generate_question_response(self, question, options, user_request)
        if(category == "answer"):
            response = "I'm sorry, I can't give you the answer to the question."
            expression = "BrowFrown"
        if(category == "greeting"):
            response, expression = self.generate_greeting_response(self, question, options, user_request)

        return response, expression
    
    def provide_hint():
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
            
            User question: {user_request}.

            Answer the user's question, but do not reveal the quiz answer. 
            Respond in max 20 words in the following format: {format}. With:
            - tip: response to the question/advice for answering the quiz
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


    def interpret_text(self, question, options, user_request):
        
        format = '{"explanation": <explanation>, "category": <category>}'

        system_prompt = f"""
        You are a quiz master helping the user with the following quiz question: {question} and 
        answers {options}. Please interpret the user_text and categorize it into one of following.
        Respond with the an explanation and the category (hint, fact, answer, irrelevant):
        - hint: The user is asking for a hint, a tip or help to answer the question.
        - fact: The user is asking a question directly or indirectly related to any of the topics from the the quiz question or answer options. Most types of what/how/where/when questions should be in this category.
        - answer: The user is asking a question which would give away the answer.
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