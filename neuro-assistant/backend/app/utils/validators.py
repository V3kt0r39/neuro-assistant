from enum import Enum

from pydantic import BaseModel, Field


class Emotion(str, Enum):
    SAD = "SAD"
    HAPPY = "HAPPY"
    CALM = "CALM"


class CalibrationRequest(BaseModel):
    user_id: int = Field(gt=0)
    concentration: float = Field(ge=0, le=100)
    relaxation: float = Field(ge=0, le=100)
    self_reported_emotion: Emotion


class CalibrationResponse(BaseModel):
    status: str = "success"
    record_id: int


class ThresholdOut(BaseModel):
    emotion: Emotion
    conc_avg: float
    relax_avg: float
    conc_min: float
    conc_max: float
    relax_min: float
    relax_max: float
    sample_count: int


class CalculateRangesResponse(BaseModel):
    status: str = "success"
    thresholds: list[ThresholdOut]


class AnalyzeRequest(BaseModel):
    concentration: float = Field(ge=0, le=100)
    relaxation: float = Field(ge=0, le=100)


class AnalyzeResponse(BaseModel):
    status: str = "success"
    detected_emotion: Emotion
    ai_recommendation: str
    session_token: str
    detection_method: str
    recommendation_source: str