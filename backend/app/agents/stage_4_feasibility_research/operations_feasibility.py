from textwrap import dedent
from typing import List, Tuple

from app.engine.tools import ToolFactory
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool


def _create_resource_analysis_tool():
    def analyze_resource_requirements(business_model: str, scale: str) -> dict:
        """Mock tool to analyze operational resource requirements"""
        return {
            "human_resources": ["Role 1", "Role 2"],
            "infrastructure": ["Requirement 1", "Requirement 2"],
            "key_partnerships": ["Partner 1", "Partner 2"],
            "operational_costs": "$X per month"
        }
    
    return FunctionTool.from_defaults(fn=analyze_resource_requirements)

def _create_operations_assessment_tool():
    def assess_operational_viability(requirements: dict) -> dict:
        """Mock tool to assess operational viability and challenges"""
        return {
            "viability_score": "High/Medium/Low",
            "operational_challenges": ["Challenge 1", "Challenge 2"],
            "scaling_requirements": ["Requirement 1", "Requirement 2"],
            "efficiency_metrics": ["Metric 1", "Metric 2"]
        }
    
    return FunctionTool.from_defaults(fn=assess_operational_viability)

def _get_operations_feasibility_params() -> Tuple[List[type[FunctionTool]], str, str]:
    tools = [
        _create_resource_analysis_tool(),
        _create_operations_assessment_tool(),
    ]
    
    prompt_instructions = dedent(
        """
        You are an expert Operations Analyst specializing in operational feasibility and resource planning.
        
        Your responsibilities:
        1. Assess operational requirements
        2. Evaluate resource needs
        3. Identify operational challenges
        4. Plan scaling strategy
        5. Define efficiency metrics
        
        Analysis Framework:
        1. Resource Requirements
           - Human resources
           - Infrastructure needs
           - Technology requirements
           - Partner relationships
           
        2. Operational Structure
           - Process workflows
           - Quality control
           - Service delivery
           - Capacity planning
           
        3. Scaling Considerations
           - Growth requirements
           - Resource scaling
           - Process automation
           - Efficiency optimization
           
        Format your response as:
        1. Operational Feasibility Overview
           - Overall assessment
           - Key requirements
           - Critical challenges
           - Feasibility score
           
        2. Resource Analysis
           - Required resources
           - Cost implications
           - Availability assessment
           - Scaling needs
           
        3. Operational Strategy
           - Process design
           - Quality measures
           - Efficiency metrics
           - Control systems
           
        4. Implementation Plan
           - Phasing strategy
           - Resource timeline
           - Key milestones
           - Success metrics
        
        Use available tools to assess operational requirements and viability.
        """
    )
    
    description = "Expert in operational feasibility assessment and resource planning"
    
    return tools, prompt_instructions, description


def create_operations_feasibility(chat_history: List[ChatMessage]):
    tools, prompt_instructions, description = _get_operations_feasibility_params()

    return FunctionCallingAgent(
        name="operations_feasibility",
        tools=tools,
        description=description,
        system_prompt=dedent(prompt_instructions),
        chat_history=chat_history,
    )
