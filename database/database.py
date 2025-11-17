# Database functions for quiz questions
import json
import random

class QuestionDatabase:
    def __init__(self, path):
        with open(path, 'r') as f:
            self.data = json.load(f)
        # Track used question indices by difficulty
        self.used_indices = {"easy": set(), "medium": set(), "hard": set()}

    def get_random_question(self, difficulty):
        questions = self.data.get(difficulty, [])
        if not questions:
            return None
        # Get unused indices
        all_indices = set(range(len(questions)))
        unused_indices = list(all_indices - self.used_indices[difficulty])
        if not unused_indices:
            return None
        selected_idx = random.choice(unused_indices)
        self.used_indices[difficulty].add(selected_idx)
        return questions[selected_idx]

    def reset_used_questions(self):
        for diff in self.used_indices:
            self.used_indices[diff] = set()
