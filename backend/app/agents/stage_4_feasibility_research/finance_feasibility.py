from textwrap import dedent
from typing import List, Tuple

from app.engine.tools import ToolFactory
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool


def _create_cost_analyzer():
    def analyze_development_costs(requirements: dict) -> dict:
        """Mock tool to analyze development and operational costs"""
        return {
            "development_costs": "$X",
            "operational_costs": "$Y per month",
            "maintenance_costs": "$Z per year",
            "scaling_costs": "Cost curve analysis"
        }
    
    return FunctionTool.from_defaults(fn=analyze_development_costs)

def _create_financial_projector():
    def project_financials(costs: dict, revenue: dict) -> dict:
        """Mock tool to create financial projections"""
        return {
            "break_even_analysis": "X months",
            "cash_flow_projections": ["Month 1: $X", "Month 2: $Y"],
            "profitability_metrics": {"ROI": "X%", "Profit Margin": "Y%"},
            "funding_requirements": "$Z initial investment"
        }
    
    return FunctionTool.from_defaults(fn=project_financials)

def _get_finance_feasibility_params() -> Tuple[List[type[FunctionTool]], str, str]:
    tools = [
        _create_cost_analyzer(),
        _create_financial_projector(),
    ]
    
    prompt_instructions = dedent(
        """
        You are an expert Financial Analyst specializing in startup feasibility and financial planning.
        
        Your responsibilities:
        1. Assess financial viability
        2. Project development costs
        3. Estimate operational costs
        4. Create financial projections
        5. Determine funding requirements
        
        Analysis Framework:
        1. Cost Analysis
           - Development costs
           - Operational costs
           - Marketing costs
           - Scaling costs
           
        2. Revenue Projections
           - Revenue streams
           - Growth projections
           - Market penetration
           - Pricing impact
           
        3. Financial Metrics
           - Break-even analysis
           - ROI projections
           - Profit margins
           - Cash flow needs
           
        Format your response as:
        1. Financial Feasibility Overview
           - Viability assessment
           - Key financial metrics
           - Critical assumptions
           - Risk factors
           
        2. Cost Structure Analysis
           - Development budget
           - Operational costs
           - Marketing budget
           - Overhead costs
           
        3. Financial Projections
           - Revenue forecasts
           - Cost projections
           - Profitability timeline
           - Cash flow analysis
           
        4. Funding Requirements
           - Initial investment
           - Operational runway
           - Funding milestones
           - Investment returns
        
        Use available tools to analyze costs and project financials.
        """
    )
    
    description = "Expert in financial feasibility assessment and financial planning"
    
    return tools, prompt_instructions, description


def create_finance_feasibility(chat_history: List[ChatMessage]):
    tools, prompt_instructions, description = _get_finance_feasibility_params()

    return FunctionCallingAgent(
        name="finance_feasibility",
        tools=tools,
        description=description,
        system_prompt=dedent(prompt_instructions),
        chat_history=chat_history,
    )
