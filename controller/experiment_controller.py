# Experiment Controller
# Manages experiment flow and interaction modes


class ExperimentController:
    def __init__(self, gui, db, furhat, llm, logger, check_relevance=True):
        self.gui = gui
        self.db = db
        self.furhat = furhat
        self.llm = llm
        self.logger = logger
        self.answer_event = None
        self.current_question = None
        self.check_relevance = check_relevance
        self.furhat.listen_speech(self.handle_transcribed_speech)


    def run_experiment(self):
        import threading
        import time
        print("Starting experiment...")

        num_questions = 8
        difficulties = ["easy"]*2 + ["medium"]*4 + ["hard"]*2

        mode = "reactive"  # or "proactive"

        for i in range(num_questions):
            difficulty = difficulties[i]
            question = self.db.get_random_question(difficulty)
            if not question:
                print(f"No {difficulty} questions available.")
                continue
            self.gui.display_question(question["question"], question["options"])
            self.logger.log_event({"event_type": "question_displayed", "details": question["question"]})

            self.answer_event = threading.Event()
            self.current_question = question
            user_answer = [None]

            answer_thread = threading.Thread(target=self.get_answer, args=(user_answer, self.answer_event))
            answer_thread.start()

            if mode == "proactive":
                help_thread = threading.Thread(target=self.proactive_help_loop, args=(self.answer_event, question))
                help_thread.daemon = True
                help_thread.start()

            answered_in_time = self.answer_event.wait(timeout=60)
            if mode == "proactive":
                help_thread.join()
            answer_thread.join()

            if not answered_in_time:
                print("Time's up! No answer received.")
                self.logger.log_event({"event_type": "timeout", "details": "No answer in 60 seconds"})
                user_answer_val = None
            else:
                user_answer_val = user_answer[0]
                self.logger.log_event({"event_type": "user_answer", "details": user_answer_val})

            print("---")
        print("Experiment finished.")
        self.logger.log_event({"event_type": "experiment_finished", "details": "done"})
    
    
    def handle_transcribed_speech(self, user_speech):
        # Only process if answer window is open and question is set
        if self.answer_event and self.current_question and not self.answer_event.is_set():
            response, expression, relevant = self.llm.generate_assistant_response(
                self.current_question["question"], self.current_question["options"], user_request=user_speech, check_relevance=self.check_relevance)
            if self.check_relevance:
                # Always speak if response is present
                if response:
                    self.furhat.speak(response)
                    self.furhat.set_expression(expression)
                    self.logger.log_event({"event_type": "robot_response", "details": response})
            else:
                # Only speak if relevant
                if relevant:
                    self.furhat.speak(response)
                    self.furhat.set_expression(expression)
                    self.logger.log_event({"event_type": "robot_response", "details": response})
                else:
                    self.logger.log_event({"event_type": "robot_noise_ignored", "details": user_speech})


    def get_answer(self, user_answer, answer_event):
        user_answer[0] = self.gui.get_user_answer()
        answer_event.set()


    def proactive_help_loop(self, answer_event, question):
        import time
        elapsed = 0
        hint_index = 0
        hints = question.get("hints", [])
        ask_first = True
        while not answer_event.is_set() and elapsed < 60:
            time.sleep(10)
            elapsed += 10
            if not answer_event.is_set():
                if ask_first:
                    tip = "Do you need help?"
                    ask_first = False
                else:
                    if hint_index < len(hints):
                        tip = hints[hint_index]
                        hint_index += 1
                    else:
                        tip = "Do you need help?"
                    ask_first = True
                self.furhat.speak(tip)
                self.furhat.set_expression("neutral")
                self.logger.log_event({"event_type": "robot_tip", "details": tip})
