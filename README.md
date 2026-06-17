Neuro Assistant — complete neural interface system

This project is a **client-server platform** for collecting, processing and analyzing electroencephalogram (EEG) data using a **NeuroSky MindWave** headset. The system consists of two main parts:

- Unity client** — provides headset connectivity, real-time visualization of signals, and sending metrics to the server.
- Backend (FastAPI)** — accepts data, filters noise, calculates emotional state (SAD/HAPPY/CALM) from a global base, generates psychological recommendations via a local LLM (Ollama), and provides an API for calibration.

The project is developed within the framework of the YUI research prototype and is intended for use in educational, therapeutic and game scenarios where adaptive feedback on the user’s psycho-emotional state is required.

Main features

- Connect to NeuroSky MindWave** via ThinkGear Connector (TCP port 13854).
- Real time** — display of attention, meditation, raw signal, noise level and spectral bands.
- Intelligent noise filter** — drop packets with `poor_signal > 25%` to protect against artifacts.
- Dynamic determination of emotions** based on global average of all entries in the database (emotional centers and ranges are recalculated automatically).
- Generate text recommendations** using Ollama (model `DistilQwen3-1.7B-uncensored` or any other).
- Two auxiliary endpoints** for interface configuration and testing:
  - `GET /api/ranges` — returns the current emotional ranges and centers.
  - `GET /api/calibration-range` — returns valid parameter ranges and noise threshold.
- Full logging** of all incoming requests, deviations and successful processing in `logs/requests.log`.

Backend (FastAPI)

Technology stack
- Python 3.10+
- FastAPI + Uvicorn
- SQLAlchemy (async) + asyncpg
- Pydantic + Pydantic-Settings
- httpx (for Ollama requests)
- Logging via standard `logging`

Request processing workflow (`POST /api/analyze`)

1. Validation of incoming JSON**:
   ```json
   {
     "concentration": 0..100,
     "relaxation": 0..100,
     "poor_signal": 0..100
   }

2. Noise filter: if poor_signal > POOR_SIGNAL_THRESHOLD (default 25), HTTP 400 returns with details.

3. Calculate the global average of the entire data_original table (SUM, COUNT aggregates).

4. Building an emotional profile:

· All points (concentration, relaxation) from the database are classified relative to the global average.
· Centers for each class are calculated (SAD, HAPPY, CALM).
·Based on the centers, ranges are constructed according to the formula (see emission_detector.py).

5. Determining emotion for current values: first checking for falling into ranges (order CALM - > HAPPY - > SAD), in the absence - Euclidean distance to centers.

6. Recommendation generation:

· Prompt is formed with current values, emotion, global means and deviations.
· Sends a POST request to Ollama (OLLAMA_URL + MODEL_NAME).
· Timeout is set via OLLAMA_TIMEOUT_SECONDS.

7. Logging:

· INCOMING — upon receipt of the request.
· REJECTED — when deflected due to noise.
PROCESSED — when processed successfully (contains emotion, recommendation, global averages).

8. Structured JSON return:
--------------------------------------------------------------
{
  "status": "success",
  "detected_emotion": "SAD|HAPPY|CALM",
  "ai_recommendation": "...",
  "current_state": {"concentration": ..., "relaxation": ... },
  "global_average": {"concentration": ..., "relaxation": ..., "total_records":... },
  "deviation": {"concentration": ..., "relaxation": ... }
}
--------------------------------------------------------------
Auxiliary endpoints

· GET /api/ranges — returns:
· Global average (concentration, relaxation, total_records).
· Emotional ranges (min/max for concentration and relaxation) for SAD, HAPPY, CALM.
· Emotional centers (class center coordinates).

GET /api/calibration-range — returns:
· Valid ranges for concentration, relaxation, poor_signal (min/max/step/unit).
· Current noise threshold (poor_signal_threshold).
· Global average and total number of entries.

Database

The data_original table with the following structure is used:

· id (SERIAL PRIMARY KEY)
· user_id (INT)
· concentration (FLOAT)
· relaxation (FLOAT)
· recorded_at (TIMESTAMP)

Important: DB entry is disabled in the current specification (DB_WRITE_ENABLED=false). The server is read-only — this is to simplify and prevent duplication of data (writing is done by other components, such as parsers). If necessary, you can enable the record by changing the flag in.env and adding the corresponding code in routes_analyze.py (there is no record in the current implementation).

Configuration (.env file)
--------------------------------------------------------------
APP_NAME=Neuro Assistant API
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false

DATABASE_URL=postgresql+asyncpg://neuro_user:YourStrongPassword123!@localhost:5432/eeg_data

OLLAMA_URL=http://localhost:11434/api/generate
MODEL_NAME=DistilQwen3-1.7B-uncensored:latest
OLLAMA_TIMEOUT_SECONDS=30

POOR_SIGNAL_THRESHOLD=25
DB_WRITE_ENABLED=false
--------------------------------------------------------------

Unity client

The Unity project provides a graphical interface for working with the MindWave headset and sending data to the backend.

Key components
· TGCConnectionController
· Manages a TCP connection to ThinkGear Connector (127.0.0.1:13854).
· Includes output of raw JSON packets.
Parsit the incoming data in a separate thread and causes events on the Unity main thread.

· Events:
· UpdatePoorSignalEvent, UpdateAttentionEvent, UpdateMeditationEvent,
· UpdateRawdataEvent, UpdateBlinkEvent,
· as well as events for all spectral bands (Delta, Theta, LowAlpha, HighAlpha, LowBeta, HighBeta, LowGamma, HighGamma).

DisplayData
· Simple Debug UI Based OnGUI.
· Displays the current values of all metrics.
· Shows the signal status icon (depending on poorSignal).
· Provides Connect/Disconnect buttons.

MindWaveHttpSender
· Listens to Attention, Meditation, PoorSignal events.
· Sends them to the backend via HTTP POST with Send Interval (in seconds).
· Field mapping: attachment → concentration, meditation → relaxation, poorSignal → poor_signal.
· Automatically skips sending if poorSignal >= 200 (unstable connection).
· Allows you to enable query and response logging.
· Supports the display of the response from the server (status, emotion, recommendation, etc).

PreserveGameObject
· Simple component that calls DontDestroyOnLoad to save object between scenes.

Unity project structure
The project must be opened from the root folder where the Assets/folder is located.
Expected structure:
--------------------------------------------------------------
YUI/
  Assets/
    NeuroSkyAssets/ <-- necessarily inside Assets, not Assets/Assets/NeuroSkyAssets!
      NeuroSkyScripts/
      NeuroSkySignalIcons/
      NeuroSkyTGCCController/
      Scenes/
  Packages/
  ProjectSettings/
--------------------------------------------------------------

Interaction Unity <-> Backend
1. The Unity client connects to ThinkGear Connector and receives the data stream.
2. MindWaveHttpSender periodically generates a JSON of the following type:
--------------------------------------------------------------
{"concentration": 65, "relaxation": 42, "poor_signal": 0 }
--------------------------------------------------------------

3. Sends a POST request to the endpoint specified in endpointUrl (for example, http://127.0.0.1:8000/api/analyze).
4. The backend processes the request (as described above) and returns a response.
5. Unity can display the received emotion and recommendation (response fields are displayed in the interface).

All settings (URL, sending interval, logging flags) are available in the Unity inspector.

Installation and startup
Requirements

Python 3.10+ (for Backend)
· PostgreSQL (Local or Remote)
· Ollama (with model loaded, e.g. DistilQwen3-1.7B-uncensored)
Unity 2022.3 LTS (or compatible version)
· ThinkGear Connector (running on Windows, macOS, Linux)
· NeuroSky MindWave (or compatible headset)

Running the backend
1. Clone the repository and go to the backend folder.
2. Create a virtual environment and activate it:
--------------------------------------------------------------
python -m venv venv
source venv/bin/active # Linux/macOS
venv\Scripts\activate # Windows
--------------------------------------------------------------

3. Set dependencies:
--------------------------------------------------------------
pip install -r requirements.txt
--------------------------------------------------------------

4. Create a.env file based on.env.example and specify the correct parameters for connecting to the database, Ollama and noise threshold.
5. Make sure PostgreSQL is running and the data_original table exists. If not — create it manually (the structure above) or use the old parser_bd.py script (but it is not recommended for use).
6. Check access to the database:
--------------------------------------------------------------
python scripts/init_database.py
--------------------------------------------------------------

7. Check the connection with Ollama (optional):
--------------------------------------------------------------
python scripts/test_ollama.py
--------------------------------------------------------------

8. Start the server:
--------------------------------------------------------------
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
--------------------------------------------------------------

Setting up and running the Unity client
1. Open Unity Hub and add a project by selecting the root folder (the one where Assets/, Packages/, ProjectSettings/are located).
· Do not open Assets folder/as project!
2. Make sure the Assets/NeuroSkyAssets/folder is present.
3. Open the Assets/NeuroSkyAssets/Scenes/TheScene.unity scene.
4. Start ThinkGear Connector and connect the headset.
5. In the site inspector with MindWaveHttpSender, specify the correct endpointUrl (for example, http://127.0.0.1:8000/api/analyze).
8. Click Play on Unity. If necessary, click the Connect button in the DisplayData interface.

Watch the data update. Sending to the server will occur automatically at a specified interval.

API documentation (briefly)
Detailed documentation is available in Swagger: http://localhost:8000/docs.
The main endpoints are:

Method | Path | Description
--------------------------------------------------------------
POST | /api/analyze | Accepts EEG data, returns emotion and recommendation.
GET | /api/ranges | Returns current emotional ranges and centers.
GET | /api/calibration-range | Returns valid parameter bounds and noise threshold.
GET | / | Welcome Message and Link to/docs.
GET | /health | Health Check (ok status).
--------------------------------------------------------------

Example of a successful response (/api/analyze):
--------------------------------------------------------------
{
  "status": "success",
  "detected_emotion": "CALM",
  "ai_recommendation": "You are in a state of calm. Keep breathing evenly.",
  "current_state": {"concentration": 30, "relaxation": 70},
  "global_average": {"concentration": 54.23, "relaxation": 48.75, "total_records": 7653},
  "deviation": {"concentration": -24.23, "relaxation": 21.25 }
}
--------------------------------------------------------------

An example of a response at high noise levels (HTTP 400) is
--------------------------------------------------------------
{
  "status": "error",
  "error": "high_interference",
  "message": "Interference level is too high. Please just your headset.",
  "details": {"concentration": 30, "relaxation": 20, "poor_signal": 30}
}
--------------------------------------------------------------

Logging
All events are written to the file backend/logs/requests.log in the following format:
--------------------------------------------------------------
[2025-01-01 12:00:00] INCOMING concentration=30.0, relaxation=20.0, poor_signal=15.0
[2025-01-01 12:00:01] REJECTED concentration=30.0, relaxation=20.0, poor_signal=30.0, reason="high_interference"
[2025-01-01 12:00:02] PROCESSED emission=CALM, concentration=30.0, relaxation=70.0, global_avg_concentration=54.23, global_avg_relaxation=48.75, recommendation="You are in a state of calm..."
--------------------------------------------------------------

The logging layer is controlled by the DEBUG parameter in.env.

Legacy components and notes
parser_bd.py — is an old script that ran a separate server on port 8822 and wrote directly to the database. It is not used in the current version. All functionality has been transferred to the FastAPI backend.
· Calibration endpoints (/api/calibrate,/api/calculate-ranges,/api/thresholds) are marked as deprecated and return HTTP 410. They are left for compatibility, but are not actively involved.
· The entry in the database in the current implementation is disabled (DB_WRITE_ENABLED=false). If necessary, you can modify routes_analyze.py by inserting an entry after successful processing.

Development and revision
· Add new Ollama model — change MODEL_NAME to.env. Make sure the model is loaded into Ollama.
· Change Noise Threshold — edit POOR_SIGNAL_THRESHOLD.
Emotional ranges setting — logic fully dynamic based on data from the database. To change the formula, refer to the function _build_ranges_from_centers in emotion_detector.py.
· Testing — use pytest (tests not included in current version but may be added).
