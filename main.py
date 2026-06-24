# best voice: Graham22k_HQ

# ----------------- Hyperparameters -----------------
IP_ADDRESS = "192.168.1.144"  # Virtual Furhat
# IP_ADDRESS = "192.168.1.178"
# IP_ADDRESS = "192.168.1.110"

MODE = "reactive"
# MODE = "proactive"


# ----------------- Main Code -----------------

from gui.web_server import QuizWebServer
from database.database import QuestionDatabase
from furhat_interface.furhat_api import FurhatAPI
from llm_backend.llm_api import LLMAPI
from controller.experiment_controller import ExperimentController
from logs.logger import Logger
import os
import threading


def main():
    furhat_ip = os.getenv("FURHAT_IP", IP_ADDRESS)
    print(">>>>> Furllionaire Experiment. IP_ADDRESS:", furhat_ip, "MODE:", MODE, "<<<<<")

    gui = QuizWebServer()
    db = QuestionDatabase("database/questions.json")
    furhat = FurhatAPI(furhat_ip)
    llm = LLMAPI(api_key=os.getenv("MISTRAL_LLM_API_KEY"))
    logger = Logger("logs/experiment_log.csv")
    controller = ExperimentController(gui, db, furhat, llm, logger, mode=MODE, check_relevance=True)

    controller_thread = threading.Thread(target=controller.run_experiment, name="experiment-controller", daemon=True)
    controller_thread.start()

    gui.start()
    controller_thread.join(timeout=2)


if __name__ == "__main__":
    main()
