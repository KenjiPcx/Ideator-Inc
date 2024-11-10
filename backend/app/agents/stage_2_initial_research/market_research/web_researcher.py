from textwrap import dedent
from typing import List
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool
from app.engine.tools.tavily import tavily_search
from app.engine.tools.web_reader import read_webpage

def create_market_researcher(name_prefix: str, chat_history: List[ChatMessage], domains: List[str] | None = None):
    def market_search(search_query: str):
        return tavily_search(
            query=search_query,
            max_results=5,
            include_domains=domains,
            search_depth="advanced"
        )
    
    tools = [
        FunctionTool.from_defaults(
            market_search, 
            name="market_search", 
            description="Search for market data and statistics"
        ),
        FunctionTool.from_defaults(
            async_fn=read_webpage, 
            name="read_webpage", 
            description="Read and extract content from a webpage"
        ),
    ]

    prompt_instructions = dedent("""
        ### Context
        You are an expert market researcher at finding and analyzing market research data. 
        
        ### Instructions
        Your task is to:
        1. Search for relevant market data using the provided query, use it as a starting point for your research
        2. Read and analyze promising pages
        3. Extract any relevant high quality data that would be useful for a market analysis report, in full details, here are some examples:
           - Market size statistics
           - Growth rates and projections
           - Segment breakdowns
           - Competitive data
           - Expert quotes and insights
           - Case studies and examples
           Include detailed background information so future agents can use it effectively.
        4. Identify what to query for next time based on your findings, you can form hypothesis and continue researching
        5. Stop searching only after you have used the search tool 3 times, not all your findings and insights and then terminate the program.
        
        Use the tools available to:
        1. Search for market data with the `market_search` tool
        2. Read and extract detailed content with the `read_webpage` tool
        
        ### Output Format
        Return your findings in this format:
        {
            "overall_summary": "High-level summary of market findings",
            "market_insights": [
                {
                    "category": "TAM/SAM/SOM | Segment | Dynamic",
                    "finding": "Key market finding or insight",
                    "value": "Quantitative metric or value",
                    "source": "Source of the data",
                    "evidence": [
                        "Detailed evidence with stats, quotes, examples, case studies with background info",
                        "Additional evidence details"
                    ]
                }
            ],
            "other_insights": ["Other relevant market insight"],
            "sources": ["URL 1"]
        }
        
        Focus on finding concrete market data including:
        - Total market size (TAM)
        - Serviceable market size (SAM)
        - Target market size (SOM) 
        - Growth rates and projections
        - Market segments and breakdowns
        - Regional distribution
        - Competitive landscape
    """)

    return FunctionCallingAgent(
        name=f"{name_prefix}_web_researcher",
        tools=tools,
        system_prompt=prompt_instructions,
        description="Expert at finding and analyzing market research data",
        chat_history=chat_history,
    ) 