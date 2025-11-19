# Quiz GUI
# Handles user interface for the quiz game

import tkinter as tk
from tkinter import messagebox
import threading

class QuizGUI:
    def __init__(self):
        self.root = tk.Tk() # Main window
        self.root.title("Quiz Game") # Set window title
        self.question_label = tk.Label(self.root, text="", font=("Arial", 14)) # Label for question text
        self.question_label.pack(pady=10) # Adds the question label to the window with padding
        self.options_var = tk.StringVar() # Variable to hold selected option
        self.options_frame = tk.Frame(self.root) # Frame for option buttons
        self.options_frame.pack(pady=10)  # Adds the options frame to the window with padding
        self.submit_button = tk.Button(self.root, text="Submit", command=self._submit_answer) # Submit button, calls _submit_answer on click
        self.submit_button.pack(pady=10) # Adds the submit button to the window with padding
        self.answer = None # Stores the user's selected answer
        self._answer_event = threading.Event() # Indicates if an answer has been submitted

    def display_question(self, question, options):
        def update_ui():
            self.question_label.config(text=question) # Update question text with the new question
            self.options_var.set("") # Resets the selected option to nothing
            for widget in self.options_frame.winfo_children(): # Removes any existing radio buttons from the options frame
                widget.destroy()
            for idx, opt in enumerate(options):
                btn = tk.Radiobutton(self.options_frame, text=opt, variable=self.options_var, value=str(idx+1), font=("Arial", 12))
                btn.pack(anchor='w')
            self.answer = None
            self._answer_event.clear()

        self.root.after(0, update_ui)

    def _submit_answer(self):
        if self.options_var.get():
            self.answer = self.options_var.get()
            self._answer_event.set()
        else:
            messagebox.showwarning("No selection", "Please select an answer.")

    def get_user_answer(self):
        self._answer_event.wait()
        return self.answer


    def start(self):
        self.root.mainloop()
