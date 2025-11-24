# Experiment Controller
# Manages experiment flow and interaction modes

import threading
import time
import re
import logging


class ExperimentController:
    def __init__(self, gui, db, furhat, llm, logger, check_relevance=True):
        self.gui = gui
        self.db = db
        self.furhat = furhat
        self.llm = llm
        self.logger = logger
        self.answer_event = None
        self.current_question = None
        self.check_relevance = check_relevance
        self.last_interaction = None
        self._last_gaze_state = None
        self._last_gaze_spoken = 0.0
        self.inactivity_threshold = 10 # time in seconds before proactive help is offered
        self.proactive_check_interval = 1 
        self.post_answer_delay = 2.0
        # events used by proactive help logic
        self._heard_help_event = threading.Event()
        self._gaze_seen_event = threading.Event()
        # awaiting response to proactive tip (yes/no)
        self._awaiting_tip_response = threading.Event()
        # events signalling tip responses
        self._hint_given_event = threading.Event()
        self._tip_declined_event = threading.Event()
        # per-question hint index
        self._current_hint_index = 0
        # proactive loop configuration
        self.cooldown_after_tip = 10.0
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
        print("Starting experiment...")

        num_questions = 8
        difficulties = ["easy"]*0 + ["medium"]*4 + ["hard"]*4

        mode = "proactive"  # or "reactive"
        self.logger.log_event({"event_type": "mode_selected", "details": mode})

        for i in range(num_questions):
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

            # reset per-question helper events
            self._heard_help_event.clear()
            self._gaze_seen_event.clear()
            self._awaiting_tip_response.clear()
            self._hint_given_event.clear()
            self._tip_declined_event.clear()
            self._current_hint_index = 0

            self.answer_event = threading.Event()
            self.current_question = question
            user_answer = [None]

            answer_thread = threading.Thread(target=self.get_answer, args=(user_answer, self.answer_event))
            answer_thread.start()

            if mode == "proactive":
                help_thread = threading.Thread(target=self.proactive_help_loop, args=(self.answer_event, question))
                help_thread.daemon = True
                help_thread.start()

            answered_in_time = self.answer_event.wait(timeout=60)
            if mode == "proactive":
                help_thread.join()
            answer_thread.join()

            user_answer_val = user_answer[0]
            if not answered_in_time or user_answer_val is None:
                print("Time's up! No answer received.")
                self.logger.log_event({"event_type": "timeout", "details": "No answer in 60 seconds"})
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

            print("---")
        print("Experiment finished.")
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
            # If we're awaiting a yes/no reply to a tip, handle that first
            try:
                if self._awaiting_tip_response.is_set() and isinstance(user_speech, str):
                    # quick yes/no matching
                    yes_match = re.search(r"\b(yes|yeah|yep|sure|please|ok|okay)\b", user_speech, re.IGNORECASE)
                    no_match = re.search(r"\b(no|nope|not now|nah)\b", user_speech, re.IGNORECASE)
                    if yes_match:
                        try:
                            self._awaiting_tip_response.clear()
                            self._give_hint()
                            return
                        except Exception:
                            pass
                    if no_match:
                        try:
                            self._awaiting_tip_response.clear()
                            try:
                                self.furhat.speak("Okay, I'll wait.", wait=True)
                            except Exception:
                                pass
                            self.logger.log_event({"event_type": "tip_response", "details": "no"})
                            return
                        except Exception:
                            pass
            except Exception:
                pass
            # detect quick keywords for proactive help (do not replace full LLM flow)
            try:
                if isinstance(user_speech, str) and re.search(r"\b(help|hint)\b", user_speech, re.IGNORECASE):
                    # signal proactive help thread that user asked for help

                    try:
                        self._heard_help_event.set()
                    except Exception:
                        pass
            except Exception:
                pass

            llm_response = self.llm.generate_assistant_response(
                self.current_question["question"],
                self.current_question["options"],
                user_request=user_speech,
                check_relevance=self.check_relevance,
            )

            if self.check_relevance:
                response, expression = llm_response
                if response is not None:
                    self._deliver_robot_response(response, expression)
                else:
                    self.logger.log_event({"event_type": "robot_noise_ignored", "details": user_speech})
            else:
                response, expression = llm_response
                if response is not None:
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
            self.logger.log_event({"event_type": "gaze_event_raw", "details": str(event)})
        except Exception:
            pass

        now = time.time()
        # only react when transitioning into 'towards' and throttle repeats (5s)
        if state == "towards" and self._last_gaze_state != "towards" and (now - self._last_gaze_spoken) > 4.0:
            try:
                # mark that user has looked at robot (used by proactive logic)
                try:
                    self._gaze_seen_event.set()
                except Exception:
                    pass
                # Terminal-only debug print and structured log so proactive logic can react
                try:
                    print(f"DEBUG: gaze detected -> {state} (conf={conf})")
                except Exception:
                    pass
                try:
                    self.logger.log_event({"event_type": "gaze_detected", "details": f"{state} (conf={conf})"})
                except Exception:
                    pass
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


    def proactive_help_loop(self, answer_event, question):
        """
        Proactive help flow (per user's requested logic):

        - After the question is announced, wait up to 5s for the user to say 'help'/'hint' (option A).
          - If user said help -> immediately go to Action 1 (ask "Do you need help?").
        - If no help word within 5s (option B):
          - If user has already looked at the robot (gaze event seen) -> immediately Action 1 (option D).
          - Otherwise (option C): wait up to 8s for the user to look at the robot; if they don't, go to Action 1.

        Action 1: ask "Do you need help?" (spoken), set neutral expression and log. Then return (do not repeatedly prompt).
        """
        # Run the proactive decision flow repeatedly until answered or max prompts reached
        while not answer_event.is_set():
            # Option A: immediate check for explicit help
            try:
                heard = bool(self._heard_help_event.is_set())
            except Exception:
                heard = False
            try:
                print(f"DEBUG: proactive_help_loop start - heard={heard}")
            except Exception:
                pass

            if answer_event.is_set():
                break

            if not heard:
                # Unconditional wait 5s for the option B behavior
                try:
                    time.sleep(5.0)
                except Exception:
                    pass
                if answer_event.is_set():
                    break

            # If user had said help (heard==True), consume the event so it won't persist
            if heard:
                try:
                    self._heard_help_event.clear()
                except Exception:
                    pass

            # After immediate check or 5s wait, inspect gaze
            try:
                gazed = self._gaze_seen_event.is_set()
            except Exception:
                gazed = False
            try:
                print(f"DEBUG: proactive_help_loop immediate gaze check -> {gazed}")
            except Exception:
                pass

            if not gazed:
                # Poll gaze for up to 8s and react immediately if seen
                gazed = False
                start_t = time.time()
                try:
                    while (time.time() - start_t) < 8.0 and not answer_event.is_set():
                        try:
                            if self._gaze_seen_event.is_set():
                                gazed = True
                                break
                        except Exception:
                            pass
                        time.sleep(0.1)
                except Exception:
                    gazed = False
                try:
                    print(f"DEBUG: proactive_help_loop finished polling gaze -> {gazed}")
                except Exception:
                    pass

            # If gaze was used, consume it so future gaze events are fresh
            if gazed:
                try:
                    self._gaze_seen_event.clear()
                except Exception:
                    pass

            # Before speaking, check again if answer arrived
            if answer_event.is_set():
                break

            # Action 1: ask the user if they want help
            tip = "Do you need help?"
            try:
                self.last_interaction = time.time()
                try:
                    self._awaiting_tip_response.set()
                except Exception:
                    pass
                self.furhat.speak(tip)
                self.furhat.set_expression("neutral")
                self.logger.log_event({"event_type": "robot_tip", "details": tip})
            except Exception:
                pass

            # Cooldown before next prompt (allow user to respond)
            cooldown = getattr(self, "cooldown_after_tip", 10.0)
            start_cd = time.time()
            while (time.time() - start_cd) < cooldown and not answer_event.is_set():
                time.sleep(0.2)

            # Clear awaiting flag after cooldown so next cycle can re-wait
            try:
                self._awaiting_tip_response.clear()
            except Exception:
                pass

            # small pause before next iteration to avoid tight looping
            try:
                time.sleep(0.1)
            except Exception:
                pass

    def _deliver_robot_response(self, response, expression):
        self.furhat.speak(response)
        if expression:
            self.furhat.set_expression(expression)
        self.logger.log_event({"event_type": "robot_response", "details": response})

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
            for idx, option in enumerate(opts):
                label = chr(65 + idx) if idx < 26 else f"Option {idx + 1}"
                utterance = f"Option {label}: {option}"
                self.furhat.speak(utterance, wait=True)
                time.sleep(0.3)
        except Exception as e:
            print(f"Error announcing question: {e}")

        try:
            # restart ASR callback
            if hasattr(self.furhat, "listen_speech"):
                self.furhat.listen_speech(self.handle_transcribed_speech)
        except Exception:
            pass
