# Neuro Assistant Backend
FastAPI backend для анализа состояния пользователя по EEG-метрикам концентрации/расслабленности, определения эмоции (SAD/HAPPY/CALM) и генерации рекомендации через Ollama.

## Стек
- Python 3.10+
- FastAPI + Uvicorn
- PostgreSQL
- SQLAlchemy (async)
- Ollama (`DistilQwen3-1.7B-uncensored:latest`)

## Подготовка
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Переменные окружения
Используется файл `.env` в директории `backend/`.

Пример:
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

## Инициализация БД и сиды
```bash
python scripts/init_database.py
python scripts/add_calibration_users.py
python scripts/add_calibration_users.py --include-samples
```

## Запуск API
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Документация Swagger: `http://localhost:8000/docs`

## Основные эндпоинты
- `POST /api/calibrate` — сохранить сырые калибровочные данные
- `POST /api/calculate-ranges` — посчитать AVG/MIN/MAX по эмоциям
- `GET /api/thresholds` — посмотреть рассчитанные пороги
- `POST /api/analyze` — определить эмоцию и получить AI-рекомендацию

## Быстрые запросы
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

## Проверка Ollama
```bash
python scripts/test_ollama.py
```
