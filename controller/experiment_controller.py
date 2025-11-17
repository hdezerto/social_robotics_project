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
            user_answer = self.gui.get_user_answer()
            self.logger.log_event({"event_type": "user_answer", "details": user_answer})
            help_requested = False
            if mode == "reactive":
                ask_help = input("Do you want help? (y/n): ").strip().lower()
                if ask_help == "y":
                    help_requested = True
            elif mode == "proactive":
                # Simulate inactivity (for demo, just ask)
                inactive = input("Were you inactive for 10s? (y/n): ").strip().lower()
                if inactive == "y":
                    help_requested = True
            if help_requested:
                tip, expression = self.llm.get_tip_and_expression(question["question"], question["options"])
                self.furhat.speak(tip)
                self.furhat.set_expression(expression)
                self.logger.log_event({"event_type": "robot_tip", "details": tip})
            print("---")
        print("Experiment finished.")
        self.logger.log_event({"event_type": "experiment_finished", "details": "done"})
