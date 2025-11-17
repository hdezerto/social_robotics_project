# Main entry point
# Initializes modules and starts experiment

from gui.quiz_gui import QuizGUI
from database.database import QuestionDatabase
from furhat_interface.furhat_api import FurhatAPI
from llm_backend.llm_api import LLMAPI
from controller.experiment_controller import ExperimentController
from logs.logger import Logger


def main():
    gui = QuizGUI()
    db = QuestionDatabase('database/questions.json')
    furhat = FurhatAPI()
    llm = LLMAPI(api_key='YOUR_API_KEY')
    logger = Logger('logs/experiment_log.csv')
    controller = ExperimentController(gui, db, furhat, llm, logger)

    # Start the GUI event loop in a way that allows experiment to run
    import threading
    gui_thread = threading.Thread(target=gui.start)
    gui_thread.daemon = True
    gui_thread.start()

    controller.run_experiment() # Runs in the main thread


if __name__ == "__main__":
    main()
