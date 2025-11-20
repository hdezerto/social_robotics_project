# Experiment Controller
# Manages experiment flow and interaction modes

import threading
import time


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
        self.inactivity_threshold = 10 # time in seconds before proactive help is offered
        self.proactive_check_interval = 1 
        self.post_answer_delay = 2.0
        self.furhat.listen_speech(self.handle_transcribed_speech)


    def run_experiment(self):
        print("Starting experiment...")

        num_questions = 8
        difficulties = ["easy"]*2 + ["medium"]*4 + ["hard"]*2

        mode = "proactive"  # or "proactive"
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


    def get_answer(self, user_answer, answer_event):
        user_answer[0] = self.gui.get_user_answer()
        self.last_interaction = time.time()
        answer_event.set()


    def proactive_help_loop(self, answer_event, question):
        hint_index = 0
        hints = question.get("hints", [])
        ask_first = True
        question_start = time.time()
        while not answer_event.is_set() and (time.time() - question_start) < 60:
            time.sleep(self.proactive_check_interval)
            if self.last_interaction and (time.time() - self.last_interaction) < self.inactivity_threshold:
                continue
            if answer_event.is_set():
                break
            if ask_first:
                tip = "Do you need help?"
                ask_first = False
            else:
                if hint_index < len(hints):
                    tip = hints[hint_index]
                    hint_index += 1
                else:
                    tip = "Do you need help?"
                ask_first = True
            self.last_interaction = time.time()
            self.furhat.speak(tip)
            self.furhat.set_expression("neutral")
            self.logger.log_event({"event_type": "robot_tip", "details": tip})

    def _deliver_robot_response(self, response, expression):
        self.furhat.speak(response)
        if expression:
            self.furhat.set_expression(expression)
        self.logger.log_event({"event_type": "robot_response", "details": response})

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
