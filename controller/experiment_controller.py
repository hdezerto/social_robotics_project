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

            help_requested = False
            if mode == "reactive":
                ask_help = input("Do you want help? (y/n): ").strip().lower()
                if ask_help == "y":
                    help_requested = True
            elif mode == "proactive":
                # Offer help every 10 seconds of inactivity until user answers or 60 seconds pass
                def proactive_help_loop():
                    elapsed = 0
                    while not answer_event.is_set() and elapsed < 60:
                        time.sleep(10)
                        elapsed += 10
                        if not answer_event.is_set():
                            tip, expression = self.llm.get_tip_and_expression(question["question"], question["options"])
                            self.furhat.speak(tip)
                            self.furhat.set_expression(expression)
                            self.logger.log_event({"event_type": "robot_tip", "details": tip})

                help_thread = threading.Thread(target=proactive_help_loop)
                help_thread.start()
                answer_thread.join()  # Wait for answer or timeout
                help_thread.join()    # Ensure help thread finishes
            print("---")
        print("Experiment finished.")
        self.logger.log_event({"event_type": "experiment_finished", "details": "done"})
