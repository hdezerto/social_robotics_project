import logging
import threading
import time
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Union

from flask import Flask, jsonify, request, send_from_directory


class WebQuizGUI:
    """Serves the Furllionaire web UI and bridges it with the experiment controller."""

    def __init__(
        self,
        static_dir: Optional[Union[Path, str]] = None,
        host: str = "127.0.0.1",
        port: int = 5000,
        open_browser: bool = True,
        expected_questions: Optional[int] = 8,
        time_limit: int = 60, # seconds per question
    ) -> None:
        if static_dir is None:
            static_dir = Path(__file__).resolve().parent / "web_client"
        self.static_dir = Path(static_dir).resolve()
        if not self.static_dir.exists():
            raise FileNotFoundError(f"Static GUI directory not found: {self.static_dir}")
        self.host = host
        self.port = port
        self.open_browser = open_browser
        self.expected_questions = expected_questions
        self.time_limit = time_limit

        self.app = Flask(__name__, static_folder=str(self.static_dir), static_url_path="")
        self._question_lock = threading.Lock() # Protects access to current question state
        self._current_question: Optional[Dict[str, object]] = None
        self._question_counter = 0 # Tracks which quesstion is being shown
        self._answer_event = threading.Event() # Used to signal when an answer is received
        self._answer_value: Optional[str] = None # Stores the received answer
        self._finished = False # Indicates if the experiment is finished
        self._server_thread: Optional[threading.Thread] = None # Thread running the Flask server
        self._stop_event = threading.Event() # Used to signal server shutdown

        self._register_routes() # Register Flask routes

    # ------------------------------------------------------------------
    # Public API expected by ExperimentController
    # ------------------------------------------------------------------
    def display_question(self, question_text: str, options: List[str]) -> None:
        with self._question_lock:
            self._question_counter += 1
            self._current_question = {
                "id": self._question_counter,
                "text": question_text,
                "options": options,
                "question_number": self._question_counter,
                "total_questions": self.expected_questions,
                "time_limit": self.time_limit,
                "timestamp": time.time(),
            }
            self._finished = False
            self._answer_event = threading.Event()
            self._answer_value = None

    def get_user_answer(self) -> Optional[str]:
        self._answer_event.wait() # Blocking event wait until answer is received
        return self._answer_value

    def notify_experiment_finished(self) -> None:
        with self._question_lock:
            self._finished = True
            self._current_question = None

    def start(self) -> None:
        self._ensure_server()
        try:
            while not self._stop_event.is_set():
                if self._server_thread is None or not self._server_thread.is_alive():
                    break
                self._server_thread.join(timeout=0.5)
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt received, shutting down WebQuizGUI.")
            self._stop_event.set()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_server(self) -> None:
        if self._server_thread and self._server_thread.is_alive():
            return
        self._server_thread = threading.Thread(target=self._run_app, name="web-gui-server", daemon=True)
        self._server_thread.start()
        if self.open_browser:
            threading.Thread(target=self._open_browser_when_ready, daemon=True).start()

    def _run_app(self) -> None:
        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

    def _open_browser_when_ready(self) -> None:
        # Give the server a moment to start before opening the browser.
        time.sleep(1.0)
        url = f"http://{self.host}:{self.port}"
        try:
            webbrowser.open(url)
        except Exception as exc:  # pragma: no cover - best effort only
            logging.warning("Unable to open web browser for GUI: %s", exc)

    def _register_routes(self) -> None:
        @self.app.route("/")
        def index() -> object:
            return send_from_directory(str(self.static_dir), "index.html")

        @self.app.route("/api/question", methods=["GET"])
        def api_question() -> object:
            with self._question_lock:
                if not self._current_question:
                    status = "finished" if self._finished else "waiting"
                    return jsonify({"status": status, "question": None, "finished": self._finished})
                question_payload = dict(self._current_question)
                answered = self._answer_event.is_set()
            return jsonify(
                {
                    "status": "ready",
                    "question": question_payload,
                    "answered": answered,
                    "finished": self._finished,
                }
            )

        @self.app.route("/api/answer", methods=["POST"])
        def api_answer() -> object:
            with self._question_lock:
                if not self._current_question:
                    return jsonify({"error": "no_active_question"}), 409
                data = request.get_json(silent=True) or {}
                incoming_id = data.get("question_id")
                choice = data.get("choice")
                if incoming_id != self._current_question["id"]:
                    return jsonify({"error": "stale_question"}), 409
                if choice is None:
                    return jsonify({"error": "missing_choice"}), 400
                if self._answer_event.is_set():
                    return jsonify({"error": "already_answered"}), 409
                try:
                    choice_as_int = int(choice)
                except (TypeError, ValueError):
                    return jsonify({"error": "invalid_choice"}), 400
                if choice_as_int < 1 or choice_as_int > len(self._current_question["options"]):
                    return jsonify({"error": "choice_out_of_range"}), 400
                self._answer_value = str(choice_as_int)
                self._answer_event.set()
            return jsonify({"status": "received"})
