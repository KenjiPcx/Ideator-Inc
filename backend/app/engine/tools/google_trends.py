from typing import Dict, List, Optional
from serpapi import GoogleSearch
from app.settings import Settings
import os

async def google_trends_search(
    query: str,
    data_type: str = "TIMESERIES",
    time_range: str = "today 3-m",
    category: str = "all",
    api_key: Optional[str] = None,
) -> Dict:
    """
    Search Google Trends using SerpAPI.
    
    Args:
        query: Search query
        data_type: Type of data to return (TIMESERIES, GEO_MAP, RELATED_QUERIES, etc.)
        time_range: Time range for the data (today 12-m, today 3-m, today 1-m, etc.)
        category: Category to filter by (all, business, entertainment, etc.)
        api_key: SerpAPI key. If not provided, will look for SERP_API_KEY env variable.
        
    Returns:
        Dict containing the Google Trends data
    """
    api_key = api_key or os.getenv("SERP_API_KEY")
    if not api_key:
        raise ValueError("SerpAPI key is required. Please provide it or set SERP_API_KEY environment variable.")
        
    params = {
        "engine": "google_trends",
        "q": query,
        "data_type": data_type,
        "cat": category,
        "date": time_range,
        "api_key": api_key
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        return {
            "success": True,
            "data": results,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e)
        } 