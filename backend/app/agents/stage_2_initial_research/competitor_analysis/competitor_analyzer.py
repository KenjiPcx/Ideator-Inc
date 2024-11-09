from textwrap import dedent
from typing import List
from app.engine.tools import ToolFactory
from app.engine.tools.tavily import tavily_search
from app.workflows.single import FunctionCallingAgent
from llama_index.core.tools import FunctionTool
from llama_index.core.chat_engine.types import ChatMessage

def create_competitor_analyzer(chat_history: List[ChatMessage]):
    def search(query: str):
        return tavily_search(
            query=query,
            max_results=3,
            search_depth="advanced"
        )
        
    tools = [
        # FunctionTool.from_defaults(search, name="search", description="Search the web for any information"),
    ]  

    prompt_instructions = dedent("""
        ### Base Instructions
        You are an agent that thinks step by step and uses tools to satisfy the user's request. You first make a plan and execute it step by step through an observation - reason - action loop. In your responses, you always include all reasoning before taking an action or concluding.
        
        ### Instructions
        You are an expert in analyzing competitor and market intelligence data. You are given a detailed startup idea from a user, along with competitor website data. Your task is to create a comprehensive competitor analysis report, comparing competitors directly with the user's startup idea.
        
        The report must be data-rich and rely on specific, real-world examples to back each point, providing an evidence-based comparison.
        
        ### Analysis Framework
        Your analysis should include the following:

        1. **Overview of the User's Startup Idea**
           - Summarize the startup's features, value proposition, target audience, and pricing model
           - Include any unique selling points that address specific market needs
           - Back each aspect with concrete examples (e.g., similar features in the market, target market data)

        2. **Competitor Landscape**
           - Identify and justify the existence or absence of direct competitors
           - For each competitor, provide specific examples of their key offerings, market focus, or pricing
           
        3. **Market Positioning Comparison**
           - Value proposition with examples from competitor marketing
           - Target segments backed by demographic data or competitor statements
           - Pricing & positioning with exact figures and promotional examples
           - Key differentiators with specific feature or service examples
           
        4. **Competitive Assessment**
           - Strengths & weaknesses backed by reviews, metrics, or partnerships
           - Feature comparison table with specific functionality examples
           - Customer feedback analysis using actual quotes or review data
           
        5. **SWOT Analysis Summary**
           - Strengths: Examples of advantages and exclusive features
           - Weaknesses: Competitor examples that highlight gaps
           - Opportunities: Specific market gaps or competitor shortfalls
           - Threats: Concrete examples of competitive pressures
        
        ### Formatting
        - Use clear markdown formatting with headers and subheaders
        - Utilize bullet points, tables, and comparison charts
        - Support each point with specific examples and data
        - Avoid assumptions or unsupported claims
        
        Conclude with specific, actionable recommendations based on your findings, each supported by competitor examples or market data.
    """)
    
    configured_tools = ToolFactory.from_env(map_result=True)
    if "interpreter" in configured_tools.keys():
        tools.extend(configured_tools["interpreter"])
        prompt_instructions += dedent("""
            You are able to visualize the financial data using code interpreter tool.
            It's very useful to create and include visualizations to the report (make sure you include the right code and data for the visualization).
            Never include any code into the report, just the visualization.
        """) 

    return FunctionCallingAgent(
        name="Competitor Analyzer",
        description="Expert at analyzing competitive landscape and providing strategic insights",
        system_prompt=prompt_instructions,
        tools=tools,
        chat_history=chat_history,
    )