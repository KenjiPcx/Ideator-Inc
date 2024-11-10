from typing import List
from textwrap import dedent
from llama_index.core import VectorStoreIndex, Document, SimpleDirectoryReader
from llama_index.core.tools import QueryEngineTool, ToolMetadata, FunctionTool
from llama_index.core.chat_engine.types import ChatMessage
from app.utils.paths import get_session_data_path
from app.workflows.single import FunctionCallingAgent
from app.engine.tools.tavily import tavily_qna_search

def _load_documents(session_id: str) -> List[Document]:
    research_path = get_session_data_path(session_id)
    print(research_path)
    if not research_path.exists():
        raise ValueError(f"No research data found for session {session_id}")
        
    return SimpleDirectoryReader(
        input_dir=str(research_path)
    ).load_data()

def _create_query_tools(documents: List[Document]) -> List[QueryEngineTool]:
    index = VectorStoreIndex.from_documents(documents)
    return [
        QueryEngineTool(
            query_engine=index.as_query_engine(),
            metadata=ToolMetadata(
                name="research_documents",
                description="ALWAYS TRY THIS FIRST. Contains information from all research documents, use this tool as a search engine to find answers based on the research done"
            )
        ),
        FunctionTool.from_defaults(tavily_qna_search, description="Ask a question to the web, it returns a detailed answer"),
    ]

def create_researcher(session_id: str, chat_history: List[ChatMessage], email: str) -> FunctionCallingAgent:
    documents = _load_documents(session_id)
    print(f"Loaded {len(documents)} documents")
    
    query_tools = _create_query_tools(documents)
    
    system_prompt = dedent("""
        You are a research assistant helping users understand the research conducted by other agents.
        You have access to all research documents and can answer questions about specific findings, comparisons between different aspects,
        and provide detailed analysis.

        IMPORTANT: When answering questions:
        1. ALWAYS check the research documents first using the research_documents tool
        2. Only if the information is not found in the research documents, use the web_search tool as a fallback, say something like "I couldn't find that information in the research documents, let me search the web for you" before doing so
        3. Clearly indicate when you're using information from web search vs. research documents
        4. Don't synthesize the information, just return the whole retrieved information.
        5. Do not make up answers.
    """)
    
    return FunctionCallingAgent(
        name="Research Assistant",
        description="A research assistant that can answer questions about the research conducted by other agents",
        tools=query_tools,
        verbose=True,
        system_prompt=system_prompt,
        chat_history=chat_history,
        use_name_as_workflow_name=True
    )
