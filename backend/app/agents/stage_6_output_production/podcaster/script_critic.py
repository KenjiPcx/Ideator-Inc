from textwrap import dedent
from typing import List
from llama_index.core.chat_engine.types import ChatMessage
from app.workflows.single import FunctionCallingAgent

CRITIC_GUIDELINES = '''
What Makes a Great Business Podcast Episode:

1. Structure & Flow (25%)
- Clear narrative arc
- Smooth transitions
- Balanced pacing
- Natural conversation flow

2. Content Quality (30%)
- Unique insights/angles
- Specific examples/numbers
- Actionable takeaways
- Depth of analysis

3. Engagement (25%)
- Hook strength
- Energy level
- Host chemistry
- Entertainment value

4. Business Value (20%)
- Target audience relevance
- Practical applications
- Market insights
- Strategic value

Rating Scale:
9-10: Exceptional, MFM quality
7-8: Strong episode, minor improvements needed
5-6: Decent but needs significant work
<5: Requires major revision
'''

def create_script_critic(chat_history: List[ChatMessage]) -> FunctionCallingAgent:
    system_prompt = dedent(f"""
        You are an expert podcast critic and showrunner.
        
        Your task is to evaluate podcast scripts against these guidelines:
        {CRITIC_GUIDELINES}
        
        Common Issues to Flag:
        - Generic insights without specifics
        - Lack of energy/enthusiasm
        - Missing actionable takeaways
        - Poor host chemistry
        - Weak examples/stories
        
        Return a detailed critique following the ScriptCritique model with:
        - satisfied: Whether quality standards are met
        - overall_rating: Score from 1-10
        - strengths: What works well
        - weaknesses: Areas needing improvement
        - specific_feedback: Section-by-section notes
        - improvement_suggestions: Actionable recommendations
    """)

    return FunctionCallingAgent(
        name="script_critic",
        system_prompt=system_prompt,
        description="Expert at evaluating and improving podcast scripts",
        tools=[],
        chat_history=chat_history
    ) 