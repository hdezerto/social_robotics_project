"""Mock Furhat client for local development.

Provides the same public methods as ``FurhatAPI`` but simply logs operations so
that the rest of the system can run without the physical robot or the
``furhat_realtime_api`` dependency present.
"""
from __future__ import annotations

import logging
import threading
from typing import Callable, Iterable, Optional


class MockFurhatAPI:
    def __init__(self, ip_address: str = "mock") -> None:
        self.ip_address = ip_address
        self._listen_callback: Optional[Callable[[str], None]] = None
        self._listening = threading.Event()
        logging.info("MockFurhatAPI initialized for %s", ip_address)

    def speak(self, text: str, wait: bool = True, abort: bool = True) -> None:
        logging.info("[Mock Furhat] speak(wait=%s, abort=%s): %s", wait, abort, text)

    def set_gesture(self, gesture_name: str, intensity: float = 1.0, duration: float = 1.0, wait: bool = False) -> None:
        logging.info(
            "[Mock Furhat] set_gesture(%s, intensity=%s, duration=%s, wait=%s)",
            gesture_name,
            intensity,
            duration,
            wait,
        )

    def set_expression(self, expression_name: str, intensity: float = 1.0) -> None:
        logging.info("[Mock Furhat] set_expression(%s, intensity=%s)", expression_name, intensity)

    def listen_speech(self, callback: Callable[[str], None], languages: Optional[Iterable[str]] = None) -> None:
        self._listen_callback = callback
        self._listening.set()
        logging.info("[Mock Furhat] listen_speech started (languages=%s)", languages)

    def stop_listening(self) -> None:
        self._listening.clear()
        logging.info("[Mock Furhat] stop_listening")

    def disconnect(self) -> None:
        self.stop_listening()
        logging.info("[Mock Furhat] disconnect")
