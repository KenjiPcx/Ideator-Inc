from textwrap import dedent
from typing import List, Tuple

from app.engine.tools import ToolFactory
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool


def _create_tam_calculator_tool():
    def calculate_tam_sam_som(industry: str, region: str) -> str:
        """Mock tool to calculate TAM, SAM, and SOM"""
        return {
            "TAM": "$X billion",
            "SAM": "$Y billion",
            "SOM": "$Z billion"
        }
    
    return FunctionTool.from_defaults(fn=calculate_tam_sam_som)

def _create_market_segments_tool():
    def analyze_market_segments(industry: str) -> str:
        """Mock tool to identify and analyze market segments"""
        return "Market segments analysis: [segment details]"
    
    return FunctionTool.from_defaults(fn=analyze_market_segments)

def _create_industry_growth_tool():
    def forecast_industry_growth(industry: str, timeframe: str) -> str:
        """Mock tool to forecast industry growth"""
        return f"Growth forecast for {timeframe}: X% CAGR"
    
    return FunctionTool.from_defaults(fn=forecast_industry_growth)

def _get_market_research_params() -> Tuple[List[type[FunctionTool]], str, str]:
    tools = [
        _create_tam_calculator_tool(),
        _create_market_segments_tool(),
        _create_industry_growth_tool(),
    ]
    
    prompt_instructions = dedent(
        """
        You are an expert Market Research Analyst specializing in market size analysis and segmentation.
        
        Your responsibilities:
        1. Calculate and analyze TAM (Total Addressable Market)
        2. Determine SAM (Serviceable Addressable Market)
        3. Estimate SOM (Serviceable Obtainable Market)
        4. Identify key market segments
        5. Analyze market growth trends
        
        Guidelines:
        - Use data-driven approaches for market size calculations
        - Consider both current market size and growth potential
        - Identify the most promising market segments
        - Analyze competitive intensity in each segment
        
        Format your response as:
        1. Market Size Analysis (TAM/SAM/SOM)
        2. Market Segmentation
        3. Growth Trends
        4. Key Opportunities
        5. Market Risks
        
        Use the available tools to gather and validate market data.
        """
    )
    
    description = "Expert in market size analysis, segmentation, and growth forecasting"
    
    return tools, prompt_instructions, description


def create_market_research(chat_history: List[ChatMessage]):
    tools, prompt_instructions, description = _get_market_research_params()

    return FunctionCallingAgent(
        name="market_research",
        tools=tools,
        description=description,
        system_prompt=dedent(prompt_instructions),
        chat_history=chat_history,
    )
