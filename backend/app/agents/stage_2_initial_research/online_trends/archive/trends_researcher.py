from textwrap import dedent
from typing import List
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool
from app.engine.tools.google_trends import google_trends_search
from pydantic import BaseModel, Field

class TrendMetrics(BaseModel):
    trend_term: str = Field(description="The search term analyzed")
    interest_over_time: str = Field(description="Summary of interest trends over time")
    growth_pattern: str = Field(description="Pattern of growth (steady, rising, declining, cyclical)")
    related_topics: List[str] = Field(description="Related topics showing correlation")
    peak_periods: List[str] = Field(description="Notable peak interest periods")

def create_trends_researcher(chat_history: List[ChatMessage]):
    tools = [
        FunctionTool.from_defaults(
            google_trends_search, 
            name="trends_search",
            description="Search Google Trends data for interest over time and related queries"
        ),
    ]

    prompt_instructions = dedent("""
        ### Instructions
        You are an expert at analyzing Google Trends data. Your task is to:
        1. Use the trends_search tool to gather data
        2. Analyze interest patterns over time
        3. Identify related topics and queries
        4. Summarize key findings
        
        For each search term:
        - Analyze multiple time ranges (12m, 5y if available)
        - Look for seasonal patterns
        - Identify geographic variations
        - Note related rising queries
        
        ### Output Format
        Return your findings in this JSON format:
        {
            "metrics": [
                {
                    "trend_term": "Search term analyzed",
                    "interest_over_time": "Summary of interest patterns",
                    "growth_pattern": "steady/rising/declining/cyclical",
                    "related_topics": ["topic 1", "topic 2"],
                    "peak_periods": ["period 1", "period 2"]
                }
            ],
            "overall_insights": [
                "Key insight 1",
                "Key insight 2"
            ]
        }
    """)

    return FunctionCallingAgent(
        name="trends_researcher",
        tools=tools,
        system_prompt=prompt_instructions,
        description="Expert at analyzing Google Trends data",
        chat_history=chat_history,
    ) 