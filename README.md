# 🏀 Ecoach Project: The Tactical Cortex

**The AI-powered assistant coach that turns "Coach Speak" into winning rotations.**

The **Tactical Cortex** is a high-performance decision support system for NBA coaching staffs. It bridges the gap between raw player data and real-time game situations by using **Gemini 2.0 Flash** to interpret natural language and **Google OR-Tools** to solve complex substitution puzzles.

---

## 🧠 How It Works: The Workflow



1.  **The Directive**: The head coach provides a command (e.g., *"We need to space the floor and stop their transition game"*).
2.  **Semantic Mapping**: The `TacticalTranslator` uses Gemini to translate that intent into statistical targets (e.g., `3P%`, `STL`, and `DRB`).
3.  **The Solver**: The `solver.py` runs a **Constraint Programming (CP-SAT)** model. It calculates the optimal 5-man unit by maximizing the target stats while respecting positional constraints and foul trouble.
4.  **The Verdict**: The system suggests the best "Sub-In/Sub-Out" pair and provides an AI-generated tactical rationale.

---

## 🛠️ The Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Interface** | Streamlit | The "War Room" Dashboard |
| **LLM** | Gemini 2.0 Flash | Natural Language Processing & Tactical Reasoning |
| **Optimization** | Google OR-Tools | Multi-objective substitution solver |
| **Data** | Pandas / NumPy | Real-time stat processing |
| **Assets** | Custom CSS & NBA API | Immersive "Court-side" UI and headshots |

---

## 📂 Project Structure

* `app.py`: The main entry point. Orchestrates the UI and live game state.
* `translator.py`: The brain. Converts English coaching prompts into mathematical weights.
* `solver.py`: The engine. Uses linear programming to find the best lineup delta.
* `styles.py`: The aesthetics. Custom CSS to give the app that high-stakes NBA feel.
* `nba_faces.py`: Utility script to fetch official headshots for the bench.
* `player_stats.csv`: The knowledge base containing full seasonal averages.

---

## 🚀 Getting Started

### 1. Requirements
Ensure you have a Google AI API Key (for Gemini).

### 2. Installation
```bash
# Clone the repo
git clone [https://github.com/yourusername/ecoach-project.git](https://github.com/yourusername/ecoach-project.git)

# Install dependencies
pip install streamlit google-generativeai ortools pandas numpy
