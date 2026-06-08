import httpx

from app.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

_FALLBACK_RECOMMENDATIONS = {
    "SAD": "Take a short pause, breathe deeply for one minute, and focus on one small task you can complete now.",
    "HAPPY": "Keep this momentum by noting what supports your mood and sharing one positive action with someone nearby.",
    "CALM": "Maintain your calm state with slow breathing and a brief mindful check-in before moving to the next task.",
}


def build_prompt(emotion: str, concentration: float, relaxation: float) -> str:
    return (
        "You are a professional psychological AI assistant. "
        f"User's neurointerface data: Concentration = {concentration:.2f}%, "
        f"Relaxation = {relaxation:.2f}%, Detected emotion = {emotion}. "
        "Provide a short, supportive, and actionable psychological recommendation "
        "on how to improve or sustain their emotional state. Keep it under 50 words. "
        "Do not use markdown formatting."
    )


def fallback_recommendation(emotion: str) -> str:
    return _FALLBACK_RECOMMENDATIONS.get(
        emotion,
        "Take three deep breaths, drink some water, and reassess how you feel before continuing.",
    )


async def get_ai_recommendation(emotion: str, concentration: float, relaxation: float) -> str:
    payload = {
        "model": settings.model_name,
        "prompt": build_prompt(emotion, concentration, relaxation),
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
        response = await client.post(settings.ollama_url, json=payload)
        response.raise_for_status()

    response_data = response.json()
    recommendation = str(response_data.get("response", "")).strip()
    if not recommendation:
        raise ValueError("Ollama returned an empty recommendation.")

    logger.info("AI recommendation generated for emotion=%s", emotion)
    return recommendation