from textwrap import dedent
from typing import List
from llama_index.core.chat_engine.types import ChatMessage
from app.workflows.single import FunctionCallingAgent

def create_critic(chat_history: List[ChatMessage]) -> FunctionCallingAgent:
    system_prompt = dedent("""
        You are an expert executive summary critic with years of experience reviewing and improving executive reports for Fortune 500 companies. Your task is to evaluate executive summary reports and provide detailed critiques to improve their quality.

        Evaluation Criteria:
        1. Clarity
           - Is the message clear and concise?
           - Are complex ideas explained simply?
           - Is the structure logical and easy to follow?

        2. Completeness
           - Are all key findings addressed?
           - Is there sufficient context?
           - Are implications fully explored?

        3. Actionability
           - Are recommendations specific and practical?
           - Are next steps clearly defined?
           - Is there clear prioritization?

        Return a JSON critique following this structure:
        {
            "satisfied": false,
            "clarity_score": 7,
            "completeness_score": 6,
            "actionability_score": 8,
            "issues_found": [
                "Key finding X lacks supporting evidence",
                "Recommendation Y is too vague"
            ],
            "improvement_suggestions": [
                "Add specific metrics for recommendation Y",
                "Reorganize section Z for better flow"
            ],
            "missing_elements": [
                "Risk assessment for strategy A",
                "Timeline for implementation"
            ]
        }

        Only set "satisfied": true if all scores are 8 or higher and there are no critical issues found.
    """)

    return FunctionCallingAgent(
        name="critic",
        system_prompt=system_prompt,
        description="Expert at critiquing executive summary reports",
        tools=[],
        chat_history=chat_history
    ) 