from textwrap import dedent
from typing import List, Tuple

from app.engine.tools import ToolFactory
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool


def _create_channel_analysis_tool():
    def analyze_marketing_channels(target_audience: str, industry: str) -> dict:
        """Mock tool to analyze marketing channels effectiveness"""
        return {
            "channel_effectiveness": {
                "social_media": "High/Medium/Low",
                "content_marketing": "High/Medium/Low",
                "paid_ads": "High/Medium/Low",
                "email": "High/Medium/Low"
            },
            "cost_per_channel": {
                "social_media": "$X",
                "content_marketing": "$Y",
                "paid_ads": "$Z",
                "email": "$W"
            }
        }
    
    return FunctionTool.from_defaults(fn=analyze_marketing_channels)

def _create_launch_strategy_tool():
    def generate_launch_strategy(product_type: str, target_market: str) -> dict:
        """Mock tool to generate launch strategy recommendations"""
        return {
            "launch_phases": ["Phase 1", "Phase 2", "Phase 3"],
            "timeline": "X months",
            "key_activities": ["Activity 1", "Activity 2"],
            "success_metrics": ["Metric 1", "Metric 2"]
        }
    
    return FunctionTool.from_defaults(fn=generate_launch_strategy)

def _get_go_to_market_params() -> Tuple[List[type[FunctionTool]], str, str]:
    tools = [
        _create_channel_analysis_tool(),
        _create_launch_strategy_tool(),
    ]
    
    prompt_instructions = dedent(
        """
        You are an expert Go-to-Market Strategist specializing in product launches and marketing strategy.
        
        Your responsibilities:
        1. Develop comprehensive GTM strategy
        2. Identify optimal marketing channels
        3. Create launch timeline
        4. Define success metrics
        5. Plan marketing activities
        
        Strategy Framework:
        1. Market Entry Strategy
           - Entry timing
           - Geographic focus
           - Target segments
           - Positioning strategy
           
        2. Marketing Channels
           - Channel prioritization
           - Budget allocation
           - Content strategy
           - Partnership opportunities
           
        3. Launch Planning
           - Phase definition
           - Timeline development
           - Resource requirements
           - Risk mitigation
           
        Format your response as:
        1. GTM Strategy Overview
           - Core strategy
           - Key differentiators
           - Value proposition
           - Market positioning
           
        2. Channel Strategy
           - Primary channels
           - Secondary channels
           - Budget allocation
           - Content plan
           
        3. Launch Plan
           - Launch phases
           - Timeline
           - Key activities
           - Success metrics
           
        4. Growth Strategy
           - Scaling plan
           - Market expansion
           - Partnership strategy
           - Long-term goals
        
        Use available tools to analyze channels and develop launch strategy.
        """
    )
    
    description = "Expert in go-to-market strategy and product launch planning"
    
    return tools, prompt_instructions, description


def create_go_to_market(chat_history: List[ChatMessage]):
    tools, prompt_instructions, description = _get_go_to_market_params()

    return FunctionCallingAgent(
        name="go_to_market",
        tools=tools,
        description=description,
        system_prompt=dedent(prompt_instructions),
        chat_history=chat_history,
    )
