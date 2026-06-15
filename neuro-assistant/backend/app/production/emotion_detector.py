from math import sqrt
from typing import TypedDict


EmotionRanges = dict[str, dict[str, tuple[float, float]]]
EmotionCenters = dict[str, dict[str, float]]


class EmotionProfile(TypedDict):
    ranges: EmotionRanges
    centers: EmotionCenters


DEFAULT_EMOTION_RANGES: EmotionRanges = {
    "SAD": {"concentration": (0.0, 40.5), "relaxation": (35.0, 100.0)},
    "HAPPY": {"concentration": (77.75, 100.0), "relaxation": (0.0, 15.0)},
    "CALM": {"concentration": (0.0, 13.5), "relaxation": (76.0, 100.0)},
}
DEFAULT_EMOTION_CENTERS: EmotionCenters = {
    "SAD": {"concentration": 40.5, "relaxation": 35.0},
    "HAPPY": {"concentration": 77.75, "relaxation": 15.0},
    "CALM": {"concentration": 13.5, "relaxation": 76.0},
}


def _clamp_percent(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _normalized_range(lower: float, upper: float) -> tuple[float, float]:
    low, high = sorted((_clamp_percent(lower), _clamp_percent(upper)))
    return (round(low, 2), round(high, 2))


def _mean(values: list[tuple[float, float]]) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    concentration_sum = sum(point[0] for point in values)
    relaxation_sum = sum(point[1] for point in values)
    count = len(values)
    return (concentration_sum / count, relaxation_sum / count)


def _build_ranges_from_centers(centers: EmotionCenters) -> EmotionRanges:
    # Formula follows the concept spreadsheet:
    # SAD concentration: [sad_avg_concentration, happy_avg_concentration]
    # SAD relaxation:    [sad_avg_relaxation, calm_avg_relaxation]
    # HAPPY concentration: [happy_avg_concentration, 100]
    # HAPPY relaxation:    [0, happy_avg_relaxation]
    # CALM concentration:  [0, calm_avg_concentration]
    # CALM relaxation:     [calm_avg_relaxation, 100]
    sad_center = centers["SAD"]
    happy_center = centers["HAPPY"]
    calm_center = centers["CALM"]
    return {
        "SAD": {
            "concentration": _normalized_range(
                sad_center["concentration"],
                happy_center["concentration"],
            ),
            "relaxation": _normalized_range(
                sad_center["relaxation"],
                calm_center["relaxation"],
            ),
        },
        "HAPPY": {
            "concentration": _normalized_range(happy_center["concentration"], 100.0),
            "relaxation": _normalized_range(0.0, happy_center["relaxation"]),
        },
        "CALM": {
            "concentration": _normalized_range(0.0, calm_center["concentration"]),
            "relaxation": _normalized_range(calm_center["relaxation"], 100.0),
        },
    }


def build_emotion_profile_from_points(points: list[tuple[float, float]]) -> EmotionProfile:
    if not points:
        return {
            "ranges": DEFAULT_EMOTION_RANGES,
            "centers": DEFAULT_EMOTION_CENTERS,
        }

    global_avg_concentration, global_avg_relaxation = _mean(points)
    happy_points: list[tuple[float, float]] = []
    calm_points: list[tuple[float, float]] = []
    sad_points: list[tuple[float, float]] = []

    for concentration, relaxation in points:
        if concentration >= global_avg_concentration and relaxation <= global_avg_relaxation:
            happy_points.append((concentration, relaxation))
        elif concentration <= global_avg_concentration and relaxation >= global_avg_relaxation:
            calm_points.append((concentration, relaxation))
        else:
            sad_points.append((concentration, relaxation))

    sad_concentration, sad_relaxation = _mean(sad_points) if sad_points else (
        global_avg_concentration,
        global_avg_relaxation,
    )
    happy_concentration, happy_relaxation = _mean(happy_points) if happy_points else (
        DEFAULT_EMOTION_CENTERS["HAPPY"]["concentration"],
        DEFAULT_EMOTION_CENTERS["HAPPY"]["relaxation"],
    )
    calm_concentration, calm_relaxation = _mean(calm_points) if calm_points else (
        DEFAULT_EMOTION_CENTERS["CALM"]["concentration"],
        DEFAULT_EMOTION_CENTERS["CALM"]["relaxation"],
    )

    centers: EmotionCenters = {
        "SAD": {
            "concentration": round(_clamp_percent(sad_concentration), 2),
            "relaxation": round(_clamp_percent(sad_relaxation), 2),
        },
        "HAPPY": {
            "concentration": round(_clamp_percent(happy_concentration), 2),
            "relaxation": round(_clamp_percent(happy_relaxation), 2),
        },
        "CALM": {
            "concentration": round(_clamp_percent(calm_concentration), 2),
            "relaxation": round(_clamp_percent(calm_relaxation), 2),
        },
    }
    return {
        "ranges": _build_ranges_from_centers(centers),
        "centers": centers,
    }


def detect_emotion(
    concentration: float,
    relaxation: float,
    emotion_ranges: EmotionRanges | None = None,
    emotion_centers: EmotionCenters | None = None,
) -> str:
    ranges_map = emotion_ranges or DEFAULT_EMOTION_RANGES

    # CALM range may overlap SAD range, so CALM is checked first.
    for emotion in ("CALM", "HAPPY", "SAD"):
        ranges = ranges_map[emotion]
        conc_range = ranges["concentration"]
        relax_range = ranges["relaxation"]
        if conc_range[0] <= concentration <= conc_range[1] and relax_range[0] <= relaxation <= relax_range[1]:
            return emotion
    return detect_emotion_by_distance(
        concentration=concentration,
        relaxation=relaxation,
        emotion_centers=emotion_centers,
    )


def detect_emotion_by_distance(
    concentration: float,
    relaxation: float,
    emotion_centers: EmotionCenters | None = None,
) -> str:
    centers_map = emotion_centers or DEFAULT_EMOTION_CENTERS
    distances = {}
    for emotion, center in centers_map.items():
        distance = sqrt(
            (concentration - center["concentration"]) ** 2 + (relaxation - center["relaxation"]) ** 2
        )
        distances[emotion] = distance
    return min(distances, key=distances.get)
