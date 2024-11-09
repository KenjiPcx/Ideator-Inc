from textwrap import dedent
from typing import List, Tuple

from app.engine.tools import ToolFactory
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool


def _create_google_trends_tool():
    def analyze_search_trends(keyword: str, timeframe: str = "12m") -> dict:
        """Mock tool to analyze Google search trends"""
        return {
            "trend_direction": "increasing/decreasing",
            "search_volume": "XXX monthly searches",
            "related_topics": ["Topic 1", "Topic 2"],
            "geographic_interest": ["Region 1", "Region 2"]
        }
    
    return FunctionTool.from_defaults(fn=analyze_search_trends)

def _create_social_trends_tool():
    def analyze_social_trends(topic: str, platforms: List[str]) -> dict:
        """Mock tool to analyze trends across social platforms"""
        return {
            "trending_hashtags": ["#tag1", "#tag2"],
            "viral_content": ["Content 1", "Content 2"],
            "engagement_metrics": {"likes": "XXX", "shares": "YYY"},
            "demographic_interest": ["Demo 1", "Demo 2"]
        }
    
    return FunctionTool.from_defaults(fn=analyze_social_trends)

def _get_online_trends_params() -> Tuple[List[type[FunctionTool]], str, str]:
    tools = [
        _create_google_trends_tool(),
        _create_social_trends_tool(),
    ]
    
    prompt_instructions = dedent(
        """
        You are an expert Trends Analyst specializing in real-time market trends and emerging patterns.
        
        Your responsibilities:
        1. Analyze current market trends
        2. Identify emerging patterns
        3. Track consumer behavior shifts
        4. Monitor platform-specific trends
        5. Predict future trend directions
        
        Research Framework:
        1. Search Trends Analysis
           - Google Trends data
           - Search volume patterns
           - Related searches
           - Geographic distribution
           
        2. Social Media Trends
           - Platform-specific trends
           - Hashtag analysis
           - Viral content patterns
           - Engagement metrics
           
        3. Consumer Behavior Shifts
           - Changing preferences
           - New use cases
           - Emerging needs
           - Behavioral patterns
           
        Format your response as:
        1. Current Trends Overview
           - Search trends
           - Social media trends
           - Consumer behavior shifts
           
        2. Trend Analysis
           - Trend strength
           - Geographic relevance
           - Demographic appeal
           - Growth trajectory
           
        3. Future Predictions
           - Short-term outlook
           - Long-term potential
           - Risk factors
           
        4. Strategic Implications
           - Market timing
           - Feature priorities
           - Marketing angles
           - Platform focus
        
        Use available tools to gather and analyze real-time trend data.
        """
    )
    
    description = "Expert in analyzing real-time market trends and consumer behavior patterns"
    
    return tools, prompt_instructions, description


def create_online_trends(chat_history: List[ChatMessage]):
    tools, prompt_instructions, description = _get_online_trends_params()

    return FunctionCallingAgent(
        name="online_trends",
        tools=tools,
        description=description,
        system_prompt=dedent(prompt_instructions),
        chat_history=chat_history,
    )
