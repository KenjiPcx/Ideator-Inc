from typing import List
from llama_index.core import VectorStoreIndex, Document, SimpleDirectoryReader
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.agent import ReActAgent
from pathlib import Path

class ResearchQAAgent:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.research_path = Path(f"filestore/{session_id}")
        
    def _load_documents(self) -> List[Document]:
        if not self.research_path.exists():
            raise ValueError(f"No research data found for session {self.session_id}")
            
        return SimpleDirectoryReader(
            input_dir=str(self.research_path)
        ).load_data()
        
    def _create_query_engine_tools(self, documents: List[Document]) -> List[QueryEngineTool]:
        # Create an index for each document
        tools = []
        for doc in documents:
            index = VectorStoreIndex.from_documents([doc])
            tools.append(
                QueryEngineTool(
                    query_engine=index.as_query_engine(),
                    metadata=ToolMetadata(
                        name=doc.metadata.get("filename", "unknown"),
                        description=f"Contains information about {doc.metadata.get('description', 'research results')}"
                    )
                )
            )
        return tools
        
    def create_agent(self):
        documents = self._load_documents()
        query_engine_tools = self._create_query_engine_tools(documents)
        
        # Create a SubQuestionQueryEngine for sophisticated querying
        query_engine = SubQuestionQueryEngine.from_defaults(
            query_engine_tools=query_engine_tools,
            verbose=True
        )
        
        # Wrap in a ReAct agent for better interaction
        return ReActAgent.from_tools(
            query_engine_tools,
            verbose=True,
            system_prompt="""You are a research assistant helping users understand the research conducted by other agents.
            You have access to all research documents and can answer questions about specific findings, comparisons between different aspects,
            and provide detailed analysis."""
        )
