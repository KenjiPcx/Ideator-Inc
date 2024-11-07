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
        FunctionTool.from_defaults(search, name="search", description="Search the web for any information"),
    ]  

    prompt_instructions = dedent("""
        ### Base Instructions
        You are an agent that thinks step by step and uses tools to satisfy the user's request. You first make a plan and execute it step by step through an observation - reason - action loop. In your responses, you always include all reasoning before taking an action or concluding.
        
        ### Instructions
        You are an expert in analyzing competitor and market intelligence data.
        You are given a user's startup idea with full details, and a list of competitor website data to analyze. Your task is to analyze this data, and return a comprehensive competitive analysis report against the user's startup idea. 
        You are also able to come up with more hypotheses, and search for additional information on the web to further analyze the data. You might also be given a critique and feedback to improve the report, you are responsible for refining the report based on the feedback.
        
        ### Analysis
        Your analysis should cover these key areas:
        1. A brief overview of the user's startup idea and its features, value proposition, target segments, and pricing strategy or any other key details
        2. Whether there are any competitors, if not, why not? If there are competitors, follow up with the following steps to compare against the user's startup idea:
        3. Market Position
           - Value proposition and target segments
           - Pricing and positioning strategy
           - Key differentiators
        4. Competitive Assessment
           - Strengths and weaknesses
           - Feature comparison
           - Customer feedback analysis
        5. Summarize a SWOT Analysis
        
        ### Formatting
        Construct the analysis in a clear markdown format, utilizing bullet points, tables, and other formatting tools for readability. 
        Focus on concrete data points and observations from the provided sources. If you want to display visualizations, you can just describe the visualization and another agent will create the visualization.
        Don't make assumptions or include information not supported by the data.
        
        Conclude with specific, actionable recommendations based on your findings.
        
        ### Tools
        You are given a search tool to further research any information you need.
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