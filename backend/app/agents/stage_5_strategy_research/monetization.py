from textwrap import dedent
from typing import List, Tuple

from app.engine.tools import ToolFactory
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool


def _create_pricing_analysis_tool():
    def analyze_pricing_models(industry: str, target_market: str) -> dict:
        """Mock tool to analyze pricing models and strategies"""
        return {
            "competitor_pricing": {"low": "$X", "high": "$Y", "average": "$Z"},
            "pricing_models": ["Subscription", "One-time", "Freemium"],
            "price_sensitivity": "Medium/High/Low",
            "optimal_price_range": "$A - $B"
        }
    
    return FunctionTool.from_defaults(fn=analyze_pricing_models)

def _create_revenue_projection_tool():
    def project_revenue(pricing_model: str, market_size: int, conversion_rate: float) -> dict:
        """Mock tool to project revenue and financial metrics"""
        return {
            "projected_revenue": "$X per year",
            "cac": "$Y per customer",
            "ltv": "$Z per customer",
            "break_even_point": "X months"
        }
    
    return FunctionTool.from_defaults(fn=project_revenue)

def _get_monetization_params() -> Tuple[List[type[FunctionTool]], str, str]:
    tools = [
        _create_pricing_analysis_tool(),
        _create_revenue_projection_tool(),
    ]
    
    prompt_instructions = dedent(
        """
        You are an expert Monetization Strategist specializing in pricing and revenue models.
        
        Your responsibilities:
        1. Develop optimal pricing strategy
        2. Calculate key metrics (CAC, LTV)
        3. Design revenue models
        4. Project financial performance
        5. Optimize monetization approach
        
        Analysis Framework:
        1. Pricing Strategy
           - Market positioning
           - Competitor benchmarking
           - Value-based pricing
           - Price sensitivity
           
        2. Revenue Models
           - Subscription tiers
           - One-time purchases
           - Freemium strategy
           - Enterprise pricing
           
        3. Financial Metrics
           - Customer Acquisition Cost (CAC)
           - Lifetime Value (LTV)
           - Break-even analysis
           - Revenue projections
           
        Format your response as:
        1. Pricing Strategy
           - Recommended pricing model
           - Price points
           - Competitive positioning
           - Value justification
           
        2. Revenue Model
           - Model structure
           - Revenue streams
           - Pricing tiers
           - Upsell opportunities
           
        3. Financial Projections
           - CAC/LTV analysis
           - Revenue forecasts
           - Break-even timeline
           - Profitability metrics
           
        4. Implementation Plan
           - Launch pricing
           - Testing strategy
           - Optimization metrics
           - Growth targets
        
        Use available tools to analyze pricing and project financials.
        """
    )
    
    description = "Expert in monetization strategy and pricing optimization"
    
    return tools, prompt_instructions, description


def create_monetization(chat_history: List[ChatMessage]):
    tools, prompt_instructions, description = _get_monetization_params()

    return FunctionCallingAgent(
        name="monetization",
        tools=tools,
        description=description,
        system_prompt=dedent(prompt_instructions),
        chat_history=chat_history,
    )
