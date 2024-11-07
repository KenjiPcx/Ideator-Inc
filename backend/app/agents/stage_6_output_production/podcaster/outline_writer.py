from textwrap import dedent
from typing import List
from llama_index.core.chat_engine.types import ChatMessage
from app.workflows.single import FunctionCallingAgent

PODCAST_EXAMPLE = '''
Example of great business podcast structure (My First Million style):

[00:00] Hook & Intro
Alex: "What if I told you this founder turned a $500 investment into a $100M exit by solving one simple problem that every business has..."
Jamie: "[laughs] No way! That's insane. How did they pull that off?"

[02:00] Quick Overview
- Problem statement
- Basic solution explanation
- Why it matters to business audience

[05:00] Deep Dive into Interesting Angles
- Surprising insights
- Behind-the-scenes stories
- Market analysis and opportunities

[15:00] Business Lessons & Takeaways
- Key strategies that worked
- Common pitfalls to avoid
- Market opportunities identified

[20:00] Actionable Insights
- How listeners can apply these lessons
- Resources and next steps
- Final thoughts
'''

def create_outline_writer(chat_history: List[ChatMessage]) -> FunctionCallingAgent:
    system_prompt = dedent(f"""
        You are an expert business podcast producer who has worked on shows like My First Million and The All-In Podcast.
        
        Your task is to analyze research data and create an engaging podcast outline.
        
        Follow this proven structure:
        {PODCAST_EXAMPLE}
        
        Guidelines:
        - Focus on surprising insights and contrarian takes
        - Include specific numbers and examples
        - Target sophisticated business audience
        - Look for interesting angles and opportunities
        
        Return a JSON outline following this structure:
        {{
            "title": "Attention-grabbing title",
            "hook": "Compelling hook that makes listeners stay",
            "segments": [
                {{
                    "timestamp": "00:00",
                    "topic": "Hook & Intro",
                    "key_points": [],
                    "stories": [],
                    "insights": []
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