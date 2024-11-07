from app.workflows.single import AgentRunEvent
from llama_index.core.agent import ReActAgent
from llama_index.core.memory import ChatMemoryBuffer
from typing import Optional, List
from llama_index.core.llms import LLM
from llama_index.core.memory.types import ChatMessage
from app.settings import Settings
class ReActAgentWithMemory(ReActAgent):
    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
        llm: LLM | None = None,
        max_iterations: int = 10,
        chat_history: Optional[List[ChatMessage]] = None,
        **kwargs
    ):
        # Initialize parent ReActAgent
        if llm is None:
            llm = Settings.llm
        print(f"Using LLM: {llm.metadata.model_name}")
        super().__init__(
            llm=llm, 
            context=system_prompt, 
            max_iterations=max_iterations, 
            **kwargs
        )
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        
        # Configure memory with chat history
        self.memory = ChatMemoryBuffer.from_defaults(
            llm=llm,
            chat_history=chat_history or [],
        )