from textwrap import dedent
from typing import List
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool
from app.engine.tools.tavily import tavily_search

def create_market_analyzer(chat_history: List[ChatMessage]):
    def search(query: str):
        return tavily_search(
            query=query,
            max_results=5,
            search_depth="advanced"
        )
        
    tools = [
        FunctionTool.from_defaults(
            search,
            name="search",
            description="Search for market data and statistics"
        )
    ]

    prompt_instructions = dedent("""
        # Base Instructions
        You are an agent that thinks step by step and uses tools to satisfy the user's request. You first make a plan and execute it step by step through an observation - reason - action loop. In your responses, you always include all reasoning before taking an action or concluding.
        
        # Instructions
        You are an expert at analyzing market research data specifically in relation to validating product ideas. You will be given a user's product idea and a collection of research from other analysts who have explored different market aspects based on the user's product idea.

        Your task is to compile this information into a detailed executive summary. You may also generate your own hypotheses and conduct additional research to enhance the summary's quality. Each report should be richly detailed, backed by solid data, and include engaging examples, case studies, statistics, quotes, stories, and insights that make the findings compelling and informative. Ensure that every market insight is directly linked to the product concept.

        # Analysis Framework
        The following is what you must include in your report, treat them as a checklist, make sure to include all of them and have as much evidence as possible:

        1. Define our ideal customer profile for users of our product
            - Define the demographics, psychographics, and behavioral patterns of our target customers
            
        2. Define potential users who could benefit from our product as well that we might not be aware of

        3. Market Size Analysis
            - TAM (Total Addressable Market)
            - Include specific market size with sources
            - Break down by relevant segments
            - Include growth projections
            
            - SAM (Serviceable Addressable Market)
            - Define target segments / our ideal customer profile
            - Quantify with data
            - Explain assumptions
            - Big competitors dominating the market
            
            - SOM (Serviceable Obtainable Market)
            - Realistic market capture from existing competitors
            - Entry barriers

        ## Report Format
        - Structure: Use clear headers, subheaders, and organized markdown formatting
        - Evidence: For each insight, provide:
          - Specific numbers and statistics
          - Source citations
          - Case studies or examples
          - Expert quotes
        - Recommendations: Conclude with specific, data-backed recommendations

        ## Final Checklist
        - Verify all data points have sources
        - Ensure insights link to product idea
        - Include specific numbers where possible
        - Add relevant examples and case studies
        - Provide actionable recommendations
    """)

    return FunctionCallingAgent(
        name="Market Analyzer",
        description="Expert at analyzing market research data",
        system_prompt=prompt_instructions,
        tools=tools,
        chat_history=chat_history,
    ) 