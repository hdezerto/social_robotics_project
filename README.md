# Furhat Game Assistant

Interactive quiz experience for the KTH Social Robotics course. A Furhat robot delivers the questions, a Flask web client (“Furllionaire”) handles visuals, an LLM backend generates responses, and every run is logged for later analysis.

## Requirements
- Python 3.10+
- Furhat robot (or the virtual Furhat application) on the same network
- Mistral API key for the LLM backend

## Setup
1. Clone the repository and (optionally) create a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Export your Mistral key:
   - Windows: `setx MISTRAL_LLM_API_KEY "<YOUR_KEY>"`
   - macOS/Linux: `export MISTRAL_LLM_API_KEY="<YOUR_KEY>"`
4. Confirm you can reach the Furhat IP (ping or via the Furhat Console).

## Run the Experiment
1. Open `main.py` and set the top-level hyperparameters:
   - `IP_ADDRESS` – robot IP (examples provided in the file)
   - `MODE` – `"proactive"` or `"reactive"`
2. Start the system: `python main.py`.
   - The console prints the selected IP and mode.
   - The Flask GUI is served on `http://127.0.0.1:5000` by default and opens automatically.
   - Experiment events are logged to `logs/experiment_log.csv`.

## Configuration Notes
- `QuizWebServer` (inside `gui/web_server.py`) exposes optional parameters such as host, port, `expected_questions`, and `time_limit` if you need to override defaults.
- Questions are loaded from `database/questions.json`; update or replace that file to change the quiz.
- Ensure `MISTRAL_LLM_API_KEY` remains set in the environment before launching the controller.

## Project Layout
- `main.py` – wires GUI, controller, robot API, LLM, and logging
- `controller/` – experiment flow and interaction logic
- `database/` – question database utilities
- `furhat_interface/` – Furhat API wrapper
- `gui/` – Flask bridge plus `web_client/` static assets
- `llm_backend/` – Mistral client
- `logs/` – CSV logger utilities and experiment output

## Maintainers
Cilia Nanninga · Diogo Paulo · Helena Westermann · Hugo Dezerto · Maria Sebastião (Group 6 @ KTH Social Robotics)
