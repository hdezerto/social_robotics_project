# Who Wants to Be a Furllionaire?

Social Robotics project for **DD2413 Social Robotics** at KTH Royal Institute of Technology.

This project implements a Furhat-based quiz assistant and was used to compare two interaction modes:

- **Reactive assistance:** Furhat gives help only when the participant asks for it.
- **Proactive assistance:** Furhat can offer help without an explicit user request, based mainly on inactivity in the current implementation.

The experiment investigated whether proactive robot assistance improves user experience during a timed quiz game. In a between-subjects study with 20 participants, the reactive mode received equal or higher ratings across enjoyment, usefulness, sociability, and performance trust. Sociability showed a significant preference for reactive assistance, suggesting that proactive support needs careful timing to avoid feeling intrusive.

## Demo

The demo video presents the interaction flow with audio, showing the reactive assistance condition first and the proactive assistance condition second.

[Watch demo video](https://hdezerto.github.io/social_robotics_project/)

## System Overview

The prototype combines:

- Furhat speech, listening, gaze, and facial expressions.
- A Flask-based "Furllionaire" quiz web client.
- A quiz controller with timed multiple-choice questions.
- A JSON question database with difficulty levels and pre-written hints.
- A Mistral LLM backend for short contextual responses.
- CSV experiment logging.

## Repository Map

| Path | Purpose |
| --- | --- |
| `main.py` | Main entry point wiring together the web server, database, Furhat API, LLM API, logger, and controller. |
| `controller/` | Experiment flow and reactive/proactive interaction logic. |
| `database/` | Quiz question database and loader. |
| `furhat_interface/` | Furhat Realtime API wrapper. |
| `gui/` | Flask bridge plus `web_client/` static assets for the themed quiz interface. |
| `llm_backend/` | Mistral API integration for contextual robot responses. |
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

Configure the Mistral API key and optional Furhat address:

```bash
export MISTRAL_LLM_API_KEY="your-api-key"
export FURHAT_IP="127.0.0.1"
```

On Windows PowerShell:

```powershell
$env:MISTRAL_LLM_API_KEY="your-api-key"
$env:FURHAT_IP="127.0.0.1"
```

`FURHAT_IP` overrides the `IP_ADDRESS` value in `main.py`. Use the actual robot IP when connecting to a physical Furhat.

## Running

Start the experiment controller and web client:

```bash
python main.py
```

The Flask quiz UI is served at `http://127.0.0.1:5000` by default and opens automatically. Set the top-level `MODE` value in `main.py` to choose `"reactive"` or `"proactive"`.

## Study Result

The project report found that proactive assistance was not perceived as more helpful or engaging in this implementation. Participants often preferred the reactive condition, and qualitative feedback pointed to mistimed interventions, missed speech inputs, and occasional over-informative hints as limitations. The main takeaway is that proactive social robot behavior depends strongly on accurate sensing and well-timed interventions.

## Report

For the full study design, analysis, and discussion, see the [group project report](docs/project-report.pdf).

## Contributors

| Contributor | Contact |
| --- | --- |
| Cilia Nanninga | `nanninga@kth.se` |
| Diogo Paulo | `diogop@kth.se` |
| Helena Westermann | `hewes@kth.se` |
| Hugo Dezerto | `hugoad@kth.se` |
| Maria Carolina Sebastião | `mcms2@kth.se` |

## Acknowledgements

- Furhat Robotics
- KTH Royal Institute of Technology
- Mistral AI
