# Neuro Assistant Backend
Production FastAPI service that receives EEG metrics and returns an AI-generated psychological recommendation based on current input and global baseline from PostgreSQL.

## What this service does
- Accepts runtime EEG data: `concentration`, `relaxation`, `poor_signal`.
- Rejects noisy signals when `poor_signal > POOR_SIGNAL_THRESHOLD`.
- Reads all records from `data_original` to compute global averages.
- Builds emotion ranges (`SAD`, `HAPPY`, `CALM`) dynamically from raw `data_original` records using the concept formula, then detects emotion.
- Calls Ollama to generate a short recommendation.
- Logs all request outcomes to `logs/requests.log`.

## Current project state (important)
- Active API in runtime: `POST /api/analyze`.
- Health/system endpoints: `GET /`, `GET /health`.
- Calibration/admin endpoints exist in codebase but are deprecated in current specification (`routes_calibration.py`, `routes_admin.py`) and are not mounted by `app/main.py`.
- Analyze flow is read-only for database writes (it only reads `data_original`).

## High-level architecture
1. Client sends `POST /api/analyze`.
2. `app/api/routes_analyze.py` validates payload and logs `INCOMING`.
3. If high interference (`poor_signal > threshold`): logs `REJECTED`, returns HTTP 400.
4. Otherwise `app/utils/statistics.py` aggregates `SUM`/`COUNT` from `data_original`.
5. `app/production/emotion_detector.py` determines emotion.
6. `app/production/recommendation_engine.py` builds prompt and calls Ollama.
7. Route logs `PROCESSED` and returns structured JSON response.

## Repository structure
```text
backend/
├── app/
│   ├── api/
│   │   ├── routes_analyze.py       # active production endpoint
│   │   ├── routes_admin.py         # deprecated
│   │   ├── routes_calibration.py   # deprecated
│   │   └── routes_production.py    # compatibility alias
│   ├── calibration/                # deprecated implementation stubs
│   ├── database/
│   │   ├── connection.py           # async SQLAlchemy engine/session
│   │   └── models.py               # DataOriginal model
│   ├── production/
│   │   ├── emotion_detector.py     # range + distance logic
│   │   └── recommendation_engine.py# Ollama integration
│   ├── utils/
│   │   ├── logger.py               # app + requests logging
│   │   ├── statistics.py           # global averages over data_original
│   │   └── validators.py           # Pydantic request/response schemas
│   ├── config.py                   # env-based settings
│   └── main.py                     # FastAPI app entry point
├── logs/
│   └── requests.log
├── scripts/
│   ├── init_database.py            # connectivity/read-only DB check
│   ├── test_ollama.py              # Ollama call smoke test
│   └── add_calibration_users.py    # deprecated helper
└── requirements.txt
```

## Runtime request flow (`POST /api/analyze`)
### Input
Payload schema:
- `concentration`: float, 0..100
- `relaxation`: float, 0..100
- `poor_signal`: float, 0..100

### Interference gate
- Config source: `POOR_SIGNAL_THRESHOLD` (default `25`).
- Condition: `poor_signal > threshold`.
- Behavior:
  - returns `400 Bad Request`
  - payload:
    - `status: "error"`
    - `error: "high_interference"`
    - `message: "Interference level is too high. Please adjust your headset."`
    - `details`: original request values
  - writes `REJECTED` log entry

### DB baseline calculation
`app/utils/statistics.py` executes aggregate query over `data_original`:
- `SUM(concentration)`
- `SUM(relaxation)`
- `COUNT(*)`
Then computes:
- `avg_concentration = sum_concentration / count`
- `avg_relaxation = sum_relaxation / count`
- rounded to 2 decimals
- safe zero handling when table is empty

### Emotion detection
`app/utils/statistics.py` + `app/production/emotion_detector.py`:
- Reads all raw pairs `(concentration, relaxation)` from `data_original`.
- Computes global average concentration/relaxation.
- Splits points into buckets:
  - `HAPPY`: concentration >= global_avg_concentration and relaxation <= global_avg_relaxation
  - `CALM`: concentration <= global_avg_concentration and relaxation >= global_avg_relaxation
  - `SAD`: all remaining points
- Computes bucket averages (emotion centers), then builds ranges by concept formula:
  - `SAD`: concentration from `sad_avg_concentration` to `happy_avg_concentration`, relaxation from `sad_avg_relaxation` to `calm_avg_relaxation`
  - `HAPPY`: concentration from `happy_avg_concentration` to `100`, relaxation from `0` to `happy_avg_relaxation`
  - `CALM`: concentration from `0` to `calm_avg_concentration`, relaxation from `calm_avg_relaxation` to `100`
- Range check order remains: `CALM`, `HAPPY`, `SAD`.
- If no range match, fallback is Euclidean distance to computed centers.

### Recommendation generation
`app/production/recommendation_engine.py`:
- Builds prompt with:
  - current values
  - detected emotion
  - global averages
  - deviation from baseline
- Calls Ollama endpoint:
  - URL: `OLLAMA_URL`
  - Model: `MODEL_NAME`
  - Timeout: `OLLAMA_TIMEOUT_SECONDS`
- Returns:
  - `emotion`
  - generated recommendation text
  - `deviation` object

## API reference
### `GET /`
Returns service message and docs path.

### `GET /health`
Returns `{"status": "ok"}`.

### `POST /api/analyze`
#### Success `200`
```json
{
  "status": "success",
  "detected_emotion": "SAD",
  "ai_recommendation": "string",
  "current_state": {
    "concentration": 30.0,
    "relaxation": 20.0
  },
  "global_average": {
    "concentration": 54.23,
    "relaxation": 48.75,
    "total_records": 7653
  },
  "deviation": {
    "concentration": -24.23,
    "relaxation": -28.75
  }
}
```

#### High interference `400`
```json
{
  "status": "error",
  "error": "high_interference",
  "message": "Interference level is too high. Please adjust your headset.",
  "details": {
    "concentration": 30.0,
    "relaxation": 20.0,
    "poor_signal": 30.0
  }
}
```

#### Upstream AI failure `502`
Returned when Ollama request fails or returns invalid data.

## Quick start
### 1) Install dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment
Create `.env` in this directory:
```env
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
```

### 3) Check DB access
```bash
python scripts/init_database.py
```
Expected output includes successful read-only check and row count for `data_original`.

### 4) Optional: check Ollama
```bash
python scripts/test_ollama.py
```

### 5) Run API
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Swagger UI: `http://localhost:8000/docs`

## Request examples
### Success path
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"concentration":30,"relaxation":20,"poor_signal":15}'
```

### Rejected by interference
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"concentration":30,"relaxation":20,"poor_signal":30}'
```

## Logging
Request log file: `logs/requests.log`.
Entries:
- `INCOMING concentration=..., relaxation=..., poor_signal=...`
- `REJECTED ... reason="high_interference"`
- `PROCESSED emotion=..., global_avg_concentration=..., global_avg_relaxation=..., recommendation="..."`

## Troubleshooting
### 1) `500` / `502` on analyze
- Check Ollama status and model availability.
- Verify `OLLAMA_URL` and `MODEL_NAME`.
- Check app logs and `logs/requests.log`.

### 2) DB permission errors (`permission denied for table data_original`)
Grant read-only rights to the app user:
```sql
GRANT CONNECT ON DATABASE eeg_data TO neuro_user;
GRANT USAGE ON SCHEMA public TO neuro_user;
GRANT SELECT ON TABLE public.data_original TO neuro_user;
```

### 3) Empty or stale averages
- Ensure `data_original` has records.
- Re-run `python scripts/init_database.py`.

## Notes for maintainers
- `app/main.py` currently mounts only `routes_analyze`.
- Deprecated modules are intentionally left for compatibility/history but are not part of active runtime flow.
- If you re-enable calibration endpoints, update `main.py`, validators, and README together.
