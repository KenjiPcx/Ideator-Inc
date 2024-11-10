from typing import List, Optional
from textwrap import dedent
from app.agents.example.reporter import create_reporter
from app.agents.stage_2_initial_research.market_research.web_researcher import create_market_researcher
from app.agents.stage_2_initial_research.market_research.market_analyzer import create_market_analyzer
from app.agents.stage_2_initial_research.market_research.market_critic import MarketReportCritique, create_market_critic
from app.engine.tools.file_writer import write_file
from llama_index.core.workflow import Context, Event, StartEvent, StopEvent, Workflow, step
from app.workflows.single import AgentRunEvent, AgentRunResult, FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.prompts.base import PromptTemplate
from app.settings import Settings
from app.utils.json_validator import JsonValidationHelper

from pydantic import BaseModel, Field

class MarketSearchQueries(BaseModel):
    search_queries: List[str] = Field(description="Queries for market research")

class MarketInsight(BaseModel):
    category: str = Field(description="Category of market insight (TAM/SAM/SOM, Segment, Dynamic)")
    finding: str = Field(description="Key finding or insight")
    value: str = Field(description="Quantitative value or metric")
    source: str = Field(description="Source of the data")
    evidence: List[str] = Field(
        description="Supporting evidence such as: statistics, specific examples, quotes, or other data points"
    )

class MarketAnalysis(BaseModel):
    overall_summary: str = Field(description="High-level summary of market analysis")
    market_size: List[MarketInsight] = Field(
        description="Market size insights including TAM/SAM/SOM"
    )
    market_segments: List[MarketInsight] = Field(
        description="Market segmentation insights"
    )
    market_dynamics: List[MarketInsight] = Field(
        description="Market dynamics insights"
    )
    sources: List[str] = Field(description="List of sources")

class ExecuteSearchEvent(Event):
    query: str

class CombineSearchesEvent(Event):
    pass

class AnalyzeMarketEvent(Event):
    input: str

class CritiqueAnalysisEvent(Event):
    input: str

class ReportEvent(Event):
    input: str

class MarketResearchWorkflow(Workflow):
    def __init__(self,
                session_id: str,
                chat_history: Optional[List[ChatMessage]] = None,
                num_queries: int = 3,
                timeout: int = 1000,
                max_critic_iterations: int = 3):
        super().__init__(timeout=timeout)
        self.session_id = session_id
        self.chat_history = chat_history or []
        self.num_queries = num_queries
        self.max_critic_iterations = max_critic_iterations

    @step()
    async def start(self, ctx: Context, ev: StartEvent) -> ExecuteSearchEvent:
        ctx.data["task"] = ev.input
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Market Research starter",
                msg=f"Starting market research on task: {ev.input}",
            )
        )

        # Generate search queries
        queries = await self._generate_search_queries(
            task=ev.input,
            chat_history=[],
            num_queries=self.num_queries
        )
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Market Research starter",
                msg=f"Generated {len(queries.search_queries)} search queries, which are: {queries.search_queries}",
            )
        )
        
        # Send events for each search
        for query in queries.search_queries[:self.num_queries]:
            ctx.send_event(ExecuteSearchEvent(query=query))
            
        return None

    @step(num_workers=5)
    async def execute_web_search(self, ctx: Context, ev: ExecuteSearchEvent) -> CombineSearchesEvent:
        prompt = f"""
            We are researching market size and segments for this task: {ctx.data["task"]}
            Please analyze market data using this query: {ev.query}
        """
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Market researcher",
                msg=f"Searching market data using query: {ev.query}",
            )
        )
        
        web_researcher = create_market_researcher(name_prefix="general", chat_history=[])
        result = await self.run_agent(ctx, web_researcher, prompt)
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Market researcher", 
                msg=f"Done searching market data using query: {ev.query}",
            )
        )
        
        # Store results
        ctx.data.setdefault("market_search_results", []).append(result.response.message.content)
        
        # Track completed searches
        ctx.data["num_completed"] = ctx.data.get("num_completed", 0) + 1
        
        return CombineSearchesEvent()
    
    @step()
    async def combine_searches(self, ctx: Context, ev: CombineSearchesEvent) -> AnalyzeMarketEvent:
        if ctx.data.get("num_completed", 0) < self.num_queries:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Research combiner",
                    msg=f"Completed {ctx.data.get('num_completed', 0)} out of {self.num_queries} searches",
                )
            )
            return None
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Research combiner",
                msg=f"All {self.num_queries} searches have been completed, asking analyzer to analyze",
            )
        )

        return AnalyzeMarketEvent(input="All search results have been combined")

    @step()
    async def analyze(
        self, ctx: Context, ev: AnalyzeMarketEvent, market_analyzer: FunctionCallingAgent
    ) -> CritiqueAnalysisEvent | ReportEvent:
        if ctx.data.get("critic_iteration", 0) == 0:
            prompt = dedent(f"""
                We are researching market size and segments for this task: {ctx.data['task']}
                
                Here are the findings from market research:
                {ctx.data.get('market_search_results', [])}
                
                Please analyze these findings and provide a comprehensive market analysis report.
            """)
        else:
            prompt = dedent(f"""
                We are researching market size and segments for this task: {ctx.data['task']}
                
                The critic provided this feedback on your previous analysis: {ev.input}
                
                Please refine the analysis based on this feedback.
            """)
            
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Market analyzer",
                msg=f"Analyzing all research found across markets",
            )
        )
        result = await self.run_agent(ctx, market_analyzer, prompt)
        ctx.data["market_analysis_result"] = result.response.message.content
        
        # If we have reached the max number of critic iterations, return the final analysis to the reporter
        if ctx.data.get("critic_iteration", 0) >= self.max_critic_iterations:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Market analyzer",
                    msg=f"Reached max critic iterations, returning final analysis to reporter",
                )
            )
            return ReportEvent(input=ctx.data["market_analysis_result"])
        
        # Otherwise, return the analysis to the critic
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Market analyzer",
                msg=f"Returning analysis to critic for feedback",
            )
        )
        ctx.data["critic_iteration"] = ctx.data.get("critic_iteration", 0) + 1
        return CritiqueAnalysisEvent(input=ctx.data["market_analysis_result"])

    @step()
    async def critique(
        self, ctx: Context, ev: CritiqueAnalysisEvent, market_critic: FunctionCallingAgent
    ) -> AnalyzeMarketEvent | ReportEvent:
        result = await self.run_agent(
            ctx, market_critic,
            f"""We are researching market size and segments for this task: {ctx.data['task']}
            Please critique this market analysis and provide actionable feedback: {ev.input}"""
        )
        
        parser = JsonValidationHelper(MarketReportCritique, Settings.llm)
        parsed_response = await parser.validate_and_fix(result.response.message.content)
        
        if parsed_response and parsed_response.satisfied:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Market critic",
                    msg=f"Critique satisfied, returning analysis to reporter",
                )
            )
            return ReportEvent(input=ctx.data["market_analysis_result"])
            
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Market critic",
                msg=f"Critique not satisfied, returning analysis to analyzer for refinement",
            )
        )
        return AnalyzeMarketEvent(input=result.response.message.content)

    @step()
    async def report(
        self, ctx: Context, ev: ReportEvent, reporter: FunctionCallingAgent
    ) -> StopEvent:
        try:
            result = await self.run_agent(
                ctx, reporter,
                f"""We have completed market research for this task: {ctx.data['task']}
                Here is the final analysis: {ev.input}
                Please create a clear, actionable report."""
            )
            
            # Save all research data
            write_file(
                content=dedent(f"""
                    # Market Research Analysis
                    
                    ### Task
                    {ctx.data["task"]}
                    
                    ### Research Results
                    Market Research Results:
                    {ctx.data.get('market_search_results', [])}
                    
                    ### Final Report
                    {ctx.data["market_analysis_result"]}
                    
                    ### Sources
                    {ctx.data.get('sources', [])}
                """),
                file_name="market_report.txt",
                session_id=self.session_id,
            )
            
            return StopEvent(result=result)
        except Exception as e:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="reporter",
                    msg=f"Error creating report: {str(e)}",
                )
            )
            return StopEvent(result=None)

    async def run_agent(self, ctx: Context, agent: FunctionCallingAgent, input: str) -> AgentRunResult:
        try:
            handler = agent.run(input=input, streaming=False)
            async for event in handler.stream_events():
                if type(event) is not StopEvent:
                    ctx.write_event_to_stream(event)
            return await handler
        except Exception as e:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name=agent.name,
                    msg=f"Error running agent: {str(e)}",
                )
            )
            raise
            
    async def _generate_search_queries(
        self, task: str, chat_history: List[ChatMessage], 
        num_queries: int
    ) -> MarketSearchQueries:
        prompt_template = PromptTemplate(
            dedent("""
                ### Base Instructions
                You are an agent that thinks step by step and uses tools to satisfy the user's request. You first make a plan and execute it step by step through an observation - reason - action loop. In your responses, you always include all reasoning before taking an action or concluding.
                
                ### Instructions
                You are an expert at generating effective search queries for market research. Given a user's product idea which also contains their target market and ideal customer profile, you must generate {num_queries} search queries that can help define the market size and segments for the user's product idea:
                1. Break down the idea into core components
                2. For each component, generate targeted search queries that focus on:
                   
                   Total Market Size:
                   - Who are facing the problem of [problem]
                   - "Number of people in [target market]"
                   - "Total addressable market size for [industry/sector/product]"
                   - "Projected market value for [industry] over next 5 years" 
                   - "Market revenue and growth rate for [industry]"
                   
                   Growth Trends:
                   - "Historical growth trends in [industry/sector]"
                   - "Current and projected CAGR for [industry]"
                   - "Future demand trends in [specific niche]"
                
                ### Output Format
                Return a JSON object with this structure:
                {
                    "search_queries": ["query1", "query2", "query3"]
                }
                
                ### Task:
                {task}
            """)
        )
        
        prompt = prompt_template.format(
            task=task,
            num_queries=num_queries
        )
        
        output = await Settings.llm.acomplete(prompt)
        validator = JsonValidationHelper(MarketSearchQueries, Settings.llm)  
        json_content = await validator.validate_and_fix(output.text)
        return json_content

def create_market_research_workflow(
    session_id: str,
    chat_history: List[ChatMessage],
    email: str | None = None,
    num_queries: int = 3,
    max_critic_iterations: int = 3,
    timeout: int = 1800,
):
    workflow = MarketResearchWorkflow(
        session_id=session_id,
        chat_history=chat_history,
        timeout=timeout,
        num_queries=num_queries,
        max_critic_iterations=max_critic_iterations,
    )
    
    # Create report team
    market_analyzer = create_market_analyzer(chat_history=[])
    market_critic = create_market_critic(chat_history=[])
    reporter = create_reporter(chat_history=chat_history, session_id=session_id, email=email)
    
    workflow.add_workflows(
        market_analyzer=market_analyzer,
        market_critic=market_critic,
        reporter=reporter,
    )
    
    return workflow 