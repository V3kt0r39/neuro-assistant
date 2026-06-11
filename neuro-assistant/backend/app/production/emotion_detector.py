from math import sqrt

EMOTION_RANGES = {
    "SAD": {"concentration": (0.0, 40.5), "relaxation": (35.0, 100.0)},
    "HAPPY": {"concentration": (77.75, 100.0), "relaxation": (0.0, 15.0)},
    "CALM": {"concentration": (0.0, 13.5), "relaxation": (76.0, 100.0)},
}

EMOTION_CENTERS = {
    "SAD": {"concentration": 40.5, "relaxation": 35.0},
    "HAPPY": {"concentration": 77.75, "relaxation": 15.0},
    "CALM": {"concentration": 13.5, "relaxation": 76.0},
}


def detect_emotion(concentration: float, relaxation: float) -> str:
    # CALM range overlaps with SAD range, so we check CALM first to keep it reachable.
    for emotion in ("CALM", "HAPPY", "SAD"):
        ranges = EMOTION_RANGES[emotion]
        conc_range = ranges["concentration"]
        relax_range = ranges["relaxation"]
        if conc_range[0] <= concentration <= conc_range[1] and relax_range[0] <= relaxation <= relax_range[1]:
            return emotion
    return detect_emotion_by_distance(concentration, relaxation)


def detect_emotion_by_distance(concentration: float, relaxation: float) -> str:
    distances = {}
    for emotion, center in EMOTION_CENTERS.items():
        distance = sqrt(
            (concentration - center["concentration"]) ** 2 + (relaxation - center["relaxation"]) ** 2
        )
        distances[emotion] = distance
    return min(distances, key=distances.get)
