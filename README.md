# Who Wants to Be a Furllionaire?

Social Robotics project for **DD2413 Social Robotics** at KTH Royal Institute of Technology.

This project implements a Furhat-based quiz assistant and was used to compare two interaction modes:

- **Reactive assistance:** Furhat gives help only when the participant asks for it.
- **Proactive assistance:** Furhat can offer help without an explicit user request, based mainly on inactivity in the current implementation.

The experiment investigated whether proactive robot assistance improves user experience during a timed quiz game. In a between-subjects study with 20 participants, the reactive mode received equal or higher ratings across enjoyment, usefulness, sociability, and performance trust. Sociability showed a significant preference for reactive assistance, suggesting that proactive support needs careful timing to avoid feeling intrusive.

## System Overview

The prototype combines:

- Furhat speech, listening, and facial expressions.
- A quiz controller with timed multiple-choice questions.
- A JSON question database with difficulty levels and pre-written hints.
- A Mistral LLM backend for short contextual responses.
- A lightweight quiz UI plus static "Furllionaire" web assets.
- CSV experiment logging.

## Repository Map

| Path | Purpose |
| --- | --- |
| `main.py` | Main entry point wiring together the GUI, database, Furhat API, LLM API, logger, and controller. |
| `controller/` | Experiment flow and reactive/proactive interaction logic. |
| `database/` | Quiz question database and loader. |
| `furhat_interface/` | Furhat Realtime API wrapper. |
| `llm_backend/` | Mistral API integration for contextual robot responses. |
| `gui/` | Simple Python quiz GUI. |
| `furllionaire-gui/` | Static web UI assets for the themed quiz interface. |
| `logs/` | Logger implementation; generated experiment logs are ignored by Git. |

## Setup

Create a Python environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure the Mistral API key and Furhat address:

```bash
export MISTRAL_LLM_API_KEY="your-api-key"
export FURHAT_IP="127.0.0.1"
```

On Windows PowerShell:

```powershell
$env:MISTRAL_LLM_API_KEY="your-api-key"
$env:FURHAT_IP="127.0.0.1"
```

Use the actual robot IP for `FURHAT_IP` when connecting to a physical Furhat.

## Running

Start the experiment controller:

```bash
python main.py
```

Run the simple quiz GUI only:

```bash
python gui/quiz_gui.py
```

Test Furhat speech/listening:

```bash
python debug_furhat_speak.py
```

## Study Result

The project report found that proactive assistance was not perceived as more helpful or engaging in this implementation. Participants often preferred the reactive condition, and qualitative feedback pointed to mistimed interventions, missed speech inputs, and occasional over-informative hints as limitations. The main takeaway is that proactive social robot behaviour depends strongly on accurate sensing and well-timed interventions.

## Contributors

| Contributor | Contact |
| --- | --- |
| Cilia Nanninga | `nanninga@kth.se` |
| Diogo Paulo | `diogop@kth.se` |
| Helena Westermann | `hewes@kth.se` |
| Hugo Dezerto | `hugoad@kth.se` |
| Maria Sebastião | `mcms2@kth.se` |

## Acknowledgements

- Furhat Robotics
- KTH Royal Institute of Technology
- Mistral AI
