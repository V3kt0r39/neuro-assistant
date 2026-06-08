import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from app.production.recommendation_engine import get_ai_recommendation


async def main() -> None:
    recommendation = await get_ai_recommendation(
        emotion="CALM",
        concentration=55,
        relaxation=70,
    )
    print("Ollama connection is working.")
    print(f"Recommendation: {recommendation}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:  # noqa: BLE001
        print(f"Ollama connection failed: {exc}")
        raise