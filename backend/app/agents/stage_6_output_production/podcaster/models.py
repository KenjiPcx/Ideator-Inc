from pydantic import BaseModel, Field
from typing import List, Dict, Any

class PodcastSegment(BaseModel):
    speaker: str = Field(description="Speaker role (host or guest)")
    text: str = Field(description="Text to be spoken")

class PodcastScript(BaseModel):
    title: str = Field(description="Engaging podcast title")
    description: str = Field(description="Brief episode description")
    segments: List[PodcastSegment] = Field(description="List of speaking segments")
    key_points: List[str] = Field(description="Key insights covered")
    estimated_duration: str = Field(description="Estimated episode duration")
    target_audience: str = Field(description="Target audience description")

class ScriptCritique(BaseModel):
    satisfied: bool = Field(description="Whether the script meets quality standards")
    overall_rating: int = Field(description="Rating from 1-10")
    strengths: List[str] = Field(description="What works well")
    weaknesses: List[str] = Field(description="Areas needing improvement")
    specific_feedback: Dict[str, List[str]] = Field(description="Section-specific feedback")
    improvement_suggestions: List[str] = Field(description="Actionable suggestions") 