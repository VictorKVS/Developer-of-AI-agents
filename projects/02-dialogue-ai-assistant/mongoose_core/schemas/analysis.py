from pydantic import BaseModel, Field


class AnalysisPayload(BaseModel):
    summary: str = Field(min_length=1)
    facts: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    goal: str = ""
    experience: str = ""
    interests: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class AnalysisResult(AnalysisPayload):
    model: str
