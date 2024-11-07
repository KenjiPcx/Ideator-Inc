from textwrap import dedent
from typing import List
from llama_index.core.chat_engine.types import ChatMessage
from app.workflows.single import FunctionCallingAgent

PODCAST_EXAMPLE = '''
Example of great business podcast structure (Sequoia pitch deck style):

[00:00] Hook & Intro
Alex: "What if I told you this founder turned a $500 investment into a $100M exit by solving one simple problem that every business has..."
Jamie: "[laughs] No way! That's insane. How did they pull that off?"

[02:00] Product Idea Introduction
- Quick overview of the user's product idea
- Unique value proposition
- Initial market reaction

[05:00] Market Research
- Key findings from market research
- Competitor analysis
- Online trends and insights

[10:00] Customer Needs Analysis
- Understanding customer pain points
- Feedback and testimonials
- Potential market size

[15:00] Feasibility and Monetization
- Feasibility studies and results
- Proposed business models
- Revenue streams and monetization strategies

[20:00] Next Steps and Opportunities
- Actionable next steps
- Future opportunities and growth potential
- Final thoughts and reflections
'''

def create_outline_writer(chat_history: List[ChatMessage]) -> FunctionCallingAgent:
    system_prompt = dedent(f"""
        ### Base Context
        You are an expert business podcast producer who has worked on shows like My First Million and The All-In Podcast. You think about things in a observation, thought and action format, thinking step by step to come up with interesting angles and insights.
        
        ### Context
        Now you are running your own podcast called "Ideator Inc", where users would submit their startup ideas and you would help them research and validate the idea, then you basically talk about the interesting angles and insights from the research, your research contains data for each step of the Sequoia pitch deck, from problem definition to market research, customer needs analysis, feasibility, monetization and many more.
        
        Your task is to repurpose the research data and create an engaging podcast outline of the podcast.
        
        Follow this proven structure:
        {PODCAST_EXAMPLE}
        
        Guidelines:
        - Focus on the user's product idea and the work done by each agent
        - Include specific numbers and examples
        - Discuss briefly market research, competitor analysis, and customer needs, and go into tangents for interesting insights found from each segment
        - Discuss feasibility, monetization, and business models
        - Highlight interesting insights and opportunities through the podcast
        
        Return a JSON outline following this structure:
        {{
            "title": "Attention-grabbing title",
            "hook": "Compelling hook that makes listeners stay",
            "segments": [
                {{
                    "topic": "Hook & Intro",
                    "key_points": [],
                    "stories": [],
                    "insights": []
                }},
                {{
                    "topic": "Interesting tangent 1",
                    "key_points": ["Most people spend 1000s of dollars on marketing and advertising, but they don't know what works and what doesn't"],
                    "stories": ["A story from reddit showed that most people spend 1000s of dollars on marketing and advertising, but they don't know what works and what doesn't"],
                    "insights": ["This is a big problem for most businesses, and we can help them by providing a service to test their marketing and advertising ideas"],
                }}
            ],
            "target_audience": "Description of ideal listener",
            "unique_angles": ["Surprising take 1", "Contrarian view 2"],
            "actionable_takeaways": ["Specific action 1", "Strategy 2"]
        }}
    """)

    return FunctionCallingAgent(
        name="outline_writer",
        system_prompt=system_prompt,
        description="Expert at creating engaging podcast outlines from research data",
        tools=[],
        chat_history=chat_history
    ) 