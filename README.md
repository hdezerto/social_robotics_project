## Furhat Game Assistant (Group 6)

**Course:** Social Robotics @ KTH Royal Institute of Technology
**Group Members:** Cilia Nanninga, Diogo Paulo, Helena Westermann, Hugo Dezerto, Maria Sebastião
**Contact:** nanninga, diogop, hewes, hugoad, mcms2 @kth.se

---

### Project Description
The Furhat Game Assistant is an interactive quiz game designed to run on the Furhat social robot platform. It combines speech interaction, a graphical user interface, and a large language model backend to create an engaging experience for users. The system logs experiment data and supports database-driven question management.

### Features
- Quiz game with multiple-choice questions
- Furhat robot speech and interaction
- Graphical user interface (GUI)
- LLM backend for dynamic responses
- Database logging of experiment results
- Modular code structure for easy extension

### Installation
1. **Clone the repository:**
	```
	git clone <repo-url>
	```
2. **Install Python dependencies:**
	```
	pip install -r requirements.txt
	```
3. **Hardware requirements:**
	- Furhat robot (for full functionality)

### Usage
To start the game assistant (launches the Furllionaire web GUI on http://127.0.0.1:5000):
```powershell
python main.py
```
The legacy Tkinter GUI is still available for quick local testing:
```powershell
python gui/quiz_gui.py
```
For debugging Furhat speech:
```powershell
python debug_furhat_speak.py
```

### File Structure
- `main.py` — Main entry point
- `controller/` — Experiment control logic
- `database/` — Question database and management
- `furhat_interface/` — Furhat API integration
- `gui/` — Graphical user interface
- `llm_backend/` — Large language model backend
- `logs/` — Experiment logs
- `gui/web_client/` — Furllionaire web GUI assets served by Flask

### Contributors
- Cilia Nanninga
- Diogo Paulo
- Helena Westermann
- Hugo Dezerto
- Maria Sebastião

### License
This project is for educational purposes as part of the Social Robotics course at KTH.

### Acknowledgements
- Furhat Robotics
- KTH Royal Institute of Technology
- Mistral (for LLM backend)
