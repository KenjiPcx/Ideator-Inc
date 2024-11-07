from textwrap import dedent
from typing import List, Tuple

from app.engine.tools import ToolFactory
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool


def _create_insight_extraction_tool():
    def extract_key_insights(research_data: dict) -> dict:
        """Mock tool to extract and prioritize key insights"""
        return {
            "key_findings": ["Finding 1", "Finding 2"],
            "critical_factors": ["Factor 1", "Factor 2"],
            "recommendations": ["Rec 1", "Rec 2"],
            "next_steps": ["Step 1", "Step 2"]
        }
    
    return FunctionTool.from_defaults(fn=extract_key_insights)

def _get_summarizer_params() -> Tuple[List[type[FunctionTool]], str, str]:
    tools = [
        _create_insight_extraction_tool(),
    ]
    
    prompt_instructions = dedent(
        """
        You are an expert Business Analyst specializing in synthesizing complex research into clear, actionable insights.
        
        Your responsibilities:
        1. Synthesize all research findings
        2. Identify key insights
        3. Prioritize recommendations
        4. Create executive summary
        
        Summary Framework:
        1. Executive Summary
           - Core idea validation
           - Key findings
           - Critical insights
           - Strategic recommendations
           
        2. Market Opportunity
           - Market size/potential
           - Target audience
           - Competitive advantage
           - Growth potential
           
        3. Feasibility Assessment
           - Technical viability
           - Financial feasibility
           - Operational requirements
           - Risk assessment
           
        4. Strategic Recommendations
           - Next steps
           - Priority actions
           - Resource needs
           - Timeline
        
        Format your response as:
        1. Executive Overview
           - One-paragraph summary
           - Key validation points
           - Critical success factors
           
        2. Detailed Findings
           - Market analysis
           - Customer insights
           - Competitive position
           - Feasibility assessment
           
        3. Strategic Implications
           - Opportunities
           - Challenges
           - Risk factors
           - Success requirements
           
        4. Action Plan
           - Immediate next steps
           - Resource requirements
           - Timeline
           - Success metrics
        
        Remember: Focus on clarity and actionability in your summary.
        """
    )
    
    description = "Expert in synthesizing research findings into actionable insights"
    
    return tools, prompt_instructions, description


def create_summarizer(chat_history: List[ChatMessage]):
    tools, prompt_instructions, description = _get_summarizer_params()

    return FunctionCallingAgent(
        name="summarizer",
        tools=tools,
        description=description,
        system_prompt=dedent(prompt_instructions),
        chat_history=chat_history,
    )
