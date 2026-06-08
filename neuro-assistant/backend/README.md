# Neuro Assistant Backend
FastAPI backend for analyzing user state based on EEG metrics of concentration/relaxation levels, emotion detection, and AI-powered recommendations.

## Stack
- Python 3.10+
- FastAPI + Uvicorn
- PostgreSQL
- SQLAlchemy (async)
- Ollama (`DistilQwen3-1.7B-uncensored:latest`)

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables
Uses a `.env` file in the `backend/` directory.

Example:
```env
APP_NAME=Neuro Assistant API
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
DATABASE_URL=postgresql+asyncpg://neuro_user:YourStrongPassword123!@localhost/neuro_assistant
OLLAMA_URL=http://localhost:11434/api/generate
MODEL_NAME=DistilQwen3-1.7B-uncensored:latest
OLLAMA_TIMEOUT_SECONDS=30
```

## Database Initialization and Seeds
```bash
python scripts/init_database.py
python scripts/add_calibration_users.py
python scripts/add_calibration_users.py --include-samples
```

## Running the API
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger documentation: `http://localhost:8000/docs`

## Main Endpoints
- `POST /api/calibrate` — save raw calibration data
- `POST /api/calculate-ranges` — calculate AVG/MIN/MAX per emotion
- `GET /api/thresholds` — view calculated thresholds
- `POST /api/analyze` — detect emotion and get AI recommendation

## Quick Requests
```bash
curl -X POST http://localhost:8000/api/calibrate \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "concentration": 41, "relaxation": 35, "self_reported_emotion": "SAD"}'
```

```bash
curl -X POST http://localhost:8000/api/calculate-ranges
```

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"concentration": 30, "relaxation": 20}'
```

## Checking Ollama
```bash
python scripts/test_ollama.py
```
