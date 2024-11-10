from pydantic import BaseModel, Field
from typing import List

class KeyInsight(BaseModel):
    finding: str = Field(description="A detailed finding with supporting evidence")
    section: str = Field(description="The section of the report that this finding belongs to")
    supporting_data: str = Field(description="Relevant stories, facts, quotes, or case studies that support this finding in full detail and context. Don't give generic statements like 'users said its frustrating or expensive', give specific examples and quote the evidence word by word on why it is the case and what was the impact, the pain point, the opportunity, etc all in full detail.")
    sources: List[str] = Field(description="List of sources that support this finding")

class ExecutiveSummaryOutline(BaseModel):
    title: str = Field(description="Clear, specific title for the executive summary")
    overview: str = Field(description="Brief overview of what the research covers")
    key_findings: List[KeyInsight] = Field(description="List of key findings with supporting evidence")

class ExecutiveCritique(BaseModel):
    satisfied: bool = Field(description="Whether the executive summary satisfies the requirements")
    clarity_score: int = Field(description="Clarity score from 1 to 10")
    completeness_score: int = Field(description="Completeness score from 1 to 10")
    actionability_score: int = Field(description="Actionability score from 1 to 10")
    issues_found: List[str] = Field(description="List of issues found in the executive summary")
    improvement_suggestions: List[str] = Field(description="List of improvement suggestions for the executive summary")
    missing_elements: List[str] = Field(description="List of missing elements in the executive summary")