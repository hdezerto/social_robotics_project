"""Minimal adapter providing `QuizGUI` for simplified `main.py`.

This small wrapper constructs the existing WebQuizGUI with sane
defaults so other modules can import `QuizGUI` and use it the same
way they would a very small GUI class. All attribute access is
delegated to the internal `WebQuizGUI` instance so the wrapper is
transparent for controller code.
"""
from __future__ import annotations

from typing import Any
from .web_gui import WebQuizGUI


class QuizGUI:
    """Lightweight adapter around `WebQuizGUI`.

    Usage:
        gui = QuizGUI()
        gui.start()

    The constructor accepts a few optional parameters in case you
    want to override the defaults used by the original main.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5000,
        expected_questions: int = 8,
        time_limit: int = 60,
        open_browser: bool = True,
    ) -> None:
        self._web = WebQuizGUI(
            expected_questions=expected_questions,
            time_limit=time_limit,
            host=host,
            port=port,
            open_browser=open_browser,
        )

    def start(self) -> Any:
        """Start the GUI server (delegates to WebQuizGUI.start)."""
        return self._web.start()

    def shutdown(self) -> None:
        """Attempt to shut down the underlying web GUI if supported."""
        if hasattr(self._web, "shutdown"):
            try:
                return self._web.shutdown()
            except Exception:
                # best-effort shutdown for compatibility
                return None

    def notify_experiment_finished(self) -> None:
        """Delegate notification method if implemented by WebQuizGUI."""
        if hasattr(self._web, "notify_experiment_finished"):
            try:
                return self._web.notify_experiment_finished()
            except Exception:
                return None

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - simple delegator
        """Fallback: delegate any other attribute access to the WebQuizGUI."""
        return getattr(self._web, name)

