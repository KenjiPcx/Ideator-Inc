from textwrap import dedent
from typing import List, Tuple

from app.engine.tools import ToolFactory
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool


def _create_risk_assessment_tool():
    def assess_risk_factors(industry: str, business_model: str) -> dict:
        """Mock tool to assess various business risks"""
        return {
            "market_risks": ["Risk 1", "Risk 2"],
            "technical_risks": ["Risk 1", "Risk 2"],
            "operational_risks": ["Risk 1", "Risk 2"],
            "financial_risks": ["Risk 1", "Risk 2"],
            "regulatory_risks": ["Risk 1", "Risk 2"]
        }
    
    return FunctionTool.from_defaults(fn=assess_risk_factors)

def _create_mitigation_strategy_tool():
    def generate_mitigation_strategies(risks: List[str]) -> dict:
        """Mock tool to generate risk mitigation strategies"""
        return {
            "risk": "mitigation strategy",
            "implementation_cost": "cost estimate",
            "timeline": "implementation timeline",
            "success_metrics": ["Metric 1", "Metric 2"]
        }
    
    return FunctionTool.from_defaults(fn=generate_mitigation_strategies)

def _get_risk_analysis_params() -> Tuple[List[type[FunctionTool]], str, str]:
    tools = [
        _create_risk_assessment_tool(),
        _create_mitigation_strategy_tool(),
    ]
    
    prompt_instructions = dedent(
        """
        You are an expert Risk Analysis Specialist focusing on comprehensive business risk assessment.
        
        Your responsibilities:
        1. Identify potential risks across all business aspects
        2. Assess risk probability and impact
        3. Develop mitigation strategies
        4. Prioritize risks by severity
        5. Monitor risk indicators
        
        Analysis Framework:
        1. Market Risks
           - Competition
           - Market size
           - Market timing
           - Entry barriers
           
        2. Technical Risks
           - Technology feasibility
           - Development challenges
           - Scalability issues
           - Technical debt
           
        3. Operational Risks
           - Resource requirements
           - Supply chain
           - Quality control
           - Service delivery
           
        4. Financial Risks
           - Funding requirements
           - Cash flow
           - Revenue model
           - Cost structure
           
        5. Regulatory Risks
           - Compliance requirements
           - Legal constraints
           - Industry regulations
           - Future legislation
           
        Format your response as:
        1. Risk Assessment Summary
           - Critical risks
           - High-priority risks
           - Medium-priority risks
           - Low-priority risks
           
        2. Detailed Risk Analysis
           - Risk description
           - Probability
           - Impact
           - Overall severity
           
        3. Mitigation Strategies
           - Preventive measures
           - Contingency plans
           - Resource requirements
           - Timeline
           
        4. Monitoring Framework
           - Key risk indicators
           - Warning signals
           - Review frequency
           - Response triggers
        
        Use available tools to assess risks and generate mitigation strategies.
        """
    )
    
    description = "Expert in business risk assessment and mitigation strategy development"
    
    return tools, prompt_instructions, description


def create_risk_analysis(chat_history: List[ChatMessage]):
    tools, prompt_instructions, description = _get_risk_analysis_params()

    return FunctionCallingAgent(
        name="risk_analysis",
        tools=tools,
        description=description,
        system_prompt=dedent(prompt_instructions),
        chat_history=chat_history,
    )
