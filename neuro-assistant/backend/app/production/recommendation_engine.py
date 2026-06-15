import httpx

from app.config import get_settings
from app.production.emotion_detector import detect_emotion
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


def build_prompt(
    concentration: float,
    relaxation: float,
    emotion: str,
    global_avg_concentration: float,
    global_avg_relaxation: float,
) -> str:
    conc_diff = concentration - global_avg_concentration
    relax_diff = relaxation - global_avg_relaxation
    return (
        "You are a professional psychological AI assistant. "
        "User's current neurointerface data: "
        f"Concentration = {concentration:.2f}%, Relaxation = {relaxation:.2f}%. "
        f"Detected emotional state: {emotion}. "
        "Global baseline (from all records in DB): "
        f"avg_concentration={global_avg_concentration:.2f}%, "
        f"avg_relaxation={global_avg_relaxation:.2f}%. "
        "Deviation from baseline: "
        f"concentration {conc_diff:+.2f}%, relaxation {relax_diff:+.2f}%. "
        "Provide a short, supportive psychological recommendation considering "
        "the current state vs global baseline. Keep it under 50 words. No markdown."
    )


async def get_ai_recommendation(
    concentration: float,
    relaxation: float,
    global_avg_concentration: float,
    global_avg_relaxation: float,
    emotion_ranges: dict[str, dict[str, tuple[float, float]]] | None = None,
    emotion_centers: dict[str, dict[str, float]] | None = None,
) -> dict[str, str | dict[str, float]]:
    emotion = detect_emotion(
        concentration=concentration,
        relaxation=relaxation,
        emotion_ranges=emotion_ranges,
        emotion_centers=emotion_centers,
    )
    conc_diff = concentration - global_avg_concentration
    relax_diff = relaxation - global_avg_relaxation
    payload = {
        "model": settings.model_name,
        "prompt": build_prompt(
            concentration=concentration,
            relaxation=relaxation,
            emotion=emotion,
            global_avg_concentration=global_avg_concentration,
            global_avg_relaxation=global_avg_relaxation,
        ),
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
        response = await client.post(settings.ollama_url, json=payload)
        response.raise_for_status()

    response_data = response.json()
    recommendation = str(response_data.get("response", "")).strip()
    if not recommendation:
        raise ValueError("Ollama returned an empty recommendation.")

    logger.info(
        "AI recommendation generated: emotion=%s concentration=%.2f relaxation=%.2f",
        emotion,
        concentration,
        relaxation,
    )
    return {
        "emotion": emotion,
        "recommendation": recommendation,
        "deviation": {
            "concentration": round(conc_diff, 2),
            "relaxation": round(relax_diff, 2),
        },
    }
