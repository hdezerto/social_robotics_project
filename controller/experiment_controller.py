# Experiment Controller
# Manages experiment flow and interaction modes

import threading
import time
import re
import logging


class ProactiveHelpStateMachine:
    """Simple three-state machine that manages proactive help prompts."""

    WAIT_STATE = "wait_state"
    OFFER_HINT = "offer_hint"
    GIVE_HINT = "give_hint"

    def __init__(self, controller, wait_timeout=18.0):
        self.controller = controller
        self.wait_timeout = wait_timeout
        self._state_lock = threading.Lock()
        self._current_state = self.WAIT_STATE
        self._stop_event = threading.Event()
        self._wait_timer = None
        self._response_timer = None
        self._answer_event = None

    def start(self, answer_event):
        """Initialize the machine for a new question."""
        self._cancel_wait_timer()
        self._stop_event.clear()
        self._answer_event = answer_event
        with self._state_lock:
            self._current_state = self.WAIT_STATE
        self._enter_wait_state()

    def stop(self):
        self._stop_event.set()
        self._cancel_wait_timer()
        self._cancel_response_timer()
        with self._state_lock:
            self._current_state = self.WAIT_STATE
        self._answer_event = None

    def on_gaze_detected(self):
        if not self._is_active():
            return
        with self._state_lock:
            if self._current_state != self.WAIT_STATE:
                return
        self._cancel_wait_timer()
        self._transition_to(self.OFFER_HINT)

    def on_help_requested(self):
        if not self._is_active():
            return False
        with self._state_lock:
            if self._current_state != self.WAIT_STATE:
                return False
        self._cancel_wait_timer()
        self._transition_to(self.OFFER_HINT)
        return True

    def handle_user_response(self, wants_help):
        if not self._is_active():
            return False
        with self._state_lock:
            if self._current_state != self.OFFER_HINT:
                return False
        self._cancel_response_timer()
        if wants_help:
            self.controller.logger.log_event({"event_type": "tip_response", "details": "yes"})
            self._transition_to(self.GIVE_HINT)
        else:
            self.controller.logger.log_event({"event_type": "tip_response", "details": "no"})
            self._transition_to(self.WAIT_STATE)
        return True

    def expecting_yes_no(self):
        with self._state_lock:
            return self._current_state == self.OFFER_HINT and self._is_active()

    def current_state(self):
        with self._state_lock:
            return self._current_state

    def _transition_to(self, new_state):
        if not self._is_active():
            return
        with self._state_lock:
            self._current_state = new_state
        print(f"[DEBUG] StateMachine: Entering state '{new_state}'")
        if new_state == self.WAIT_STATE:
            self._enter_wait_state()
        elif new_state == self.OFFER_HINT:
            self._enter_offer_hint_state()
        elif new_state == self.GIVE_HINT:
            self._enter_give_hint_state()

    def _enter_wait_state(self):
        print("[DEBUG] StateMachine: In WAIT_STATE (timer armed)")
        self._cancel_wait_timer()
        self._cancel_response_timer()
        if not self._is_active():
            return
        timer = threading.Timer(self.wait_timeout, self._wait_timeout_fired)
        timer.daemon = True
        with self._state_lock:
            self._wait_timer = timer
        timer.start()

    def _enter_offer_hint_state(self):
        print("[DEBUG] StateMachine: In OFFER_HINT (asking for help)")
        self._cancel_wait_timer()
        self._cancel_response_timer()
        if not self._is_active():
            return
        tip = "Do you need help?"
        try:
            self.controller.last_interaction = time.time()
            self.controller._speak_with_listening_pause(tip)
            self.controller.furhat.set_expression("neutral")
            self.controller.logger.log_event({"event_type": "robot_tip", "details": tip})
        except Exception:
            logging.exception("Failed to request help")
        timer = threading.Timer(5.0, self._offer_timeout_fired)
        timer.daemon = True
        with self._state_lock:
            self._response_timer = timer
        timer.start()

    def _enter_give_hint_state(self):
        print("[DEBUG] StateMachine: In GIVE_HINT (providing hint)")
        if not self._is_active():
            return
        self.controller._give_hint()
        self._transition_to(self.WAIT_STATE)

    def _wait_timeout_fired(self):
        if not self._is_active():
            return
        with self._state_lock:
            if self._current_state != self.WAIT_STATE:
                return
        self._transition_to(self.OFFER_HINT)

    def _offer_timeout_fired(self):
        if not self._is_active():
            return
        with self._state_lock:
            if self._current_state != self.OFFER_HINT:
                return
        print("[DEBUG] StateMachine: OFFER_HINT timeout, returning to WAIT_STATE")
        self.controller.logger.log_event({"event_type": "tip_response", "details": "no_response"})
        self._transition_to(self.WAIT_STATE)

    def _cancel_wait_timer(self):
        with self._state_lock:
            timer = self._wait_timer
            self._wait_timer = None
        if timer:
            timer.cancel()

    def _cancel_response_timer(self):
        with self._state_lock:
            timer = self._response_timer
            self._response_timer = None
        if timer:
            timer.cancel()

    def _is_active(self):
        if self._stop_event.is_set():
            return False
        if self._answer_event is None:
            return False
        if self._answer_event.is_set():
            return False
        controller_check = getattr(self.controller, "is_answering_user_question", None)
        if callable(controller_check):
            try:
                if controller_check():
                    return False
            except Exception:
                pass
        return True
    

class ExperimentController:
    def __init__(self, gui, db, furhat, llm, logger, mode, check_relevance=True):
        self.gui = gui
        self.db = db
        self.furhat = furhat
        self.llm = llm
        self.logger = logger
        self.mode = mode
        self.num_questions = 8 # Can later be adapted to variable number
        self.answer_event = None
        self.current_question = None
        self.check_relevance = check_relevance
        self.last_interaction = None
        self._last_gaze_state = None
        self._last_gaze_spoken = time.time()
        self.inactivity_threshold = 10 # time in seconds before proactive help is offered
        self.proactive_check_interval = 1 
        self.post_answer_delay = 2.0
        # per-question hint index
        self._current_hint_index = 0
        self.help_state_machine = None
        self._answering_user_question = threading.Event()
        # start Furhat attention/gaze monitor if supported
        try:
            if hasattr(self.furhat, "start_attention_monitor"):
                self.furhat.start_attention_monitor(self.handle_gaze)
        except Exception as exc:
            print(f"Attention monitor not started: {exc}")

        try:
            self.furhat.listen_speech(self.handle_transcribed_speech)
        except Exception:
            pass


    def run_experiment(self):
        self._wait_for_intro_then_greet()
        print("Starting experiment...")

        num_questions = self.num_questions
        difficulties = ["easy"]*0 + ["medium"]*4 + ["hard"]*4

        self.logger.log_event({"event_type": "mode_selected", "details": self.mode})

        if self.mode == "proactive" and self.help_state_machine is None:
            self.help_state_machine = ProactiveHelpStateMachine(self)

        for i in range(num_questions):
            print(f"\n----- Question {i+1} of {num_questions} -----")
            difficulty = difficulties[i]
            question = self.db.get_random_question(difficulty)
            if not question:
                continue
            self.gui.display_question(question["question"], question["options"], question.get("answer"))
            self.logger.log_event({"event_type": "question_displayed", "details": question["question"]})

            # wait for Start on the very first question (uses same simple event-based mechanism as answer selection)
            if i == 0 and hasattr(self.gui, "wait_for_start"):
                print("Waiting for user to press Start in the browser...")
                self.gui.wait_for_start()  # blocks until /api/start called by browser

            try:
                self._announce_question(question)
            except Exception as e:
                print(f"Error announcing question: {e}")
            self.last_interaction = time.time()

            # reset per-question helper state
            self._current_hint_index = 0

            self.answer_event = threading.Event()
            self.current_question = question
            user_answer = [None]

            answer_thread = threading.Thread(target=self.get_answer, args=(user_answer, self.answer_event))
            answer_thread.start()

            if self.mode == "proactive" and self.help_state_machine:
                self.help_state_machine.start(self.answer_event)

            answered_in_time = self.answer_event.wait(timeout=60)
            if self.mode == "proactive" and self.help_state_machine:
                self.help_state_machine.stop()
            answer_thread.join()

            user_answer_val = user_answer[0]
            if not answered_in_time or user_answer_val is None:
                print("Time's up! No answer received.")
                self.logger.log_event({"event_type": "timeout", "details": "No answer in 60 seconds"})
                self._announce_time_up(question)
            else:
                self.logger.log_event({"event_type": "user_answer", "details": user_answer_val})

                # Robot feedback: announce correctness immediately
                try:
                    # parse selected (gui uses 1-based choice)
                    selected = int(user_answer_val)
                except Exception:
                    selected = None

                correct_option = question.get("answer")
                if selected is not None and correct_option is not None:
                    if selected == correct_option:
                        # enthusiastic correct response
                        try:
                            self.furhat.speak("Correct!", wait=True)
                        except Exception as e:
                            print(f"Error speaking correct feedback: {e}")
                        try:
                            self.furhat.set_expression("BigSmile")
                        except Exception:
                            pass
                        self.logger.log_event({"event_type": "robot_response", "details": "Correct! Well done!"})
                    else:
                        # wrong response
                        try:
                            self.furhat.speak("Wrong!", wait=True)
                        except Exception as e:
                            print(f"Error speaking incorrect feedback: {e}")
                        try:
                            self.furhat.set_expression("ExpressSad")
                        except Exception:
                            pass
                        self.logger.log_event({"event_type": "robot_response", "details": "Ohhh, it's wrong."})
                # end robot feedback

            if self.post_answer_delay:
                time.sleep(self.post_answer_delay)

        print("Experiment finished.")
        self._say_thank_you()
        self.logger.log_event({"event_type": "experiment_finished", "details": "done"})
        if hasattr(self.gui, "notify_experiment_finished"):
            try:
                self.gui.notify_experiment_finished()
            except Exception as exc:
                print(f"Error notifying GUI about experiment completion: {exc}")
        # Stop Furhat speech listener
        try:
            self.furhat.stop_listening()
        except Exception as e:
            print(f"Error stopping Furhat listener: {e}")
    
    
    def handle_transcribed_speech(self, user_speech):
        self.last_interaction = time.time()
        # Only process if answer window is open and question is set
        if self.answer_event and self.current_question and not self.answer_event.is_set():
            state_machine = getattr(self, "help_state_machine", None)
            # Handle proactive yes/no replies first so they do not fall through to the LLM
            if state_machine and isinstance(user_speech, str) and state_machine.expecting_yes_no():
                yes_match = re.search(r"\b(yes|yeah|yep|sure|please|ok|okay)\b", user_speech, re.IGNORECASE)
                no_match = re.search(r"\b(no|nope|not now|nah)\b", user_speech, re.IGNORECASE)
                if yes_match and state_machine.handle_user_response(True):
                    return
                if no_match and state_machine.handle_user_response(False):
                    try:
                        self.furhat.speak("Okay, I'll wait.", wait=True)
                    except Exception:
                        pass
                    return

            # detect quick keywords for proactive help and transition the state machine
            if state_machine and isinstance(user_speech, str) and re.search(r"\b(help|hint)\b", user_speech, re.IGNORECASE):
                if state_machine.on_help_requested():
                    return

            llm_response = self.llm.llm_generate_response(
                self.current_question["question"],
                self.current_question["options"],
                user_request=user_speech
            )


            response, expression = llm_response
            if response is None or expression is None:
                self.logger.log_event({"event_type": "robot_noise_ignored", "details": user_speech})
            elif response == "hint":
                if state_machine:
                    state_machine.stop()
                self._give_hint()
            else:
                self._deliver_robot_response(response, expression)


    def handle_gaze(self, event):
        """Handle gaze/attention events from FurhatAPI.
        event: {'state': 'towards'|'away'|'left'|'right'|'up'|'down', 'confidence': float}
        When user looks at the robot (towards) speak a short acknowledgement.
        """
        # Defensive parse and logging for debugging
        state = None
        conf = 0.0
        if isinstance(event, dict):
            state = event.get("state")
            try:
                conf = float(event.get("confidence", 0.0))
            except Exception:
                conf = 0.0

        # (No verbose debug prints) — keep only structured logging and concise output on reaction
        try:
            self.loggr.log_event({"event_type": "gaze_event_raw", "details": str(event)})
        except Exception:
            pass

        state_machine = getattr(self, "help_state_machine", None)
        now = time.time()
        # only react when transitioning into 'towards' and throttle repeats (8s)
        if state == "towards" and self._last_gaze_state != "towards" and (now - self._last_gaze_spoken) > 8.0:
            try:
                # Terminal-only debug print and structured log so proactive logic can react
                try:
                    print(f"DEBUG: gaze detected -> {state} (conf={conf})")
                except Exception:
                    pass
                try:
                    self.logger.log_event({"event_type": "gaze_detected", "details": f"{state} (conf={conf})"})
                except Exception:
                    pass
                if state_machine:
                    state_machine.on_gaze_detected()
            except Exception as e:
                # avoid noisy prints; log the exception
                try:
                    self.logger.log_event({"event_type": "gaze_reaction_error", "details": str(e)})
                except Exception:
                    pass
            self._last_gaze_spoken = now

        # update last state
        self._last_gaze_state = state


    def get_answer(self, user_answer, answer_event):
        user_answer[0] = self.gui.get_user_answer()
        self.last_interaction = time.time()
        answer_event.set()


    def _deliver_robot_response(self, response, expression):
        state_machine = getattr(self, "help_state_machine", None)
        should_restart = False
        self._answering_user_question.set()
        try:
            if state_machine and hasattr(state_machine, "stop"):
                try:
                    state_machine.stop()
                    if self.answer_event and not self.answer_event.is_set():
                        should_restart = True
                except Exception:
                    pass
            self.furhat.speak(response, wait=True)
            if expression:
                self.furhat.set_expression(expression)
            self.logger.log_event({"event_type": "robot_response", "details": response})
        finally:
            self._answering_user_question.clear()
        if should_restart and state_machine and hasattr(state_machine, "start"):
            try:
                state_machine.start(self.answer_event)
            except Exception:
                pass

    def _give_hint(self):
        """Deliver a hint from the current question's hints list (if available).
        Advances the per-question hint index so repeated requests give the next hint.
        """
        try:
            hints = self.current_question.get("hints", []) if self.current_question else []
            idx = self._current_hint_index
            if isinstance(hints, (list, tuple)) and idx < len(hints):
                hint = hints[idx]
                try:
                    self.furhat.speak(hint, wait=True)
                except Exception:
                    pass
                self.logger.log_event({"event_type": "robot_hint", "details": hint})
                self._current_hint_index = idx + 1
            else:
                # No more predefined hints; give a short generic fallback
                try:
                    self.furhat.speak("I don't have more hints right now.", wait=True)
                except Exception:
                    pass
                self.logger.log_event({"event_type": "robot_hint", "details": "no_more_hints"})
        except Exception:
            logging.exception("_give_hint failed")

    def _announce_question(self, question):
        """Format and have Furhat read the question and options aloud (pauses listening while speaking)."""
        if not question:
            return
        q_text = question.get("question") or question.get("text") or str(question)
        opts = question.get("options") or question.get("choices") or []
        # pause listening (if available), speak, then resume listening
        try:
            if hasattr(self.furhat, "stop_listening"):
                self.furhat.stop_listening()
        except Exception:
            pass

        try:
            # Speak question first
            self.furhat.speak(q_text, wait=True)
            # Then speak options using letter labels with tiny pauses between
            #for idx, option in enumerate(opts):
            #    label = chr(65 + idx) if idx < 26 else f"Option {idx + 1}"
            #    utterance = f"Option {label}: {option}"
            #    self.furhat.speak(utterance, wait=True)
            time.sleep(0.3)
        except Exception as e:
            print(f"Error announcing question: {e}")

        try:
            # restart ASR callback
            if hasattr(self.furhat, "listen_speech"):
                self.furhat.listen_speech(self.handle_transcribed_speech)
        except Exception:
            pass
        finally:
            mark_ready = getattr(self.gui, "mark_question_ready", None)
            if callable(mark_ready):
                try:
                    mark_ready()
                except Exception:
                    pass

    def _wait_for_intro_then_greet(self):
        reset_intro = getattr(self.gui, "reset_intro_complete", None)
        if callable(reset_intro):
            try:
                reset_intro()
            except Exception:
                pass
        reset_ready = getattr(self.gui, "reset_welcome_ready", None)
        if callable(reset_ready):
            try:
                reset_ready()
            except Exception:
                pass
        wait_intro = getattr(self.gui, "wait_for_intro_complete", None)
        if callable(wait_intro):
            try:
                print("Waiting for intro video to finish before greeting contestant...")
                if not wait_intro(timeout=20.0):
                    print("Intro wait timed out; proceeding anyway.")
            except Exception as exc:
                print(f"Intro wait failed: {exc}")
        self._speak_welcome_message()
        mark_ready = getattr(self.gui, "mark_welcome_ready", None)
        if callable(mark_ready):
            try:
                mark_ready()
            except Exception:
                pass

    def _announce_time_up(self, question):
        if not question:
            return
        options = question.get("options") or []
        correct_option = question.get("answer")
        correct_text = None
        label = None
        if isinstance(correct_option, int):
            idx = correct_option - 1
            if 0 <= idx < len(options):
                correct_text = options[idx]
            if 0 <= idx < 26:
                label = chr(65 + idx)
            elif idx >= 0:
                label = f"Option {idx + 1}"
        if correct_text:
            if label:
                message = f"Time is up, and the correct answer is {label}: {correct_text}."
            else:
                message = f"Time is up, and the correct answer is {correct_text}."
        elif label:
            message = f"Time is up, and the correct answer is {label}."
        else:
            message = "Time is up."
        try:
            self.furhat.speak(message, wait=True)
        except Exception:
            pass
        self.logger.log_event({"event_type": "robot_response", "details": message})

    def _say_thank_you(self):
        try:
            self.furhat.speak("Thank you for playing the game!", wait=True)
        except Exception:
            pass

    def _speak_with_listening_pause(self, text, wait=True):
        stop_listening = getattr(self.furhat, "stop_listening", None)
        restart_listening = getattr(self.furhat, "listen_speech", None)
        try:
            if callable(stop_listening):
                try:
                    stop_listening()
                except Exception:
                    pass
            self.furhat.speak(text, wait=wait)
        finally:
            if callable(restart_listening):
                try:
                    restart_listening(self.handle_transcribed_speech)
                except Exception:
                    pass

    def _speak_welcome_message(self):
        stop_listening = getattr(self.furhat, "stop_listening", None)
        restart_listening = getattr(self.furhat, "listen_speech", None)
        try:
            if callable(stop_listening):
                try:
                    stop_listening()
                except Exception:
                    pass
            self.furhat.speak(
                "Welcome to Who Wants to Be a Furllionaire! "
                "I'm your host, and I'm thrilled to have you here today! "
                "Get ready for a fun and engaging experience as we test your knowledge and curiosity! "
                "Before we begin, here are a few instructions. "
                "You'll be presented with a series of questions—read each one carefully. "
                "Select your answer and submit it when you're ready. "
                "Don't worry if you're unsure—just give it your best shot! "
                "If you need help, just let me know. "
                "Are you ready? Let's get started with your first question!",
                wait=True
            )
        except Exception:
            pass
        finally:
            if callable(restart_listening):
                try:
                    restart_listening(self.handle_transcribed_speech)
                except Exception:
                    pass

    def is_answering_user_question(self):
        return self._answering_user_question.is_set()
