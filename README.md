# WizardOfWor-AiRemake
.
# WizardOfWor – AI Remake (Python)

A 2D remake of **Wizard of Wor** enhanced with **AI-controlled players** and multiple play modes.
Built as a capstone / graduation project focusing on **real-time AI decision making**, **pathfinding**, and a **multithreaded game loop**.

---

## Gameplay & Modes

The game supports multiple modes:

- **Solo / Local Play**
- **Human vs Human**
- **Human vs AI**
- **AI vs AI**
  - **Cooperative:** AI players coordinate and avoid conflicts
  - **Competitive:** AI players behave as opponents and compete for score

Primary goal: **kill monsters, survive, and maximize score** while progressing through levels.

---

## Controls

- **Player1 (Yellow / AIPlayer1 or Human)**
  - Move: **Arrow Keys**
  - Fire: **SPACE**
- **Player2 (Blue / AIPlayer2 or Human)**
  - Move: **WASD**
  - Fire: **F**

> Mode selection and AI vs AI options are available from the in-game menu (depends on current build).

---

## AI Overview

The project includes AI players with behavior such as:

- **Pathfinding (e.g., A\*)** to reach targets / positions
- **Enemy detection + aiming + shooting logic**
- **Real-time decisions** (AI runs in dedicated threads to keep FPS stable)
- Cooperative vs Competitive behavior differences

### AIPlayer1 (Rana)
- Focuses on **engaging the nearest monster**
- Turns to face enemies and fires proactively
- Designed for **fast decision time** in real-time gameplay

### AIPlayer2 / Other AI (Team)
- Includes alternative strategies such as holding positions, scanning directions, and reactive shooting
- (Edit this section according to your current team roles)

---

## Multithreaded Architecture

To improve responsiveness and maintain stable FPS, the game architecture uses separate threads (depending on build), typically for:

- Rendering
- Physics / state updates
- Audio
- Asset loading
- AI decision loop(s)

---

## Project Structure (Typical)

> File names may vary slightly depending on the latest version.

- `main.py` – Entry point / game startup
- `config.ini` – Game configuration
- `ai_player.py` – AI player classes and action logic
- `game_manager.py` – Core loop / thread orchestration (if included)
- `pathfinding_*.py` – Pathfinding implementations (A*, greedy, etc.)
- `Level1.txt`, `Level2.txt` – Level layouts / grids
- `assets/` – Sprites, sounds, other resources (if included)

---

## Requirements

- Python **3.10+** recommended
- Common dependencies may include:
  - `pygame` (if used in your build)

If you have a `requirements.txt`, use it to install dependencies.

---

## Installation

```bash
git clone https://github.com/Rana-inan/wizardofwor-AiRemake.git
cd wizardofwor-AiRemake
python -m venv .venv
