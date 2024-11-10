import asyncio
from textwrap import dedent
from typing import List, Optional
from app.agents.example.reporter import create_reporter
from app.agents.stage_2_initial_research.online_trends.domain_researcher import create_domain_researcher
from app.agents.stage_2_initial_research.online_trends.trend_analyzer import create_trend_analyzer
from app.agents.stage_2_initial_research.online_trends.trend_critic import create_trend_critic
from app.agents.stage_2_initial_research.online_trends.web_researcher import create_web_researcher
from app.engine.tools.file_writer import write_file
from llama_index.core.workflow import Context, Event, StartEvent, StopEvent, Workflow, step
from app.workflows.single import AgentRunEvent, AgentRunResult, FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.prompts.base import PromptTemplate
from app.settings import Settings
from app.utils.json_validator import JsonValidationHelper

from pydantic import BaseModel, Field
from typing import List

class TrendSearchQueries(BaseModel):
    search_queries: List[str] = Field(description="Queries for general web search")

class TrendInsight(BaseModel):
    trend: str = Field(description="Name or description of the content trend")
    summary: str = Field(description="Brief summary of what this trend involves")
    relevance: str = Field(description="How this trend relates to the product idea")
    impact: str = Field(description="Potential impact on the product idea")
    evidence: List[str] = Field(
        description="Supporting evidence such as: statistics, specific examples, quotes, engagement metrics, or other data points that validate this trend"
    )
    
class WebTrendInsight(BaseModel):
    overall_summary: str = Field(description="High-level summary of content landscape and key patterns")
    key_trend_insights: List[TrendInsight] = Field(
        description="List of significant content trends with supporting evidence"
    )
    other_insights: List[str] = Field(
        description="Other interesting insights that are worth noting"
    )
    sources: List[str] = Field(description="List of sources visited")

class DomainContentAnalysis(BaseModel):
    overall_summary: str = Field(description="High-level summary of content landscape and key patterns")
    key_trend_insights: List[TrendInsight] = Field(
        description="List of significant content trends with supporting evidence"
    )
    content_approaches: List[str] = Field(
        description="Common content strategies, formats, and presentation styles being used (e.g., 'how to do X', 'top 10 tools to do X')"
    )
    other_insights: List[str] = Field(
        description="Other interesting insights that are worth noting"
    )

class TrendReportCritique(BaseModel):
    satisfied: bool = Field(description="Whether the critique is satisfied")
    critique: str = Field(description="Critique of the trend analysis")
    feedback: str = Field(description="Feedback on the trend analysis")
    
class ExecuteSearchEvent(Event):
    query: str

class CombineSearchesEvent(Event):
    pass

class AnalyzeTrendsEvent(Event):
    input: str

class CritiqueTrendsEvent(Event):
    input: str

class ReportEvent(Event):
    input: str

class OnlineTrendsWorkflow(Workflow):
    def __init__(self,
                session_id: str,
                chat_history: Optional[List[ChatMessage]] = None,
                num_queries: int = 3,
                timeout: int = 1800,
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
                name="Trend Research starter",
                msg=f"Starting trend research on task: {ev.input}",
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
                name="Trend Research starter",
                msg=f"Generated {len(queries.search_queries)} search queries, which are: {queries.search_queries}",
            )
        )
        # Send events for each search
        for query in queries.search_queries[:self.num_queries]:
            ctx.send_event(ExecuteSearchEvent(query=query))
            
        return None

    @step(num_workers=3)
    async def execute_web_search(self, ctx: Context, ev: ExecuteSearchEvent) -> CombineSearchesEvent:
        prompt = f"""
            We are researching trends for this task: {ctx.data["task"]}
            Please analyze online trends using this query: {ev.query}
        """
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Web researcher",
                msg=f"Searching the web for trends using query: {ev.query}",
            )
        )
        
        general_web_researcher = create_web_researcher(name_prefix="general", chat_history=[])
        trendhunter_web_researcher = create_web_researcher(name_prefix="trendhunter", chat_history=[], domains=["trendhunter.com"])
        reddit_web_researcher = create_web_researcher(name_prefix="reddit", chat_history=[], domains=["reddit.com"])
    
        web_researcher_tasks = [
            self.run_agent(ctx, general_web_researcher, prompt),
            self.run_agent(ctx, trendhunter_web_researcher, prompt),
            self.run_agent(ctx, reddit_web_researcher, prompt),
        ]
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Web researcher",
                msg=f"Done searching the web for trends using query: {ev.query}",
            )
        )
        
        results = await asyncio.gather(*web_researcher_tasks)
        
        for result in results:  
            # Store results
            ctx.data.setdefault("web_search_results", []).append(result.response.message.content)
        
        # Track completed searches
        ctx.data["num_completed"] = ctx.data.get("num_completed", 0) + 1
        
        return CombineSearchesEvent()

    @step(num_workers=3)
    async def execute_domain_search(self, ctx: Context, ev: ExecuteSearchEvent) -> CombineSearchesEvent:
        prompt = f"""
            We are researching trends for this task: {ctx.data["task"]}
            Please analyze online content for trends using this query: {ev.query}
        """
        
        youtube_domain_researcher = create_domain_researcher(name_prefix="youtube", chat_history=[], domain="youtube.com")
        tiktok_domain_researcher = create_domain_researcher(name_prefix="tiktok", chat_history=[], domain="tiktok.com")
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Domain researcher",
                msg=f"Searching the web for trends using query: {ev.query}",
            )
        )
        
        domain_researcher_tasks = [
            self.run_agent(ctx, youtube_domain_researcher, prompt),
            self.run_agent(ctx, tiktok_domain_researcher, prompt),
        ]
        
        results = await asyncio.gather(*domain_researcher_tasks)

        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Domain researcher",
                msg=f"Done searching the web for trends using query: {ev.query}",
            )
        )
        
        for result in results:
            # Store results
            ctx.data.setdefault("domain_search_results", []).append(result.response.message.content)
        
        # Track completed searches
        ctx.data["num_completed"] = ctx.data.get("num_completed", 0) + 1
        
        return CombineSearchesEvent()
    
    @step()
    async def combine_searches(self, ctx: Context, ev: CombineSearchesEvent) -> AnalyzeTrendsEvent:
        # Check if all searches are complete, double events to collect as we are getting both web and domain searches
        num_searches = self.num_queries * 2
        if ctx.data.get("num_completed", 0) < num_searches:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Research combiner",
                    msg=f"Completed {ctx.data.get('num_completed', 0)} out of {num_searches} searches",
                )
            )
            return None
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Research combiner",
                msg=f"All {num_searches} searches have been completed, asking analyzer to analyze",
            )
        )

        return AnalyzeTrendsEvent(input="All search results have been combined")

    @step()
    async def analyze(
        self, ctx: Context, ev: AnalyzeTrendsEvent, trend_analyzer: FunctionCallingAgent
    ) -> CritiqueTrendsEvent | ReportEvent:
        if ctx.data.get("critic_iteration", 0) == 0:
            prompt = dedent(f"""
                We are researching trends for this task: {ctx.data['task']}
                
                Here are the findings from web searches across the web, reddit and trendhunter:
                {ctx.data.get('web_search_results', [])}
                
                Here are the findings from content trends across domains like youtube and tiktok:
                {ctx.data.get('domain_search_results', [])}
                
                Please analyze these findings and provide a comprehensive trend analysis report.
            """)
        else:
            prompt = dedent(f"""
                We are researching trends for this task: {ctx.data['task']}
                
                The critic provided this feedback on your previous analysis: {ev.input}
                
                Please refine the analysis based on this feedback.
            """)
            
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Trend analyzer",
                msg=f"Analyzing all research found across the web and domains",
            )
        )
        result = await self.run_agent(ctx, trend_analyzer, prompt)
        ctx.data["trend_analysis_result"] = result.response.message.content
        
        # If we have reached the max number of critic iterations, return the final analysis to the reporter
        if ctx.data.get("critic_iteration", 0) >= self.max_critic_iterations:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Trend analyzer",
                    msg=f"Reached max critic iterations, returning final analysis to reporter",
                )
            )
            return ReportEvent(input=ctx.data["trend_analysis_result"])
        
        # Otherwise, return the analysis to the critic
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Trend analyzer",
                msg=f"Returning analysis to critic for feedback",
            )
        )
        ctx.data["critic_iteration"] = ctx.data.get("critic_iteration", 0) + 1
        return CritiqueTrendsEvent(input=ctx.data["trend_analysis_result"])

    @step()
    async def critique(
        self, ctx: Context, ev: CritiqueTrendsEvent, trend_critic: FunctionCallingAgent
    ) -> AnalyzeTrendsEvent | ReportEvent:
        result = await self.run_agent(
            ctx, trend_critic,
            f"""We are researching trends for this task: {ctx.data['task']}
            Please critique this trend analysis and provide actionable feedback: {ev.input}"""
        )
        
        parser = JsonValidationHelper(TrendReportCritique, Settings.llm)
        parsed_response = await parser.validate_and_fix(result.response.message.content)
        
        if parsed_response and parsed_response.satisfied:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Trend critic",
                    msg=f"Critique satisfied, returning analysis to analyzer",
                )
            )
            return ReportEvent(input=ctx.data["trend_analysis_result"])
            
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Trend critic",
                msg=f"Critique not satisfied, returning analysis to analyzer for refinement",
            )
        )
        return AnalyzeTrendsEvent(input=result.response.message.content)

    @step()
    async def report(
        self, ctx: Context, ev: ReportEvent, reporter: FunctionCallingAgent
    ) -> StopEvent:
        try:
            result = await self.run_agent(
                ctx, reporter,
                f"""We have completed trend research for this task: {ctx.data['task']}
                Here is the final analysis: {ev.input}
                Please create a clear, actionable report."""
            )
            
            # Save all research data
            web_search_results = '\n'.join(ctx.data.get('web_search_results', []))
            domain_search_results = '\n'.join(ctx.data.get('domain_search_results', []))
            write_file(
                content=dedent(f"""
                    # Online Trends Analysis
                    
                    ### Task
                    {ctx.data["task"]}
                    
                    ### Research Results
                    #### General Search Results:
                    {web_search_results}
                    
                    #### Domain Search Results:
                    {domain_search_results}
                    
                    ### Final Report
                    {ctx.data["trend_analysis_result"]}
                    
                    ### Sources
                    {ctx.data.get('sources', [])}
                """),
                file_name="trend_report.txt",
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
    ) -> TrendSearchQueries:
        prompt_template = PromptTemplate(
            dedent("""
                ### Context
                You are an expert at generating effective search queries to research online trends. 
                
                ### Instructions
                Given a user's startup idea:
                1. Break down the idea into 3-4 core components or themes
                2. For each component, generate targeted search queries that:
                   - Focus on recent market trends (last 2-3 years)
                   - Explore emerging technologies and innovations
                   - Investigate market dynamics and consumer behavior
                   - Consider competitive landscape and industry shifts
                
                Your queries should follow these patterns:
                - "latest trends in [industry/technology] [year]"
                - "[industry] market analysis [year]"
                - "emerging [technology] applications in [industry]"
                - "future of [component] [year-year range]"
                - "[industry] consumer behavior trends"
                
                ### Example
                For a "Smart home garden monitoring system":
                
                Core components:
                1. IoT/Smart home technology
                2. Garden/Plant care
                3. Monitoring/Automation
                4. Consumer gardening
                
                Example queries:
                - "latest smart home IoT trends"
                - "indoor gardening technology market analysis"
                - "plant monitoring automation innovations"
                - "consumer behavior smart garden products"
                - "future of home agriculture in 10 years"
                
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
        validator = JsonValidationHelper(TrendSearchQueries, Settings.llm)  
        json_content = await validator.validate_and_fix(output.text)
        return json_content

def create_online_trends_workflow(
    session_id: str,
    chat_history: List[ChatMessage],
    email: str | None = None,
    num_queries: int = 3,
    max_critic_iterations: int = 3,
    timeout: int = 1800,
):
    workflow = OnlineTrendsWorkflow(
        session_id=session_id,
        timeout=timeout,
        chat_history=chat_history,
        num_queries=num_queries,
        max_critic_iterations=max_critic_iterations,
    )
    
    # Create report team
    trend_analyzer = create_trend_analyzer(chat_history=[])
    trend_critic = create_trend_critic(chat_history=[])
    reporter = create_reporter(chat_history=chat_history, session_id=session_id, email=email)
    
    workflow.add_workflows(
        trend_analyzer=trend_analyzer,
        trend_critic=trend_critic,
        reporter=reporter,
    )
    
    return workflow
