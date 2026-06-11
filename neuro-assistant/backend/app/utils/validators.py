from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    concentration: float = Field(ge=0, le=100)
    relaxation: float = Field(ge=0, le=100)
    poor_signal: float = Field(ge=0, le=100)


class CurrentState(BaseModel):
    concentration: float
    relaxation: float


class GlobalAverage(BaseModel):
    concentration: float
    relaxation: float
    total_records: int


class Deviation(BaseModel):
    concentration: float
    relaxation: float


class AnalyzeResponse(BaseModel):
    status: Literal["success"] = "success"
    detected_emotion: Literal["SAD", "HAPPY", "CALM"]
    ai_recommendation: str
    current_state: CurrentState
    global_average: GlobalAverage
    deviation: Deviation


class AnalyzeErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error: Literal["high_interference"] = "high_interference"
    message: str = "Interference level is too high. Please adjust your headset."
    details: AnalyzeRequest
