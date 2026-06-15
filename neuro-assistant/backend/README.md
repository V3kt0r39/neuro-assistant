# Neuro Assistant Backend
Production FastAPI service that receives EEG metrics and returns an AI-generated psychological recommendation based on current input and global baseline from PostgreSQL.

## What this service does
- Accepts runtime EEG data: `concentration`, `relaxation`, `poor_signal`.
- Rejects noisy signals when `poor_signal > POOR_SIGNAL_THRESHOLD`.
- Reads all records from `data_original` to compute global averages.
- Builds emotion ranges (`SAD`, `HAPPY`, `CALM`) dynamically from raw `data_original` records using the concept formula, then detects emotion.
- Calls Ollama to generate a short recommendation.
- Exposes emotion sampling ranges via `GET /api/ranges` for neurointerface calibration and testing.
- Exposes calibration configuration ranges via `GET /api/calibration-range` for neurointerface testing setup.
- Logs all request outcomes to `logs/requests.log`.

## Current project state (important)
- Active API in runtime: `POST /api/analyze`, `GET /api/ranges`, `GET /api/calibration-range`.
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
8. `GET /api/ranges` queries `data_original` and returns the current emotion detection ranges, centers, and global averages — useful for neurointerface calibration and testing.
9. `GET /api/calibration-range` returns valid parameter ranges and thresholds for neurointerface testing configuration.

## Repository structure
```text
backend/
├── app/
│   ├── api/
│   │   ├── routes_analyze.py       # active production endpoint
│   │   ├── routes_ranges.py        # GET /api/ranges — emotion sampling ranges
│   │   ├── routes_calibration_range.py  # GET /api/calibration-range — testing config
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

## Emotion sampling ranges (`GET /api/ranges`)
Returns the dynamically computed emotion detection ranges and centers used by the neurointerface for calibration and testing.

### How it works
- `app/api/routes_ranges.py` calls `get_global_averages()` and `get_emotion_profile_from_raw_data()`.
- The profile is built from all `(concentration, relaxation)` pairs in `data_original`.
- Points are classified into SAD/HAPPY/CALM buckets based on global average.
- Bucket means become emotion centers; ranges are derived from the concept formula.

### Response schema
```json
{
  "status": "success",
  "global_average": {
    "concentration": 54.23,
    "relaxation": 48.75,
    "total_records": 7653
  },
  "emotion_ranges": {
    "SAD": {
      "concentration": [40.5, 77.75],
      "relaxation": [35.0, 76.0]
    },
    "HAPPY": {
      "concentration": [77.75, 100.0],
      "relaxation": [0.0, 15.0]
    },
    "CALM": {
      "concentration": [0.0, 13.5],
      "relaxation": [76.0, 100.0]
    }
  },
  "emotion_centers": {
    "SAD": { "concentration": 40.5, "relaxation": 35.0 },
    "HAPPY": { "concentration": 77.75, "relaxation": 15.0 },
    "CALM": { "concentration": 13.5, "relaxation": 76.0 }
  }
}
```

### Response fields
- `global_average`: current global baseline from `data_original`.
- `emotion_ranges`: per-emotion `concentration` and `relaxation` interval `["lower", "upper"]`.
- `emotion_centers`: per-emotion centroid point `(concentration, relaxation)`.
- If `data_original` is empty, default hardcoded ranges are returned.

## Calibration configuration ranges (`GET /api/calibration-range`)
Returns the valid configuration ranges and parameters for testing the neurointerface. This endpoint provides the input parameter boundaries, step sizes, and current global averages needed to configure test scenarios.

### How it works
- `app/api/routes_calibration_range.py` queries `get_global_averages()` to fetch current baseline.
- Returns predefined valid ranges for `concentration`, `relaxation`, and `poor_signal` parameters.
- Includes the `poor_signal_threshold` from configuration.
- Returns current global averages and total record count from the database.

### Response schema
```json
{
  "status": "success",
  "concentration": {
    "min": 0.0,
    "max": 100.0,
    "step": 0.1,
    "unit": "%"
  },
  "relaxation": {
    "min": 0.0,
    "max": 100.0,
    "step": 0.1,
    "unit": "%"
  },
  "poor_signal": {
    "min": 0.0,
    "max": 100.0,
    "step": 1.0,
    "unit": "%"
  },
  "poor_signal_threshold": 25,
  "global_average": {
    "concentration": 54.23,
    "relaxation": 48.75
  },
  "total_records": 7653
}
```

### Response fields
- `concentration`: valid range for concentration parameter (min, max, step, unit).
- `relaxation`: valid range for relaxation parameter (min, max, step, unit).
- `poor_signal`: valid range for poor_signal parameter (min, max, step, unit).
- `poor_signal_threshold`: current threshold for signal rejection (from `POOR_SIGNAL_THRESHOLD` env var).
- `global_average`: current global baseline from `data_original`.
- `total_records`: total number of records in `data_original`.

## API reference
### `GET /`
Returns service message and docs path.

### `GET /health`
Returns `{"status": "ok"}`.

### `GET /api/ranges`
Returns emotion sampling ranges, centers, and global averages for neurointerface calibration.

### `GET /api/calibration-range`
Returns configuration ranges for neurointerface testing setup, including valid parameter ranges, thresholds, and current global averages.

#### Success `200`
```json
{
  "status": "success",
  "concentration": {
    "min": 0.0,
    "max": 100.0,
    "step": 0.1,
    "unit": "%"
  },
  "relaxation": {
    "min": 0.0,
    "max": 100.0,
    "step": 0.1,
    "unit": "%"
  },
  "poor_signal": {
    "min": 0.0,
    "max": 100.0,
    "step": 1.0,
    "unit": "%"
  },
  "poor_signal_threshold": 25,
  "global_average": {
    "concentration": 54.23,
    "relaxation": 48.75
  },
  "total_records": 7653
}
```

#### Success `200`
```json
{
  "status": "success",
  "global_average": {
    "concentration": 54.23,
    "relaxation": 48.75,
    "total_records": 7653
  },
  "emotion_ranges": {
    "SAD": { "concentration": [40.5, 77.75], "relaxation": [35.0, 76.0] },
    "HAPPY": { "concentration": [77.75, 100.0], "relaxation": [0.0, 15.0] },
    "CALM": { "concentration": [0.0, 13.5], "relaxation": [76.0, 100.0] }
  },
  "emotion_centers": {
    "SAD": { "concentration": 40.5, "relaxation": 35.0 },
    "HAPPY": { "concentration": 77.75, "relaxation": 15.0 },
    "CALM": { "concentration": 13.5, "relaxation": 76.0 }
  }
}
```

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
### Get emotion sampling ranges
```bash
curl http://localhost:8000/api/ranges
```

### Get calibration configuration ranges
```bash
curl http://localhost:8000/api/calibration-range
```

### Success path (analyze)
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
- `app/main.py` currently mounts only `routes_analyze`, `routes_ranges`, and `routes_calibration_range`.
- Deprecated modules are intentionally left for compatibility/history but are not part of active runtime flow.
- If you re-enable calibration endpoints, update `main.py`, validators, and README together.
