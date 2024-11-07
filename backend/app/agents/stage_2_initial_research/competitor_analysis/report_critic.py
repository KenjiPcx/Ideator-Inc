from textwrap import dedent
from typing import List
from pydantic import BaseModel, Field
from app.workflows.single import FunctionCallingAgent
from llama_index.core.tools import FunctionTool
from llama_index.core.chat_engine.types import ChatMessage

class CompetitorReportCritique(BaseModel):
    satisfied: bool = Field(description="Whether you are satisfied with the report")
    critique: str = Field(description="A detailed critique highlighting specific gaps and issues")
    actionable_feedback: str = Field(description="Actionable recommendations for improving the report")

def create_report_critic(chat_history: List[ChatMessage]):
    tools = []

    prompt_instructions = dedent("""
        You are an expert critic reviewing competitive analysis reports. Your task is to evaluate if the report meets the minimum requirements for a useful competitor analysis.
        
        Required Elements Checklist:
        1. Competitor Overview
           - [ ] List of main direct competitors (minimum 3)
           - [ ] Brief company descriptions
           - [ ] Market positioning
        
        2. Core Metrics
           - [ ] Pricing information (if available)
           - [ ] Target customer segments
           - [ ] Key differentiators
        
        3. Product Comparison
           - [ ] Feature comparison matrix
           - [ ] Strengths and weaknesses
           - [ ] Unique selling propositions
        
        4. Strategic Insights
           - [ ] Key competitive advantages
           - [ ] Market opportunities
           - [ ] Potential threats
           - [ ] Recommended actions
        
        A satisfactory report must cover at least 80\% of these elements with specific, concrete information.
        
        Provide your feedback in three parts:
        1. Whether you are satisfied with the report (boolean)
        2. A detailed critique highlighting specific gaps and issues
        3. Actionable recommendations for improving the report
        
        Focus on being constructive and specific. Each piece of criticism should be paired with a concrete suggestion for improvement.
        
        Example Output:
        {
            "satisfied": false,
            "critique": "The report lacks quantitative metrics and specific examples. Market positioning claims aren't supported by concrete evidence. Competitor feature comparison is too general.",
            "actionable_feedback": "1. Add specific pricing data points for each competitor\n2. Include 2-3 specific customer review quotes to support claims\n3. Create a detailed feature comparison matrix\n4. Quantify market size and growth rates"
        }
    """)

    return FunctionCallingAgent(
        name="competitor_report_critic",
        tools=tools,
        description="Expert at critiquing competitive analysis reports and providing improvement suggestions",
        system_prompt=prompt_instructions,
        chat_history=chat_history,
    ) 