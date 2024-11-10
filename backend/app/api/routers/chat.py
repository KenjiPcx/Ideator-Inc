import logging

from app.api.routers.models import (
    ChatData,
)
from app.api.routers.vercel_response import VercelStreamResponse
from app.engine.engine import get_chat_engine
from app.agents.stage_6_output_production import create_researcher
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

chat_router = r = APIRouter()

logger = logging.getLogger("uvicorn")


@r.post("")
async def chat(
    request: Request,
    data: ChatData,
    background_tasks: BackgroundTasks,
):
    try:
        last_message_content = data.get_last_message_content()
        messages = data.get_history_messages(include_agent_messages=True)

        # The chat API supports passing private document filters and chat params
        # but agent workflow does not support them yet
        # ignore chat params and use all documents for now
        # TODO: generate filters based on doc_ids
        params = data.data or {}
        logger.info(f"Email: {data.email}")
        logger.info(f"Session ID: {data.sessionId}")
        engine = get_chat_engine(session_id=data.sessionId, chat_history=messages, email=data.email, params=params, mode="prod")

        event_handler = engine.run(input=last_message_content, streaming=True)
        return VercelStreamResponse(
            request=request,
            chat_data=data,
            event_handler=event_handler,
            events=engine.stream_events(),
        )
    except Exception as e:
        logger.exception("Error in chat engine", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in chat engine: {e}",
        ) from e

@r.post("/qna")
async def research_qna(
    request: Request,
    data: ChatData,
):
    try:
        agent = create_researcher(session_id=data.sessionId, chat_history=data.get_history_messages(include_agent_messages=True), email=data.email)
        
        event_handler = agent.run(
            input=data.get_last_message_content(),
            streaming=True
        )
        
        return VercelStreamResponse(
            request=request,
            chat_data=data,
            event_handler=event_handler,
            events=agent.stream_events(),
        )
    except Exception as e:
        logger.exception("Error in research QA", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in research QA: {e}",
        ) from e
