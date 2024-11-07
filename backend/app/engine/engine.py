from typing import List, Optional

from app.agents.stage_2_initial_research.competitor_analysis.workflow import create_competitor_analysis
from app.agents.example.workflow import create_workflow
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.workflow import Workflow


def get_chat_engine(
    session_id: str,
    chat_history: Optional[List[ChatMessage]] = None, 
    email: Optional[str] = None, 
    mode: str = "not test", 
    **kwargs
) -> Workflow:
    if mode == "test":
        agent_workflow = create_workflow(session_id, chat_history, email=email, **kwargs)
    else:
        agent_workflow = create_competitor_analysis(session_id, chat_history, email, **kwargs)
    return agent_workflow
