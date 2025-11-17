# Database functions for quiz questions
import json
import random

class QuestionDatabase:
    def __init__(self, path):
        with open(path, 'r') as f:
            self.data = json.load(f)

    def get_random_question(self, difficulty):
        questions = self.data.get(difficulty, [])
        if not questions:
            return None
        # Each question should be a dict: {"question": str, "options": [str], "answer": int}
        return random.choice(questions)
