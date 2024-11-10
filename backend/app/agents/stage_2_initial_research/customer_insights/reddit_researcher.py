from textwrap import dedent
from typing import List
from app.engine.tools.web_reader import read_webpage
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool
from app.engine.tools.tavily import tavily_search

def create_reddit_researcher(chat_history: List[ChatMessage]):
    def reddit_search(search_query: str):
        return tavily_search(
            query=search_query,
            max_results=5,
            include_domains=["reddit.com"]
        )
        
    async def read_reddit_post(url: str):
        return await read_webpage(url, instruction="Extract the main content of the Reddit post, and the comments from the thread, ignore all other content")
    
    tools = [
        FunctionTool.from_defaults(
            reddit_search, 
            name="reddit_search",
            description="Search Reddit for customer discussions and insights"
        ),
        FunctionTool.from_defaults(
            async_fn=read_reddit_post, 
            name="read_reddit_post", 
            description="Read and extract content from a Reddit post"
        ),
    ]

    prompt_instructions = dedent("""
        ### Context
        You are an expert at finding and analyzing customer insights through Reddit discussions.
        
        ### Instructions
        Your task is to:
        1. Search Reddit discussions using the provided query
        2. Read and analyze promising threads and comments
        3. Extract valuable customer insights including:
           - Pain points and frustrations
           - Unmet needs and desires
           - Willingness to pay indicators
           - User stories and experiences
           - Demographics and characteristics
           - Reviews of existing solutions
        4. Extract high quality evidence for your findings - they must be very detailed and complete, including:
           - Direct quotes from users
           - Specific examples and stories
           - Pricing discussions
           - Feature requests
           - Competitor mentions
           Include enough context and background so future agents can use the evidence effectively.
        
        Use the tools available to:
        1. Search Reddit content with the `reddit_search` tool
        2. Read and extract detailed content with the `read_reddit_post` tool
        
        
        ### Output Format
        Return your findings as a json object in this format:
        {
            "summary": "High-level summary of findings",
            "insights": [
                {
                    "title": "Clear title of the insight",
                    "type": "pain_point | demographic | competitor | feature_request | pricing",
                    "summary": "Detailed explanation of the insight",
                    "evidence": [
                        {
                            "quote": "Direct quote from user with context",
                            "source": {
                                "url": "https://reddit.com/r/example/post",
                                "subreddit": "r/example",
                            }
                        }
                    ],
                }
            ]
        }

        Example:
        {
            "summary": "Mobile developers struggle with push notification reliability and are willing to pay premium for better solutions",
            "insights": [
                {
                    "title": "Poor notification delivery rates in China",
                    "type": "pain_point",
                    "summary": "iOS developers are experiencing <45% delivery rates in China, causing revenue loss and user complaints",
                    "evidence": [
                        {
                            "quote": "Losing $5k/month due to failed notification delivery in China. Tried Firebase, OneSignal, nothing works reliably. Users are churning because they miss important updates.",
                            "source": {
                                "url": "https://reddit.com/r/iOSProgramming/comments/abc123",
                                "subreddit": "r/iOSProgramming",
                            }
                        },
                        {
                            "quote": "Would instantly switch to any provider that can guarantee >95% delivery in Asia. Happy to pay 2-3x what we're paying now if it actually works.",
                            "source": {
                                "url": "https://reddit.com/r/androiddev/comments/xyz789",
                                "subreddit": "r/androiddev",
                            }
                        }
                    ],
                }
            ]
        }
    """)

    return FunctionCallingAgent(
        name="reddit_researcher",
        tools=tools,
        system_prompt=prompt_instructions,
        description="Expert at finding and analyzing customer insights through Reddit discussions",
        chat_history=chat_history,
    ) 