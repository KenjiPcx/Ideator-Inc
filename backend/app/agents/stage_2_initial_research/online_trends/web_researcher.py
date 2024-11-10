from textwrap import dedent
from typing import List
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool
from app.engine.tools.tavily import tavily_search
from app.engine.tools.web_reader import read_webpage

def create_web_researcher(name_prefix: str, chat_history: List[ChatMessage], domains: List[str] | None = None):
    def trend_search(search_query: str):
        return tavily_search(
            query=search_query,
            max_results=5,
            include_domains=domains
        )
    
    tools = [
        FunctionTool.from_defaults(trend_search, name="trend_search", description="Search the web for information about trends"),
        FunctionTool.from_defaults(async_fn=read_webpage, name="read_webpage", description="Read and extract content from a webpage"),
    ]

    prompt_instructions = dedent("""
        ### Context
        You are an expert at finding and validating trends through web research. 
        
        ### Instructions
        Your task is to:
        1. Search for relevant trends using the provided query
        2. Read and analyze promising pages
        3. Extract interesting insights on trends
        4. Assess source credibility
        5. Extract high quality data backed evidence for your findings, and include them in the evidence field, they must be very detailed and complete, like if there's a statistic, quote, examples, stories, case studies, etc include them as detailed as possible, otherwise it will be pointless. In fact, even include some commentary and background information so future agents can use it.
        
        Use the tools available to:
        1. Search web content with the `trend_search` tool
        2. Read and extract detailed content with the `read_webpage` tool
        3. If you are not satisfied with the results, you can search again with a different query one more time, otherwise accept the results, note your findings and terminate.
        
        ### Output Format
        Return your findings in this format:
        {
            "overall_summary": "High-level summary of content landscape and key patterns",
            "key_trend_insights": [
                {
                    "trend": "Name/description of trend",
                    "summary": "Brief summary of what the trend involves",
                    "relevance": "How this trend relates to the product idea",
                    "impact": "Potential impact on the product idea",
                    "evidence": [
                        "Detailed evidence with stats, quotes, story, case studies, etc, with enough background information so future agents can use it",
                        "Detailed evidence 2"
                    ]
                }
            ],
            "other_insights": ["Other interesting insight 1"],
            "sources": ["URL 1"]
        }
    """)

    return FunctionCallingAgent(
        name=f"Web Researcher ({name_prefix})",
        tools=tools,
        system_prompt=prompt_instructions,
        description="Expert at finding and validating trends through web research",
        chat_history=chat_history,
    ) 