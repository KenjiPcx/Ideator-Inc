from textwrap import dedent
from typing import List
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool
from app.engine.tools.tavily import tavily_search
from app.engine.tools.web_reader import read_webpage
from pydantic import BaseModel, Field

class ProductDetails(BaseModel):
    homepage_url: str = Field(description="Official homepage URL of the product")
    value_proposition: str = Field(description="Main value proposition of the product")
    key_features: List[str] = Field(description="List of key features and capabilities")
    target_audience: List[str] = Field(description="Target customer segments or user types")
    tech_stack: List[str] = Field(description="Technologies or frameworks used, if mentioned")

class PricingInfo(BaseModel):
    pricing_model: str = Field(description="Type of pricing (freemium, subscription, one-time, etc)")
    plans: List[dict] = Field(description="List of pricing plans with details")
    free_trial: bool = Field(description="Whether a free trial is available")
    enterprise_offering: bool = Field(description="Whether they have enterprise/custom pricing")

class ReviewSummary(BaseModel):
    source: str = Field(description="Source of the review (platform name)")
    summary: str = Field(description="Overall summary of reviews from this source")
    rating: float = Field(description="Rating out of 5, if available, can be 0 if not available", default=0)
    review_count: int = Field(description="Number of reviews found, can be 0 if not available", default=0)

class SearchCompetitorDetailsResponse(BaseModel):
    name: str = Field(description="Name of the product")
    homepage_url: str = Field(description="Official homepage URL of the product")
    value_proposition: str = Field(description="Main value proposition of the product")
    key_features: List[str] = Field(description="List of key features and capabilities")
    target_audience: List[str] = Field(description="Target customer segments or user types")
    pricing_summary: str = Field(description="Summary of pricing structure, plans, and any special offerings")
    reviews_exist: bool = Field(description="Whether reviews exist for this product")
    reviews: List[ReviewSummary] = Field(description="Review summaries from different platforms")
    pros: List[str] = Field(description="Overall key positive points from all reviews")
    cons: List[str] = Field(description="Overall key negative points from all reviews")
    sources: List[str] = Field(description="List of URLs used for the analysis")
    
def create_competitor_researcher(chat_history: List[ChatMessage]):
    def search(query: str):
        return tavily_search(
            query=query,
            max_results=3,
            search_depth="advanced"
        )
        
    def review_search(query: str):
        return tavily_search(
            query=query,
            max_results=5,
            search_depth="advanced",
            include_domains=["reddit.com", "ycombinator.com", "g2.com", "trustpilot.com", "producthunt.com", "capterra.com", "appsumo.com"]
        )
    
    def scrape_product_details(url: str, product_name: str):
        return read_webpage(
            url=url,
            schema=ProductDetails.model_json_schema(),
            instruction=f"Extract detailed product information for {product_name} from their official website."
        )
    
    def scrape_pricing(url: str, product_name: str):
        return read_webpage(
            url=url,
            schema=PricingInfo.model_json_schema(),
            instruction=f"Extract detailed pricing information for {product_name}. Include all plans, features, and special offers."
        )
    
    def scrape_reviews(url: str, product_name: str):
        return read_webpage(
            url=url,
            schema=ReviewSummary.model_json_schema(),
            instruction=f"Analyze user reviews and feedback for {product_name}. Summarize key positive and negative points."
        )


    tools = [
        FunctionTool.from_defaults(search, name="search", description="Search the web for any information"),
        FunctionTool.from_defaults(review_search, name="review_search", description="Search on a curated list of websites for user reviews"),
        FunctionTool.from_defaults(async_fn=scrape_product_details, name="scrape_product_details", description="Extract detailed product information from a webpage"),
        FunctionTool.from_defaults(async_fn=scrape_pricing, name="scrape_pricing", description="Extract pricing information from a webpage"),
        FunctionTool.from_defaults(async_fn=scrape_reviews, name="scrape_reviews", description="Extract and analyze user reviews from a webpage, note that there may be no reviews on the site"),
    ]

    prompt_instructions = dedent("""
        ### Instructions
        You are an expert at analyzing competitor products through their online presence. Given some basic information about a competitor, follow these steps:

        1. Gather basic details from the official / trustworthy source:
            - If the provided url is from a trusted source (e.g., ProductHunt, YCombinator, official website), use it directly
            - Otherwise, use the `search` tool to search for the product's official website, or ProductHunt page, or YCombinator page
            - Use the scrape_product_details` tool to extract key information
            - If you are calling the scrape tool more than 2 times, and nothing is getting returned, you should accept defeat and terminate

        2. Gather pricing details:
           - Use the `search` tool to search for the product's pricing information
           - Use the `scrape_pricing` tool to extract pricing details
           - Note any special offers or enterprise options
           - If pricing is not available, note it as a free product

        3. Gather user feedback and reviews:
           - Use the `review_search` tool to search for product reviews on platforms like reddit, ycombinator, G2, Trustpilot, ProductHunt, you must scrape reviews from multiple sources (at least 2-3) to be less biased, if there are no results for reviews, note that the product is still very new and has no reviews yet
           - Use the `scrape_reviews` tool to extract review insights
           - Produce a summary of the reviews and feedback, and highlight any key insights
           - It is possible that there are no reviews on the site, in that case, search again for other platforms
           - Never skip this step, it is crucial for your analysis

        4. Return only a comprehensive JSON object containing:
           {
            "name": "Example Product",
            "homepage_url": "https://example.com",
            "value_proposition": "Project management tool for remote teams",
            "key_features": ["Task management", "Time tracking", "Team chat"],
            "target_audience": ["Remote teams", "Software companies"],
            "pricing_summary": "Offers a freemium model with paid plans starting at $10/month. Enterprise pricing available.",
            "reviews_exist": true,
            "reviews": [
                {
                    "source": "Product Hunt",
                    "summary": "Generally positive reviews highlighting ease of use and good support, with some concerns about limited features",
                    "rating": 4.5,
                    "review_count": 150
                }
            ],
            "pros": ["Easy to use", "Excellent customer support", "Reliable uptime"],
            "cons": ["Limited advanced features", "Higher pricing for enterprise", "Basic reporting"],
            "sources": [
                "https://example.com",
                "https://g2.com/products/example"
            ]
        }

        Tips for effective searching:
        + Use specific keyword combinations if app name is very generic (e.g., "{product} {keywords} pricing", "{product} {keywords} reviews", "{product} {keywords} official website")
        + Include review platforms in search queries when looking for feedback, would be useful to search on reddit, producthunt, trustpilot and the official website's reviews page if available
        + Try different variations of the product name if initial searches don't yield results
        + Double check by asking yourself at each step if the action taken was correct and the results are as expected
    """)

    return FunctionCallingAgent(
        name="Web Researcher (Competitor)",
        tools=tools,
        system_prompt=prompt_instructions,
        chat_history=chat_history,
        description="Expert at analyzing competitor products through their online presence",
    )
