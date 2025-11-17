# Quiz GUI
# Handles user interface for the quiz game

import tkinter as tk
from tkinter import messagebox

class QuizGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Quiz Game")
        self.question_label = tk.Label(self.root, text="", font=("Arial", 14))
        self.question_label.pack(pady=10)
        self.options_var = tk.StringVar()
        self.options_frame = tk.Frame(self.root)
        self.options_frame.pack(pady=10)
        self.submit_button = tk.Button(self.root, text="Submit", command=self._submit_answer)
        self.submit_button.pack(pady=10)
        self.answer = None
        self._answer_ready = tk.BooleanVar(value=False)

    def display_question(self, question, options):
        self.question_label.config(text=question)
        self.options_var.set("")
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        for idx, opt in enumerate(options):
            btn = tk.Radiobutton(self.options_frame, text=opt, variable=self.options_var, value=str(idx+1), font=("Arial", 12))
            btn.pack(anchor='w')
        self._answer_ready.set(False)

    def _submit_answer(self):
        if self.options_var.get():
            self.answer = self.options_var.get()
            self._answer_ready.set(True)
        else:
            messagebox.showwarning("No selection", "Please select an answer.")

    def get_user_answer(self):
        self.root.wait_variable(self._answer_ready)
        return self.answer


    def start(self):
        self.root.mainloop()
