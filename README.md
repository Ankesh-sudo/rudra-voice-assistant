# Rudra — Intelligent Voice Assistant 🧠🎙️

Rudra is a **modular, Python-based intelligent voice assistant** designed to run reliably on **Linux systems**.  
The project is built **step-by-step** with a strong emphasis on **architecture, stability, and extensibility**, rather than quick or fragile features.

The long-term vision is to evolve Rudra into an **offline-first, algorithm-driven AI assistant**, capable of system control, memory, and natural interaction across devices.

---

## 🔖 Project Status

**Current Stable Milestone:** ✅ **Day 9 — Input Intelligence & Conversation Stability**

Day 9 focuses entirely on making Rudra **reliable, calm, and frustration-free** during conversations.

✔ Robust input validation  
✔ Confidence-based intent gating  
✔ Active listening with silence handling  
✔ Repeat-safe retry logic  
✔ Stable conversation loop  

> 🚧 **Action-based system control begins from Day 10**

---

## 🚀 Features (Implemented)

### ✅ Core Assistant
- Intent-based command processing
- Modular NLP pipeline
- Short-term & long-term conversational memory
- MySQL-backed persistent storage
- Clean separation of concerns
- Predictable and debuggable execution flow

---

### ✅ Input System (Day 8)
- Voice input using **Google Speech Recognition**
- Text input fallback
- **Push-to-talk** (press ENTER to speak)
- Configurable input mode (voice / text)
- Controlled listening (no always-on microphone)

---

### ✅ Input Intelligence (Day 9)
- Input normalization & validation gate
- Minimum-length and word-count filtering
- Repeat suppression (only for previously accepted inputs)
- Confidence refinement after intent scoring
- Safe handling of unknown intents
- Clear retry prompts (no infinite loops)

---

### ✅ Active Listening & Silence Handling (Day 9)
- Listening state machine (`IDLE → ACTIVE → WAITING`)
- Automatic silence detection
- Context-aware prompts:
  - “I’m listening.”
  - “Going to sleep.”
- No accidental intent execution during silence
- Natural conversational pacing

---

### ✅ Stability & Logging
- Structured logging using **Loguru**
- Detailed debug traces for:
  - Input validation
  - Intent scoring
  - Confidence decisions
- Graceful handling of speech and microphone errors
- Environment-variable based configuration
- Secure `.env` usage (never committed)

---

## 🧠 Project Architecture
core/
├── main.py # Entry point
├── assistant.py # Main assistant loop (state-driven)
├── config.py # Input & environment configuration
├── input_controller.py # Centralized input handling
│
├── input/
│ └── input_validator.py # Input intelligence & repeat control
│
├── speech/
│ └── google_engine.py # Google Speech Recognition engine
│
├── nlp/
│ ├── normalizer.py # Text normalization
│ ├── tokenizer.py # Tokenization
│ └── intent.py # Intent definitions
│
├── intelligence/
│ ├── intent_scorer.py # Rule-based intent scoring
│ └── confidence_refiner.py
│
├── skills/
│ └── basic.py # Skill execution layer
│
├── context/
│ ├── short_term.py # Session memory
│ └── long_term.py # Persistent memory
│
├── storage/
│ ├── mysql.py # Database connection
│ └── models.py # DB models


---

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Speech Engine:** Google Speech Recognition
- **Database:** MySQL
- **Logging:** Loguru
- **OS Target:** Linux (Ubuntu tested)

---

## ▶️ Running the Assistant

```bash
# Activate virtual environment
source venv/bin/activate

# Run Rudra
python3 -m core.main


---
Usage:

Press ENTER → speak

Say commands naturally

Silence is handled automatically

Say exit rudra to quit

🧭 Roadmap (High Level)
Day 10–14: System actions (apps, files, OS control)

Day 15–25: Advanced skills & workflows

Day 26–40: Memory intelligence & personalization

Day 41–60: Offline intent engine & algorithms

Day 61–70: Multi-device sync & Raspberry Pi build

📌 Philosophy
Rudra is not built to demo quickly —
it is built to last, scale, and evolve.

Every feature must be:

Predictable

Debuggable

Extendable

Safe to modify later

📜 License
This project is currently for learning, research, and portfolio purposes.
License will be finalized once the core system stabilizes.

Author: Ankesh
Project: Rudra — Intelligent Voice Assistant