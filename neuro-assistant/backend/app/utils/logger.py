import logging
from logging.config import dictConfig
from pathlib import Path

REQUESTS_LOGGER_NAME = "neuro_requests"
LOGS_DIR = Path(__file__).resolve().parents[2] / "logs"
REQUESTS_LOG_PATH = LOGS_DIR / "requests.log"


def configure_logging(level: str = "INFO") -> None:
    LOGS_DIR.mkdir(exist_ok=True)
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                },
                "requests": {
                    "format": "[%(asctime)s] %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
                "requests_file": {
                    "class": "logging.FileHandler",
                    "formatter": "requests",
                    "filename": str(REQUESTS_LOG_PATH),
                    "encoding": "utf-8",
                },
            },
            "root": {
                "handlers": ["console"],
                "level": level,
            },
            "loggers": {
                REQUESTS_LOGGER_NAME: {
                    "handlers": ["requests_file"],
                    "level": "INFO",
                    "propagate": False,
                }
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def _get_requests_logger() -> logging.Logger:
    return logging.getLogger(REQUESTS_LOGGER_NAME)


def log_incoming(concentration: float, relaxation: float, poor_signal: float) -> None:
    _get_requests_logger().info(
        "INCOMING concentration=%s, relaxation=%s, poor_signal=%s",
        concentration,
        relaxation,
        poor_signal,
    )


def log_rejected(concentration: float, relaxation: float, poor_signal: float, reason: str) -> None:
    _get_requests_logger().warning(
        'REJECTED concentration=%s, relaxation=%s, poor_signal=%s, reason="%s"',
        concentration,
        relaxation,
        poor_signal,
        reason,
    )


def log_processed(
    emotion: str,
    concentration: float,
    relaxation: float,
    global_avg_concentration: float,
    global_avg_relaxation: float,
    recommendation: str,
) -> None:
    snippet = recommendation.replace("\n", " ").strip()
    _get_requests_logger().info(
        'PROCESSED emotion=%s, concentration=%s, relaxation=%s, '
        'global_avg_concentration=%.2f, global_avg_relaxation=%.2f, recommendation="%s"',
        emotion,
        concentration,
        relaxation,
        global_avg_concentration,
        global_avg_relaxation,
        f"{snippet[:120]}..." if len(snippet) > 120 else snippet,
    )
