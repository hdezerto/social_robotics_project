"""Preview multiple mock questions in the Furllionaire web GUI.

This helper starts the existing Flask-based `WebQuizGUI`, feeds in a few
predefined questions, and automatically advances through them so you can review
screen transitions without the full experiment controller or Furhat robot. You
can keep the countdown in sync with the cycling cadence by passing
`--time-limit` (defaults to the seconds-per-question value) and add a
`--delay-before-start` buffer so the browser has time to clear the intro screen
before the first mock question appears.
"""
from __future__ import annotations

import argparse
import threading
import time
from typing import Iterable, Sequence

from gui.web_gui import WebQuizGUI

# Static demo questions for quick previews. Edit or extend this list to test
# additional layouts, option lengths, or time limits.
MOCK_QUESTIONS: Sequence[dict] = (
    {
        "text": "Who is hosting tonight's Furllionaire special?",
        "options": [
            "Furhat the Fabulous",
            "Maria the Magnificent",
            "Both together",
            "A surprise guest",
        ],
        "answer": 1,
    },
    {
        "text": "Which lifeline would you pick first?",
        "options": [
            "Ask the Robot",
            "Call a Friend",
            "Audience Pulse",
            "Double Dip",
        ],
        "answer": 2,
    },
    {
        "text": "Finish the catchphrase: Who wants to be…",
        "options": [
            "A Furllionaire!",
            "An Engineer!",
            "An Astronaut!",
            "A Superstar!",
        ],
        "answer": 1,
    },
)


def cycle_questions(
    gui: WebQuizGUI,
    questions: Iterable[dict],
    seconds_per_question: float,
    endscreen_pause: float,
    delay_before_start: float,
) -> None:
    if delay_before_start > 0:
        print(f"Waiting {delay_before_start:.1f}s before showing the first question...")
        time.sleep(delay_before_start)

    for idx, question in enumerate(questions, start=1):
        gui.display_question(
            question["text"],
            list(question["options"]),
            question.get("answer"),
        )
        print(f"Showing mock question {idx}")
        time.sleep(seconds_per_question)

    gui.notify_experiment_finished()
    print("Preview finished — showing end screen.")
    time.sleep(endscreen_pause)
    gui.shutdown()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview multiple GUI questions.")
    parser.add_argument(
        "--seconds-per-question",
        type=float,
        default=8.0,
        help="How long each mock question stays on screen before the next one.",
    )
    parser.add_argument(
        "--endscreen-pause",
        type=float,
        default=4.0,
        help="Seconds to keep the thank-you screen visible before exiting.",
    )
    parser.add_argument(
        "--delay-before-start",
        type=float,
        default=5.0,
        help="Wait this many seconds before displaying the first question.",
    )
    parser.add_argument(
        "--time-limit",
        type=int,
        default=None,
        help="Seconds shown on the on-screen timer (defaults to seconds-per-question).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Run without opening a browser automatically.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    gui_time_limit = args.time_limit
    if gui_time_limit is None:
        gui_time_limit = max(1, int(round(args.seconds_per_question)))
    gui = WebQuizGUI(
        expected_questions=len(MOCK_QUESTIONS),
        time_limit=gui_time_limit,
        open_browser=not args.no_browser,
    )

    driver = threading.Thread(
        target=cycle_questions,
        args=(
            gui,
            MOCK_QUESTIONS,
            args.seconds_per_question,
            args.endscreen_pause,
            max(0.0, args.delay_before_start),
        ),
        daemon=True,
    )
    driver.start()

    try:
        gui.start()
    except KeyboardInterrupt:
        gui.notify_experiment_finished()
    finally:
        gui.shutdown()


if __name__ == "__main__":
    main()
