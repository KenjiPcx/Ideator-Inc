from textwrap import dedent
from typing import List, Tuple

from app.engine.tools import ToolFactory
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool


def _create_social_listening_tool():
    def analyze_social_sentiment(topic: str, platform: str) -> dict:
        """Mock tool to analyze social media sentiment and discussions"""
        return {
            "sentiment": "positive/negative/neutral",
            "common_topics": ["Topic 1", "Topic 2"],
            "pain_points": ["Pain point 1", "Pain point 2"],
            "feature_requests": ["Feature 1", "Feature 2"]
        }
    
    return FunctionTool.from_defaults(fn=analyze_social_sentiment)

def _create_survey_analysis_tool():
    def analyze_survey_data(target_demographic: str) -> dict:
        """Mock tool to analyze survey responses and feedback"""
        return {
            "key_findings": ["Finding 1", "Finding 2"],
            "user_preferences": ["Preference 1", "Preference 2"],
            "willingness_to_pay": "Price range",
            "adoption_barriers": ["Barrier 1", "Barrier 2"]
        }
    
    return FunctionTool.from_defaults(fn=analyze_survey_data)

def _get_customer_insights_params() -> Tuple[List[type[FunctionTool]], str, str]:
    tools = [
        _create_social_listening_tool(),
        _create_survey_analysis_tool(),
    ]
    
    prompt_instructions = dedent(
        """
        You are an expert Customer Insights Analyst specializing in understanding user needs and preferences.
        
        Your responsibilities:
        1. Analyze customer feedback and sentiment
        2. Identify key pain points and needs
        3. Understand user preferences and behaviors
        4. Discover feature requests and desires
        5. Assess willingness to pay
        
        Research Framework:
        1. Social Listening Analysis
           - Reddit discussions
           - Twitter sentiment
           - YouTube comments
           - Forum discussions
           
        2. User Feedback Analysis
           - Common complaints
           - Feature requests
           - Usage patterns
           - Success stories
           
        3. Behavioral Analysis
           - User journey mapping
           - Pain points
           - Decision factors
           - Usage context
           
        Format your response as:
        1. Voice of Customer
           - Key themes
           - Common pain points
           - Feature requests
           
        2. User Behavior Analysis
           - Usage patterns
           - Decision journey
           - Adoption barriers
           
        3. Preference Analysis
           - Must-have features
           - Nice-to-have features
           - Price sensitivity
           
        4. Recommendations
           - Priority features
           - User experience focus
           - Pricing strategy
        
        Use available tools to gather and analyze customer feedback data.
        """
    )
    
    description = "Expert in customer insights and user behavior analysis"
    
    return tools, prompt_instructions, description


def create_customer_insights(chat_history: List[ChatMessage]):
    tools, prompt_instructions, description = _get_customer_insights_params()

    return FunctionCallingAgent(
        name="customer_insights",
        tools=tools,
        description=description,
        system_prompt=dedent(prompt_instructions),
        chat_history=chat_history,
    )
