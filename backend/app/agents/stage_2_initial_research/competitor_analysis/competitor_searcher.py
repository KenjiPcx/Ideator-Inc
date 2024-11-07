from textwrap import dedent
from typing import List
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool

from app.engine.tools.tavily import tavily_search
from app.engine.tools.web_reader import read_webpage
from pydantic import BaseModel, Field

class CompetitorInfo(BaseModel):
    name: str = Field(description="The name of the competitor")
    description: str = Field(description="A 2-3 sentence description of the product / startup")
    direct_competitor: bool = Field(description="Whether the competitor is a direct competitor to the user's product idea")
    source_url: str = Field(description="The url to the source of the information")
    relevance_factors: List[str]  = Field(description="Why is it a competitor?")

class CompetitorSearchResponse(BaseModel):
    sources: List[str] = Field(description="List of sources used for research")
    insights: List[str] = Field(description="Key insights from the competitor research")
    competitors: List[CompetitorInfo] = Field(description="Detailed information about each competitor found")

def create_competitor_searcher(chat_history: List[ChatMessage]):
    def curated_competitor_search(search_query: str):
        return tavily_search(query=search_query, max_results=5, include_domains=["ycombinator.com", "reddit.com", "producthunt.com", "news.ycombinator.com", "hackernews.com", "appsumo.com", "g2.com"])
    
    tools = [
        FunctionTool.from_defaults(tavily_search, name="search", description="Search the web for information, it returns a list of urls and content"),
        FunctionTool.from_defaults(curated_competitor_search, name="curated_competitor_search", description="Search a curated domain of websites for information, it returns a list of urls and content"),
        FunctionTool.from_defaults(async_fn=read_webpage, name="read_webpage", description="Access a webpage and read it"),
    ]

    prompt_instructions = dedent("""
        ### Base Instructions
        You are an agent that thinks step by step and uses tools to satisfy the user's request. You first make a plan and execute it step by step through an observation - reason - action loop. In your responses, you always include all reasoning before taking an action or concluding.
        
        ### Instructions
        You are an expert competitor analyst. Your goal is to identify and analyze direct competitors to a product idea - companies or products that are solving the same problem in a similar way.

        Follow these steps:
        1. You are given a search query, use it to find competitors using the `curated_competitor_search` tool for a curated search and the `search` tool for a general search for competitors. You must use both tools, you don't need to modify the query, just use it as is.

        2. After calling both tools, analyze the search results to identify competitors and extract interesting insights, you can read the page content using the `read_webpage` tool:
           - Prioritize relevant competitors that are solving the same problem in a similar way
           - Maximum of the top 4 most relevant competitors

        3. For each competitor, gather:
           - Product/company name
           - A clear description of their solution (2-3 sentences)
           - source url
           - Specific features/approaches that overlap with the proposed idea
           - Whether they're a true direct competitor or just adjacent

        4. Note any relevant insights about competition or search results:
           - Summarize the search results, what they mostly contain
           - How saturated is this specific approach
           - Any products in development but not yet launched
           - Recent entries or exits in this specific space
           - If no direct competitors exist, note this finding
           - If there are news or teasing about a product but it's not yet launched, note this finding
           - If there is a reason why the product idea is not a good idea or have no chance of succeeding, note this finding

        5. Return a JSON object only without any other text with the following structure:
        {
            "sources": ["source 1", "source 2"],
            "insights": ["summary of findings","interesting insight 1", "interesting insight 2"],
            "competitors": [
                {
                    "name": "Competitor Name",
                    "direct_competitor": true/false,
                    "description": "2-3 sentence description",
                    "source_url": "URL",
                    "relevance_factors": ["specific overlapping features/approaches"]
                }
            ]
        }
    """)

    return FunctionCallingAgent(
        name="competitor_searcher",
        tools=tools,
        system_prompt=prompt_instructions,
        description="Expert at finding competing products and companies",
        chat_history=chat_history,
    )