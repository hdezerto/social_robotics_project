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
	- Microphone and speakers

### Usage
To start the game assistant:
```powershell
python main.py
```
For GUI:
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
- `DIOGO_furllionaire-gui/` — Web GUI resources

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
