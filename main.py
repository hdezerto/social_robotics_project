# Main entry point
# Initializes modules and starts experiment

from gui.web_gui import WebQuizGUI
from database.database import QuestionDatabase
from furhat_interface.furhat_api import FurhatAPI
from llm_backend.llm_api import LLMAPI
from controller.experiment_controller import ExperimentController
from logs.logger import Logger
import threading


def main():
    gui = WebQuizGUI(expected_questions=8)
    db = QuestionDatabase('database/questions.json')
    furhat = FurhatAPI("192.168.1.110")
    allowed_expressions = [
        "neutral",
        "happy",
        "excited",
        "concerned",
        "thinking",
        "confident",
        "encouraging",
    ]
    llm = LLMAPI(api_key='YOUR_API_KEY', allowed_expressions=allowed_expressions)
    logger = Logger('logs/experiment_log.csv')
    controller = ExperimentController(gui, db, furhat, llm, logger, check_relevance=True)

    controller_thread = threading.Thread(target=controller.run_experiment, name="experiment-controller", daemon=True)
    controller_thread.start()

    gui.start()

    controller_thread.join(timeout=2)


if __name__ == "__main__":
    main()
