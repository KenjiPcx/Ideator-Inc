from textwrap import dedent
from typing import List
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool
from app.engine.tools.tavily import tavily_search

def create_domain_researcher(name_prefix: str, chat_history: List[ChatMessage], domain: str):
    def domain_specific_search(search_query: str):
        return tavily_search(
            query=search_query,
            max_results=10,
            include_domains=[domain]
        )
    
    tools = [
        FunctionTool.from_defaults(
            domain_specific_search, 
            name="domain_search", 
            description=f"Search for content specifically on {domain}"
        ),
    ]

    prompt_instructions = dedent(f"""
        ### Context
        You are an analyst specialized in understanding content patterns on {domain}. 
        
        ### Instructions
        Your task is to:
        1. Search for content using the provided query
        2. Analyze the search results holistically
        3. Identify patterns, trends, and interesting insights
        4. Provide a high-level summary of what content creators are focusing on
        5. Extract high quality data backed evidence for your findings, and include them in the evidence field, they must be very detailed and complete, like if there's a statistic, quote, examples, stories, etc include them as detailed as possible, otherwise it will be pointless. In fact, even include some commentary and background information so future agents can use it.
        
        Use the domain_search tool to find content specifically on {domain}.
        
        ### Output Format
        Return your analysis in this JSON format:
        {{
            "overall_summary": "A comprehensive overview of the content landscape, key themes, and notable patterns",
            "key_trend_insights": [
                {{
                    "trend": "Name of specific content trend",
                    "summary": "Detailed explanation of what this trend involves",
                    "confidence": "High/Medium/Low",
                    "evidence": [
                        "Evidence with specific statistic or metric (e.g., '70% of top videos use this format') this seems to be because of...",
                        "Evidence with concrete example with context (e.g., 'Channel X's video with 1M views demonstrates...')",
                        "Evidence with notable quote or observation (e.g., 'Creators frequently mention...')"
                    ],
                }}
            ],
            "content_approaches": [
                "how to do X",
                "top 10 tools to do X",
            ],
            "other_insights": [
                "There are no videos on X"
            ]
        }}
        
        ### Important Notes
        - Focus on patterns and trends rather than individual pieces
        - Back up trends with specific evidence and metrics when available
        - Include engagement patterns and audience response
        - Look for unique angles or approaches
        - Consider what makes content successful in this space
        - Identify gaps or opportunities in the content landscape
    """)

    return FunctionCallingAgent(
        name=f"Domain Researcher ({name_prefix})",
        tools=tools,
        system_prompt=prompt_instructions,
        description=f"Expert at analyzing content patterns on {domain}",
        chat_history=chat_history,
    )