
# best voice: Graham22k_HQ


# Main entry point
# Initializes modules and starts experiment

from gui.quiz_gui import QuizGUI
from database.database import QuestionDatabase
from furhat_interface.furhat_api import FurhatAPI
from llm_backend.llm_api import LLMAPI
from controller.experiment_controller import ExperimentController
from logs.logger import Logger
import os
import threading

def main():
    gui = QuizGUI()
    db = QuestionDatabase('database/questions.json')
    # $Env:MISTRAL_LLM_API_KEY="cORAOPjkqUnzqHEh4eSGQw7Q2Fffq5iF"
    
    #furhat = FurhatAPI("192.168.1.178")
    #furhat = FurhatAPI("192.168.1.110")
    furhat = FurhatAPI("192.168.1.144") # Virtual Furhat

    llm = LLMAPI(api_key=os.getenv("MISTRAL_LLM_API_KEY"))
    logger = Logger('logs/experiment_log.csv')
    controller = ExperimentController(gui, db, furhat, llm, logger, check_relevance=True)

    controller_thread = threading.Thread(target=controller.run_experiment, name="experiment-controller", daemon=True)
    controller_thread.start()

    gui.start()

    controller_thread.join(timeout=2)


if __name__ == "__main__":
    main()