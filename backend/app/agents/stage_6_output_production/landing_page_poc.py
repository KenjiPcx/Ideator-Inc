from textwrap import dedent
from typing import List, Tuple

from app.engine.tools import ToolFactory
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool


def _create_landing_page_generator_tool():
    def generate_landing_page_content(value_prop: str, target_audience: str) -> dict:
        """Mock tool to generate landing page content structure"""
        return {
            "headline": "Main value proposition",
            "subheadlines": ["Benefit 1", "Benefit 2"],
            "features": ["Feature 1", "Feature 2"],
            "cta_sections": ["Primary CTA", "Secondary CTA"]
        }
    
    return FunctionTool.from_defaults(fn=generate_landing_page_content)

def _create_conversion_optimizer_tool():
    def optimize_conversion_elements(page_elements: dict) -> dict:
        """Mock tool to optimize landing page for conversions"""
        return {
            "layout_recommendations": ["Rec 1", "Rec 2"],
            "cta_placement": ["Position 1", "Position 2"],
            "social_proof": ["Testimonial 1", "Testimonial 2"],
            "trust_elements": ["Element 1", "Element 2"]
        }
    
    return FunctionTool.from_defaults(fn=optimize_conversion_elements)

def _get_landing_page_poc_params() -> Tuple[List[type[FunctionTool]], str, str]:
    tools = [
        _create_landing_page_generator_tool(),
        _create_conversion_optimizer_tool(),
    ]
    
    prompt_instructions = dedent(
        """
        You are an expert Landing Page Designer specializing in conversion-optimized proof of concept pages.
        
        Your responsibilities:
        1. Create compelling value propositions
        2. Design conversion-focused layout
        3. Craft engaging content
        4. Optimize for conversions
        5. Incorporate trust elements
        
        Design Framework:
        1. Above the Fold
           - Main headline
           - Supporting subheadline
           - Primary CTA
           - Hero visual concept
           
        2. Value Proposition
           - Key benefits
           - Problem solution
           - Unique advantages
           - Target audience fit
           
        3. Social Proof
           - Testimonial concepts
           - Trust indicators
           - Success metrics
           - Industry validation
           
        Format your response as:
        1. Page Structure
           - Above the fold
           - Key sections
           - Content flow
           - CTA placement
           
        2. Content Elements
           - Headlines
           - Value propositions
           - Feature descriptions
           - Social proof
           
        3. Conversion Elements
           - Primary CTA
           - Secondary CTAs
           - Trust builders
           - Urgency factors
           
        4. Visual Guidelines
           - Layout structure
           - Key visuals
           - Color psychology
           - Typography notes
        
        Remember: Focus on creating a compelling narrative that drives visitor engagement and conversions.
        """
    )
    
    description = "Expert in designing conversion-optimized landing pages for concept validation"
    
    return tools, prompt_instructions, description


def create_landing_page_poc(chat_history: List[ChatMessage]):
    tools, prompt_instructions, description = _get_landing_page_poc_params()

    return FunctionCallingAgent(
        name="landing_page_poc",
        tools=tools,
        description=description,
        system_prompt=dedent(prompt_instructions),
        chat_history=chat_history,
    )
