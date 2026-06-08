from dataclasses import dataclass
from math import dist

from app.database.models import EmotionThreshold


@dataclass(slots=True)
class DetectionResult:
    detected_emotion: str
    method: str
    distance: float


def _distance_to_threshold(
    concentration: float,
    relaxation: float,
    threshold: EmotionThreshold,
) -> float:
    return dist((concentration, relaxation), (threshold.conc_avg, threshold.relax_avg))


def detect_emotion(
    concentration: float,
    relaxation: float,
    thresholds: list[EmotionThreshold],
) -> DetectionResult:
    if not thresholds:
        raise ValueError("Emotion thresholds are empty. Run /api/calculate-ranges first.")

    in_range_thresholds = [
        threshold
        for threshold in thresholds
        if threshold.conc_min <= concentration <= threshold.conc_max
        and threshold.relax_min <= relaxation <= threshold.relax_max
    ]

    candidate_thresholds = in_range_thresholds or thresholds
    method = "range" if in_range_thresholds else "distance"

    best_threshold = min(
        candidate_thresholds,
        key=lambda threshold: _distance_to_threshold(concentration, relaxation, threshold),
    )
    best_distance = _distance_to_threshold(concentration, relaxation, best_threshold)
    return DetectionResult(
        detected_emotion=best_threshold.emotion,
        method=method,
        distance=best_distance,
    )