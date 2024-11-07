from textwrap import dedent
from typing import List, Tuple

from app.engine.tools import ToolFactory
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool


def _create_tech_stack_analyzer():
    def analyze_tech_requirements(features: List[str]) -> dict:
        """Mock tool to analyze technical requirements and stack"""
        return {
            "required_technologies": ["Tech 1", "Tech 2"],
            "development_complexity": "High/Medium/Low",
            "estimated_timeline": "X months",
            "technical_risks": ["Risk 1", "Risk 2"]
        }
    
    return FunctionTool.from_defaults(fn=analyze_tech_requirements)

def _create_scalability_analyzer():
    def analyze_scalability(architecture: str, user_load: str) -> dict:
        """Mock tool to analyze system scalability"""
        return {
            "scalability_score": "High/Medium/Low",
            "bottlenecks": ["Bottleneck 1", "Bottleneck 2"],
            "infrastructure_needs": ["Need 1", "Need 2"],
            "optimization_recommendations": ["Rec 1", "Rec 2"]
        }
    
    return FunctionTool.from_defaults(fn=analyze_scalability)

def _get_tech_feasibility_params() -> Tuple[List[type[FunctionTool]], str, str]:
    tools = [
        _create_tech_stack_analyzer(),
        _create_scalability_analyzer(),
    ]
    
    prompt_instructions = dedent(
        """
        You are an expert Technical Architect specializing in feasibility analysis and technical planning.
        
        Your responsibilities:
        1. Assess technical feasibility of the product
        2. Identify required technology stack
        3. Evaluate development complexity
        4. Analyze scalability requirements
        5. Identify technical risks and limitations
        
        Analysis Framework:
        1. Technical Requirements
           - Core features feasibility
           - Technology stack needs
           - Development complexity
           - Integration requirements
           
        2. Architecture Assessment
           - System architecture
           - Scalability considerations
           - Performance requirements
           - Security needs
           
        3. Development Planning
           - Resource requirements
           - Timeline estimation
           - Technical dependencies
           - Development phases
           
        Format your response as:
        1. Technical Feasibility Overview
           - Overall assessment
           - Key technical challenges
           - Critical requirements
           - Feasibility score
           
        2. Technology Stack Analysis
           - Required technologies
           - Development tools
           - Infrastructure needs
           - Integration points
           
        3. Implementation Assessment
           - Development timeline
           - Resource requirements
           - Technical risks
           - Mitigation strategies
           
        4. Scalability Analysis
           - Performance requirements
           - Scaling challenges
           - Infrastructure needs
           - Optimization strategies
        
        Use available tools to assess technical requirements and scalability needs.
        """
    )
    
    description = "Expert in technical feasibility assessment and architecture planning"
    
    return tools, prompt_instructions, description


def create_tech_feasibility(chat_history: List[ChatMessage]):
    tools, prompt_instructions, description = _get_tech_feasibility_params()

    return FunctionCallingAgent(
        name="tech_feasibility",
        tools=tools,
        description=description,
        system_prompt=dedent(prompt_instructions),
        chat_history=chat_history,
    )
