# 🧠 Neuro Assistant

### Neural Interface System for Psycho-Emotional Analysis

[![Unity 2022.3](https://img.shields.io/badge/Unity-2022.3_LTS-black?logo=unity)](https://unity.com/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org/)

---

## 🌟 What is Neuro Assistant?

Neuro Assistant is an intelligent **client-server platform** that reads brain signals in real time using the **NeuroSky MindWave** headset, detects your emotional state, and provides personalized AI-powered recommendations.

> Built for education, therapy, and gaming — anywhere adaptive feedback on the user's psycho-emotional state makes a difference.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🎧 **Real-Time EEG** | Connects to NeuroSky MindWave via ThinkGear Connector and streams live brain data |
| 📊 **Live Dashboard** | Displays attention, meditation, raw signal, noise level, and spectral bands in real time |
| 🧹 **Smart Noise Filter** | Automatically rejects noisy packets to ensure clean, reliable readings |
| 💡 **Emotion Detection** | Dynamically classifies your state as **SAD**, **HAPPY**, or **CALM** based on global data patterns |
| 🤖 **AI Recommendations** | Generates personalized text advice via a local LLM (Ollama) |
| 📡 **RESTful API** | Clean endpoints for data analysis, calibration, and range inspection |

---

## 🏗️ Architecture

```
┌──────────────────┐         HTTP POST         ┌──────────────────┐
│                  │  ───────────────────────>  │                  │
│   🎧 Unity App   │                           │  ⚡ FastAPI       │
│   (MindWave)     │  <───────────────────────  │  Backend         │
│                  │        JSON Response       │                  │
└──────────────────┘                           └────────┬─────────┘
                                                        │
                                              ┌─────────▼─────────┐
                                              │   🐘 PostgreSQL   │
                                              │   (EEG Data)     │
                                              └──────────────────┘
                                                        │
                                              ┌─────────▼─────────┐
                                              │   🦙 Ollama LLM   │
                                              │   (Recommendations)│
                                              └──────────────────┘
```

---

## 🚀 Quick Start

### 📋 Prerequisites

- **Python 3.10+**
- **PostgreSQL** (local or remote)
- **Ollama** with a model loaded (e.g., `DistilQwen3-1.7B-uncensored`)
- **Unity 2022.3 LTS**
- **ThinkGear Connector** (Windows / macOS / Linux)
- **NeuroSky MindWave** headset

### ⚡ Backend Setup

```bash
# Navigate to the backend folder
cd neuro-assistant/backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database, Ollama, and threshold settings

# Verify database connection
python scripts/init_database.py

# (Optional) Test Ollama connection
python scripts/test_ollama.py

# Launch the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

🎉 The API is now running at `http://localhost:8000`
📖 Interactive docs: `http://localhost:8000/docs`

### 🎮 Unity Client Setup

1. Open **Unity Hub** → Add project → select the `neuro-assistant/frontend` root folder
2. Ensure `Assets/NeuroSkyAssets/` is present
3. Open the scene: `Assets/NeuroSkyAssets/Scenes/TheScene.unity`
4. Start **ThinkGear Connector** and pair your headset
5. In the inspector, set the `MindWaveHttpSender` endpoint URL (e.g., `http://127.0.0.1:8000/api/analyze`)
6. Press **▶ Play** — click **Connect** in the UI if needed

Data will stream automatically at the configured interval!

---

## 📡 API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Submit EEG data → receive emotion + AI recommendation |
| `GET` | `/api/ranges` | View current emotional ranges and centers |
| `GET` | `/api/calibration-range` | View valid parameter bounds and noise threshold |
| `GET` | `/health` | Server health check |

### 💬 Example Response

```json
{
  "status": "success",
  "detected_emotion": "CALM",
  "ai_recommendation": "You are in a state of calm. Keep breathing evenly.",
  "current_state": { "concentration": 30, "relaxation": 70 },
  "global_average": { "concentration": 54.23, "relaxation": 48.75, "total_records": 7653 },
  "deviation": { "concentration": -24.23, "relaxation": 21.25 }
}
```

---

## 🔧 Configuration

The backend is configured via a `.env` file in the `backend/` directory:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `OLLAMA_URL` | Ollama API endpoint | `http://localhost:11434/api/generate` |
| `MODEL_NAME` | LLM model for recommendations | `DistilQwen3-1.7B-uncensored:latest` |
| `POOR_SIGNAL_THRESHOLD` | Max noise level before rejection | `25` |
| `DEBUG` | Enable detailed logging | `false` |

---

## 📁 Project Structure

```
neuro-assistant/
├── 📄 README.md              ← You are here
├── 📄 LICENSE.md
│
├── 🖥️ backend/               ← FastAPI server & AI engine
│   ├── app/                  ← Application source code
│   ├── scripts/              ← Utility scripts
│   ├── requirements.txt
│   └── .gitignore
│
└── 🎮 frontend/              ← Unity client application
    ├── Assets/               ← Unity scenes, scripts & assets
    ├── Packages/
    ├── ProjectSettings/
    └── .gitignore
```

---

## 🤝 How It Works

1. 🎧 The **Unity client** connects to the NeuroSky headset via ThinkGear Connector
2. 📡 It sends concentration, relaxation, and signal quality data to the backend via HTTP
3. 🧹 The backend **filters out noise** and validates the incoming data
4. 💡 Using global data patterns, it **classifies the emotional state**
5. 🦙 An **LLM generates personalized recommendations** based on your current state
6. 🎮 Unity displays the detected emotion and advice in the interface

---

## 📄 License

See [LICENSE.md](LICENSE.md) for details.

---

<p align="center">Built with 🧠 and ❤️ by the Neuro Assistant Team</p>
