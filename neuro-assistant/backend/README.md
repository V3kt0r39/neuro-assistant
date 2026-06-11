# Neuro Assistant Backend
FastAPI backend for EEG analysis and AI psychological recommendations via Ollama.

## Core behavior
- Accepts EEG metrics: `concentration`, `relaxation`, `poor_signal`.
- Does **not** accept `user_id` in API requests.
- Logs **all** incoming requests to `logs/requests.log`.
- If `poor_signal > 25`: returns HTTP 400 (`high_interference`), logs `REJECTED`, and stops processing.
- If `poor_signal <= 25`: reads existing raw data from PostgreSQL table `data_original`, calculates global averages, detects emotion (`SAD`/`HAPPY`/`CALM`), and requests recommendation from Ollama.
- Database is used in **read-only** mode for runtime logic (no inserts/updates in analyze flow).

## Stack
- Python 3.10+
- FastAPI + Uvicorn
- PostgreSQL (read-only in runtime flow)
- SQLAlchemy (async)
- Ollama (`DistilQwen3-1.7B-uncensored:latest`)

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Environment variables
Create `.env` in `backend/`:
```env
APP_NAME=Neuro Assistant API
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
DATABASE_URL=postgresql+asyncpg://neuro_user:YourStrongPassword123!@localhost:5432/neuro_assistant
OLLAMA_URL=http://localhost:11434/api/generate
MODEL_NAME=DistilQwen3-1.7B-uncensored:latest
OLLAMA_TIMEOUT_SECONDS=30
POOR_SIGNAL_THRESHOLD=25
DB_WRITE_ENABLED=false
```

## DB connectivity check
```bash
python scripts/init_database.py
```
Checks table `data_original` and prints total records count.

## Run API
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger: `http://localhost:8000/docs`

## Main endpoint
`POST /api/analyze`

Successful request:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"concentration": 30, "relaxation": 20, "poor_signal": 15}'
```

Rejected request:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"concentration": 30, "relaxation": 20, "poor_signal": 30}'
```

## Logs
- `INCOMING` — every request.
- `REJECTED` — high interference requests (`poor_signal > 25`).
- `PROCESSED` — successful analyze flow with emotion, global averages, and recommendation snippet.
