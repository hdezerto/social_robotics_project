"""Main entry point for the Furhat quiz experiment."""

from __future__ import annotations

import argparse
import logging
import os
import threading

from controller.experiment_controller import ExperimentController
from database.database import QuestionDatabase
from gui.web_gui import WebQuizGUI
from llm_backend.llm_api import LLMAPI
from logs.logger import Logger

ALLOWED_EXPRESSIONS = [
    "neutral",
    "happy",
    "excited",
    "concerned",
    "thinking",
    "confident",
    "encouraging",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Furhat quiz experiment.")
    parser.add_argument("--furhat-ip", default="192.168.1.110", help="IP address of the Furhat robot.")
    parser.add_argument(
        "--mock-furhat",
        action="store_true",
        help="Use the mock Furhat API so the UI can run without the robot or its SDK.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for the web GUI server.")
    parser.add_argument("--port", type=int, default=5000, help="Port for the web GUI server.")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open the GUI in a browser.")
    parser.add_argument(
        "--questions-file",
        default="database/questions.json",
        help="Path to the questions JSON file.",
    )
    parser.add_argument(
        "--expected-questions",
        type=int,
        default=8,
        help="Number of questions to show in the counter at the top of the GUI.",
    )
    parser.add_argument(
        "--time-limit",
        type=int,
        default=60,
        help="Per-question countdown shown to the user.",
    )
    parser.add_argument(
        "--log-file",
        default="logs/experiment_log.csv",
        help="Path to the CSV experiment log.",
    )
    parser.add_argument(
        "--disable-relevance-check",
        action="store_true",
        help="Disable LLM relevance filtering.",
    )
    parser.add_argument(
        "--dev-exit-after",
        type=float,
        default=None,
        help="Automatically shut down after N seconds (useful for local smoke tests).",
    )
    return parser.parse_args()


def create_furhat(use_mock: bool, ip: str):
    if use_mock:
        from furhat_interface.mock_furhat_api import MockFurhatAPI

        return MockFurhatAPI(ip)

    from furhat_interface.furhat_api import FurhatAPI

    return FurhatAPI(ip)


def schedule_dev_exit(gui: WebQuizGUI, furhat: object, seconds: float) -> None:
    def _shutdown() -> None:
        logging.warning("Dev exit triggered after %.2fs", seconds)
        try:
            gui.notify_experiment_finished()
        except Exception:
            pass
        gui.shutdown()
        try:
            furhat.stop_listening()
        except Exception:
            pass
        os._exit(0)

    timer = threading.Timer(seconds, _shutdown)
    timer.daemon = True
    timer.start()


def main() -> None:
    args = parse_args()

    gui = WebQuizGUI(
        expected_questions=args.expected_questions,
        time_limit=args.time_limit,
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
    )
    db = QuestionDatabase(args.questions_file)
    furhat = create_furhat(args.mock_furhat, args.furhat_ip)
    llm = LLMAPI(api_key="YOUR_API_KEY", allowed_expressions=ALLOWED_EXPRESSIONS)
    logger = Logger(args.log_file)
    controller = ExperimentController(
        gui,
        db,
        furhat,
        llm,
        logger,
        check_relevance=not args.disable_relevance_check,
    )

    controller_thread = threading.Thread(
        target=controller.run_experiment,
        name="experiment-controller",
        daemon=True,
    )
    controller_thread.start()

    if args.dev_exit_after:
        schedule_dev_exit(gui, furhat, args.dev_exit_after)

    gui.start()

    controller_thread.join(timeout=2)


if __name__ == "__main__":
    main()
