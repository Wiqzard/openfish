from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SurfaceType = Literal["browser", "window", "monitor", "unknown"]


class CapturedImage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data_url: str = Field(alias="dataUrl")
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    surface_type: SurfaceType = Field(alias="surfaceType")

    @field_validator("data_url")
    @classmethod
    def validate_data_url(cls, value: str) -> str:
        if not value.startswith("data:image/png;base64,"):
            raise ValueError("Captured screenshots must be PNG data URLs.")
        return value


class PlanSuggestion(BaseModel):
    summary: str = Field(min_length=1)
    current_view: str = Field(min_length=1)
    goals: list[str]
    next_steps: list[str]
    risks: list[str]
    confidence: float = Field(ge=0, le=1)


class AnalysisRequest(BaseModel):
    image: CapturedImage


class AnalysisResult(BaseModel):
    image: CapturedImage
    plan: PlanSuggestion
    raw_response: str = Field(alias="rawResponse", min_length=1)
