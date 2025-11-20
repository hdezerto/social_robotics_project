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

    def _truncate(self, text, max_words):
        if not text:
            return text
        words = text.strip().split()
        if len(words) <= max_words:
            return text.strip()
        return " ".join(words[:max_words]).rstrip() + "..."

    def _truncate_sentence(self, text, max_words):
        """
        Return one or more full sentences whose combined word count does not exceed max_words.
        If the first sentence alone exceeds max_words, return the full first sentence (no mid-sentence cut).
        """
        if not text:
            return text
        text = text.strip()
        # split into sentences, keeping punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if not sentences:
            return self._truncate(text, max_words)
        selected = []
        total = 0
        for s in sentences:
            wc = len(s.split())
            if total + wc <= max_words:
                selected.append(s.strip())
                total += wc
            else:
                # if nothing selected yet, return the full first sentence (avoid mid-sentence cut)
                if not selected:
                    return sentences[0].strip()
                break
        return " ".join(selected).strip()

    def generate_assistant_response(self, question, options, user_request=None, check_relevance=False, fake_response=False):
        # For demo, return a dummy tip and expression
        print("Received request: ", user_request)
        if fake_response or self.api_key is None:
            tip = "Consider eliminating obviously wrong answers."
            expression = "smile"
            if self.api_key is None:
                print("No api key configured. Faking response. Check readme for how to configure it.")
            return tip, expression

        user_text = (user_request or "").strip()
        user_text_lower = user_text.lower()

        # treat explicit help/hint requests as always relevant (bypass relevance classifier)
        is_help_request = bool(re.search(r'\b(help|hint|another hint|give me a hint)\b', user_text_lower))
        if is_help_request:
            print("Detected explicit help/hint request — skipping relevance check and returning a tip.")
        # detect explicit requests to reveal the quiz's correct answer
        is_reveal_request = bool(re.search(
            r"\b(correct answer|what(?:'s| is)? the answer|tell me the answer|reveal the answer|which (?:is|one) is correct|give me the answer)\b",
            user_text_lower
        ))

        if is_reveal_request:
            refusal = "I'm not allowed to reveal the correct answer to the quiz."
            # make the refusal available as written output for GUI/logging
            self.last_written_answer = refusal
            print("REFUSE: ", refusal)
            return refusal, None

        # simple heuristic: treat as factual if starts with interrogative or contains '?'
        is_factual_question = bool(re.match(r'^(what|who|where|when|why|how|define|describe)\b', user_text_lower)) or user_text.endswith('?')

        # --- new: handle factual questions with a factual-answer prompt and return the explanation ---
        if is_factual_question:
            factual_system = (
                "You are a helpful assistant. Provide a concise (1-2 sentence) factual answer to the user's question. "
                "Do NOT try to give quiz hints or reveal any quiz answers — just answer the factual question."
            )
            chat_response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": factual_system},
                    {"role": "user", "content": user_request},
                ]
            )
            factual_answer = chat_response.choices[0].message.content.strip()

            # make the factual answer available as written output for GUI/logging
            self.last_written_answer = factual_answer
            

            # return a shortened spoken version (keep full written)
            spoken = self._truncate_sentence(factual_answer, max_words=15)
            print("WRITTEN: ", spoken)

            return spoken, None
        # --- end new ---

        if check_relevance and user_text:
            # only run relevance check for non-help messages
            if not is_help_request:
                # run relevance check (same prompt as before)
                system_prompt = f"""
                    You evaluate whether a user’s text is related to a quiz question or any of its answer options.
                    Input fields: 
                    - question: {question}, 
                    - options: {options},
                    - user_text: {user_request}
                    Output:
                    1) repeat user_text on the first line,
                    2) give a 1–2 sentence explanation on the second line (RETURN THE EXPLANATION ONLY — do NOT prefix with meta-comments such as "Mention that", "Note that", "You should", "Try to", etc.),
                    3) "True" or "False" on the third line,
                    Decision rules:
                    - Return True if user_text directly or indirectly refers to the question topic or any option.
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

                relevance_text = chat_response.choices[0].message.content
                print("RELEVANCE: ", relevance_text)

                # try to parse lines: first = repeat, second = explanation, third = True/False
                lines = [l.strip() for l in relevance_text.splitlines() if l.strip()]
                verdict = None
                explanation = None
                if len(lines) >= 1:
                    # last line likely contains True/False
                    verdict = lines[-1]
                if len(lines) >= 2:
                    # take the second line as explanation if present
                    explanation = lines[1] if len(lines) > 1 else None

                # clean common prefatory phrases the model may add (e.g., "Mention that ...")
                if explanation:
                    explanation = re.sub(
                        r'^\s*(?:mention that|note that|say that|you should|please note(?: that)?|it could be|try to)\s*[:,-]?\s*',
                        '',
                        explanation,
                        flags=re.IGNORECASE
                    ).strip()

                if verdict and "False" in verdict:
                    return None, None

                # If user asked a factual question, prefer returning the explanation from relevance check
                if is_factual_question and explanation:
                    # make full explanation available for GUI/logging
                    self.last_written_answer = explanation
                    # return a shortened spoken version (keep full written)
                    spoken_expl = self._truncate_sentence(explanation, max_words=30)
                    return spoken_expl, None
            else:
                # when user explicitly asks for help/hint, assume relevant
                verdict = "True"
                explanation = None
                relevance_text = "Help request - forced relevant"
                print("RELEVANCE: forced True for help/hint")

        # existing quiz-tip prompt (used for hints/help)
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
        # keep the existing parsing but be defensive
        try:
            response_dict = ast.literal_eval(response_string)
        except Exception:
            # fallback: try JSON
            try:
                response_dict = json.loads(response_string)
            except Exception:
                # if parsing fails, return a truncated raw string as tip
                spoken = self._truncate_sentence(response_string, max_words=20)
                # store full as written
                self.last_written_answer = response_string.strip()
                return spoken, None

        tip_full = (response_dict.get("tip") or "").strip()
        expr = response_dict.get("expression")
        # store full tip for written display, but shorten spoken tip
        self.last_written_answer = tip_full
        tip_spoken = self._truncate_sentence(tip_full, max_words=20)
        print("response (full): ", tip_full)
        print("expression: ", expr)
        return tip_spoken, expr
