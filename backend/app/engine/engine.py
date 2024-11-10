from typing import List, Optional

from app.agents.ideator_inc_workflow import create_idea_research_workflow
from app.agents.example.workflow import create_workflow
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.workflow import Workflow


def get_chat_engine(
    session_id: str,
    chat_history: Optional[List[ChatMessage]] = None, 
    email: Optional[str] = None, 
    mode: str = "test", 
    **kwargs
) -> Workflow:
    if mode == "test":
        agent_workflow = create_workflow(session_id, chat_history, email=email, **kwargs)
    else:
        agent_workflow = create_idea_research_workflow(session_id, chat_history, email, **kwargs)
    return agent_workflow
