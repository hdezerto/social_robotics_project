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
    # Try to create the Furhat client. If the robot is unreachable the
    # constructor may raise (websocket timeout). Fall back to a silent stub
    # so the GUI and controller can run — we don't care about speaking now.
    try:
        furhat = FurhatAPI("192.168.1.175")
    except Exception:
        class _FurhatStub:
            def speak(self, text: str, wait: bool = False) -> None:
                return None

            def stop_listening(self) -> None:
                return None
            
            def listen_speech(self, callback):
                # No-op: in simplified mode we don't listen to speech.
                return None

            def set_expression(self, expression: str) -> None:
                # No-op placeholder for robot expressions.
                return None

        furhat = _FurhatStub()
    llm = LLMAPI(api_key=os.getenv("MISTRAL_LLM_API_KEY"))
    logger = Logger('logs/experiment_log.csv')
    controller = ExperimentController(gui, db, furhat, llm, logger, check_relevance=True)

    controller_thread = threading.Thread(target=controller.run_experiment, name="experiment-controller", daemon=True)
    controller_thread.start()

    gui.start()

    controller_thread.join(timeout=2)


if __name__ == "__main__":
    main()