from textwrap import dedent
from typing import List, Optional
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import BaseTool, QueryEngineTool, ToolMetadata
from app.engine.index import IndexConfig, get_index
from llama_index.indices.managed.llama_cloud import LlamaCloudIndex
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import os
from pathlib import Path

def _create_query_tools(session_id: str) -> List[BaseTool]:
    """Create query tools for the session's research data"""
    current_file = Path(__file__)
    data_dir = current_file.parent.parent.parent.parent.parent / "data" / session_id
    documents = SimpleDirectoryReader(
        str(data_dir)
    ).load_data()
    index = VectorStoreIndex.from_documents(documents)

    top_k = int(os.getenv("TOP_K", 5))
    tools = []

    if isinstance(index, LlamaCloudIndex):
        # Document-level retriever
        doc_retriever = index.as_query_engine(
            retriever_mode="files_via_content",
            similarity_top_k=top_k,
        )
        tools.append(
            QueryEngineTool(
                query_engine=doc_retriever,
                metadata=ToolMetadata(
                    name="query_documents",
                    description=dedent("""
                        Use this to retrieve entire research documents when you need broad context 
                        or need to analyze patterns across multiple findings.
                    """)
                )
            )
        )
        
        # Chunk-level retriever
        chunk_retriever = index.as_query_engine(
            retriever_mode="chunks",
            similarity_top_k=top_k,
        )
        tools.append(
            QueryEngineTool(
                query_engine=chunk_retriever,
                metadata=ToolMetadata(
                    name="query_chunks",
                    description=dedent("""
                        Use this to retrieve specific facts, statistics, or quotes from the research.
                        Better for finding precise information or evidence to support specific points.
                    """)
                )
            )
        )
    else:
        query_engine = index.as_query_engine(similarity_top_k=top_k)
        tools.append(
            QueryEngineTool(
                query_engine=query_engine,
                metadata=ToolMetadata(
                    name="query_research",
                    description="Use this to retrieve information from the research data."
                )
            )
        )
    
    return tools

def create_analyzer(chat_history: List[ChatMessage], session_id: str) -> FunctionCallingAgent:
    tools = _create_query_tools(session_id)
    
    system_prompt = dedent("""
        # Context
        You are an expert business analyst specializing in startup analysis and validation. 
        
        # Task
        Given a report outline, your task is to draft a comprehensive report following the Sequoia Capital pitch deck framework. You are able to use query tools to find supporting evidence for your analysis.

        # Analysis Framework
        For each section, you must provide detailed analysis backed by specific data, examples, and quotes from the research. Use the query tools to find supporting evidence.

        # Report Structure
        Your report must follow this exact structure in markdown format:

        ## Executive Summary
        Brief 2-3 paragraph overview highlighting the key findings and recommendations.

        ## 1. Problem Analysis
        - Clear problem statement
        - Market pain points with specific examples and data
        - Current solutions and their limitations
        - Supporting evidence from research (market data, user quotes, case studies)

        ## 2. Solution Analysis
        - Unique approach with specific details
        - Key features and benefits
        - Technical feasibility assessment
        - Implementation challenges and mitigation strategies
        - Supporting evidence (similar success stories, technical validation)

        ## 3. Why Now?
        - Market timing analysis with data
        - Technology enablers and trends
        - Societal/cultural shifts with evidence
        - Market readiness indicators
        - Supporting trends with specific examples

        ## 4. Unique Value Proposition
        - Clear differentiation factors
        - Competitive advantages with evidence
        - Value metrics and quantification
        - Customer benefits with specific examples
        - Supporting evidence (competitor comparisons, user feedback)

        ## 5. Market Size Analysis
        - TAM (Total Addressable Market) with specific numbers
        - SAM (Serviceable Addressable Market) with breakdown
        - SOM (Serviceable Obtainable Market) with justification
        - Growth projections with data sources
        - Market trends and dynamics

        ## 6. Competition Analysis
        - Direct competitors with detailed analysis
        - Indirect competitors and substitutes
        - Competitive landscape overview
        - Market positioning strategy
        - Competitive advantages and disadvantages

        ## 7. Feasibility Assessment
        - Technical feasibility (score/10 with detailed justification)
        - Market feasibility (score/10 with evidence)
        - Financial feasibility (score/10 with analysis)
        - Operational feasibility
        - Risk assessment and mitigation strategies

        ## Key Recommendations
        Prioritized list of actionable recommendations based on the analysis.

        ## Risk Analysis
        Detailed analysis of key risks and mitigation strategies.

        ## Next Steps
        Clear, actionable next steps prioritized by importance and urgency.

        # Guidelines for Analysis
        - Use query_documents for broad patterns and context
        - Use query_chunks for specific facts, quotes, and statistics
        - Every major point must be supported by data or examples
        - Include specific numbers where available
        - Use direct quotes from research when relevant
        - Identify patterns across different research areas
        - Highlight both opportunities and risks
        - Maintain objectivity in analysis
        - Use tables and bullet points for clarity where appropriate
        - Include specific examples and case studies
        - Cite sources when using specific data points

        Remember to:
        1. Be specific and data-driven
        2. Use clear, executive-level language
        3. Support all major points with evidence
        4. Maintain a balanced perspective
        5. Focus on actionable insights
    """)

    return FunctionCallingAgent(
        name="executive_analyzer",
        system_prompt=system_prompt,
        description="Expert at analyzing startup ideas using the Sequoia framework",
        tools=tools,
        chat_history=chat_history
    ) 