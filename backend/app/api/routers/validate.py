from typing import List
from fastapi import APIRouter, Request
from app.api.routers.models import ChatData
from app.api.routers.vercel_response import VercelStreamResponse
from app.agents.stage_1_problem_definition.idea_prescreener import create_idea_prescreener_agent

validate_router = r = APIRouter()

@r.post("")
async def validate(
    request: Request,
    data: ChatData,
):
    messages = data.get_history_messages(include_agent_messages=True)
    agent = create_idea_prescreener_agent(chat_history=messages)
    
    event_handler = agent.run(
        input=data.get_last_message_content(),
        streaming=True,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "update_idea",
                    "description": "Update the displayed idea details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "problem_statement": {"type": "string"},
                            "product_idea": {"type": "string"},
                            "unique_value_proposition": {"type": "string"},
                            "user_story": {"type": "string"},
                            "how_it_works": {"type": "string"},
                            "target_users": {"type": "string"}
                        }
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "confirm_idea",
                    "description": "Confirm the idea is validated and ready for research",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]
    )
    
    return VercelStreamResponse(
        request=request,
        chat_data=data,
        event_handler=event_handler,
        events=agent.stream_events(),
    ) 