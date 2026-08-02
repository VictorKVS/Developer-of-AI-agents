from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    title: str
    reason: str
    next_step: str


class UserProfile(BaseModel):
    name: str | None = None
    goals: list[str] = Field(default_factory=list)
    experience: str = ""
    interests: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    profile: UserProfile
    summary: str
    recommendations: list[Recommendation]
    confidence: float = Field(ge=0.0, le=1.0)
    missing_information: list[str] = Field(default_factory=list)
    disclaimer: str
