# Experiment Controller
# Manages experiment flow and interaction modes

class ExperimentController:
    def __init__(self, gui, db, furhat, llm, logger):
        self.gui = gui
        self.db = db
        self.furhat = furhat
        self.llm = llm
        self.logger = logger

    def run_experiment(self):
        import threading
        import time
        print("Starting experiment...")

        num_questions = 8
        difficulties = ["easy"]*2 + ["medium"]*4 + ["hard"]*2

        mode = input("Choose mode (reactive/proactive): ").strip().lower()
        for i in range(num_questions):
            difficulty = difficulties[i]
            question = self.db.get_random_question(difficulty)
            if not question:
                print(f"No {difficulty} questions available.")
                continue
            self.gui.display_question(question["question"], question["options"])
            self.logger.log_event({"event_type": "question_displayed", "details": question["question"]})

            # Timer for user answer (60 seconds)
            answer_event = threading.Event()
            user_answer = [None]

            def get_answer():
                user_answer[0] = self.gui.get_user_answer()
                answer_event.set()

            answer_thread = threading.Thread(target=get_answer)
            answer_thread.start()
            answered_in_time = answer_event.wait(timeout=60)
            if not answered_in_time:
                print("Time's up! No answer received.")
                self.logger.log_event({"event_type": "timeout", "details": "No answer in 60 seconds"})
                user_answer_val = None
            else:
                user_answer_val = user_answer[0]
                self.logger.log_event({"event_type": "user_answer", "details": user_answer_val})

            # Handle user speech input for help (reactive and proactive)
            def handle_user_speech(user_speech, question):
                # Send user speech to LLM for assistant response (with guardrails)
                response, expression = self.llm.generate_assistant_response(question["question"], question["options"], user_request=user_speech)
                self.furhat.speak(response)
                self.furhat.set_expression(expression)
                self.logger.log_event({"event_type": "robot_response", "details": response})

            help_requested = False
            if mode == "reactive":
                # In a real system, this would be triggered by Furhat receiving user speech
                ask_help = input("Did the user ask for help? (y/n): ").strip().lower()
                if ask_help == "y":
                    # Simulate receiving user speech
                    user_speech = input("Enter transcribed user speech: ")
                    handle_user_speech(user_speech, question)
                    help_requested = True
            elif mode == "proactive":
                # Offer hint from database every 10 seconds of inactivity until user answers or 60 seconds pass
                def proactive_help_loop():
                    elapsed = 0
                    hint_index = 0
                    hints = question.get("hints", [])
                    while not answer_event.is_set() and elapsed < 60:
                        time.sleep(10)
                        elapsed += 10
                        if not answer_event.is_set():
                            if hint_index < len(hints):
                                tip = hints[hint_index]
                                hint_index += 1
                            else:
                                tip = "Do you need help?"
                            self.furhat.speak(tip)
                            self.furhat.set_expression("neutral")
                            self.logger.log_event({"event_type": "robot_tip", "details": tip})

                help_thread = threading.Thread(target=proactive_help_loop)
                help_thread.start()
                answer_thread.join()  # Wait for answer or timeout
                help_thread.join()    # Ensure help thread finishes
                # After hint, if user asks a question, handle speech
                ask_help = input("Did the user ask for help during proactive hints? (y/n): ").strip().lower()
                if ask_help == "y":
                    user_speech = input("Enter transcribed user speech: ")
                    handle_user_speech(user_speech, question)
            print("---")
        print("Experiment finished.")
        self.logger.log_event({"event_type": "experiment_finished", "details": "done"})
