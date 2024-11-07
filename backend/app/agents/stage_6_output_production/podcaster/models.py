from pydantic import BaseModel, Field
from typing import List, Dict, Any

class OutlineSegment(BaseModel):
    topic: str = Field(description="Topic of the segment")
    key_points: List[str] = Field(description="Key points of the segment")
    stories: List[str] = Field(description="Stories of the segment")
    insights: List[str] = Field(description="Insights of the segment")

class PodcastOutline(BaseModel):
    title: str = Field(description="Engaging podcast title")
    hook: str = Field(description="Compelling hook that makes listeners stay")
    segments: List[OutlineSegment] = Field(description="List of speaking segments")
    target_audience: str = Field(description="Description of ideal listener")
    unique_angles: List[str] = Field(description="Surprising take 1, Contrarian view 2")
    actionable_takeaways: List[str] = Field(description="Specific action 1, Strategy 2")

class PodcastSegment(BaseModel):
    speaker: str = Field(description="Speaker of the segment")
    text: str = Field(description="Text of the segment")

class PodcastScript(BaseModel):
    segments: List[PodcastSegment] = Field(description="List of speaking segments")

class ScriptCritique(BaseModel):
    satisfied: bool = Field(description="Whether the script meets quality standards")
    overall_rating: int = Field(description="Rating from 1-10")
    strengths: List[str] = Field(description="What works well")
    weaknesses: List[str] = Field(description="Areas needing improvement")
    specific_feedback: Dict[str, List[str]] = Field(description="Section-specific feedback")
    improvement_suggestions: List[str] = Field(description="Actionable suggestions") 