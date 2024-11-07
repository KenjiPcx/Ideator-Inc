from llama_index.core.tools.function_tool import FunctionTool
from typing import Literal, Optional, List
import os

MAX_RESULTS = 5

def tavily_search(
    query: str,
    search_depth: str = "advanced",
    max_results: int = MAX_RESULTS,
    api_key: Optional[str] = None,
    topic: Literal["general", "news"] = "general",
    include_domains: Optional[List[str]] = None,
):
    """
    Use this function to search for any query using Tavily's API.
    Args:
        query (str): The query to search.
        search_depth (str): The search depth to use ('basic' or 'advanced'). Default is 'advanced'.
        max_results (int): The maximum number of results to be returned. Default is 10.
        api_key (Optional[str]): Tavily API key. If not provided, will look for TAVILY_API_KEY env variable.
    """
    try:
        from tavily import TavilyClient
    except ImportError:
        raise ImportError(
            "tavily-python package is required to use this function. "
            "Please install it by running: `poetry add tavily-python` or `pip install tavily-python`"
        )

    api_key = api_key or os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("Tavily API key is required. Please provide it or set TAVILY_API_KEY environment variable.")

    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=query,
        search_depth=search_depth,
        max_results=max_results,
        topic=topic,
        include_domains=include_domains,
    )
    
    return response


def tavily_qna_search(
    query: str,
    api_key: Optional[str] = None,
):
    """
    Use this function to get quick answers to questions using Tavily's API.
    Args:
        query (str): The question to ask.
        api_key (Optional[str]): Tavily API key. If not provided, will look for TAVILY_API_KEY env variable.
    """
    try:
        from tavily import TavilyClient
    except ImportError:
        raise ImportError(
            "tavily-python package is required to use this function. "
            "Please install it by running: `poetry add tavily-python` or `pip install tavily-python`"
        )

    api_key = api_key or os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("Tavily API key is required. Please provide it or set TAVILY_API_KEY environment variable.")

    client = TavilyClient(api_key=api_key)
    response = client.qna_search(query=query)
    
    return response


def get_tools(**kwargs):
    return [
        FunctionTool.from_defaults(tavily_search, description="Search the web for information, it returns a list of urls and content"),
        FunctionTool.from_defaults(tavily_qna_search, description="Ask a question to the web, it returns a detailed answer"),
    ]