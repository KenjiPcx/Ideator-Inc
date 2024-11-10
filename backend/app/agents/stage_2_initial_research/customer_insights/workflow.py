import asyncio
from textwrap import dedent
from typing import List, Optional
from app.agents.stage_2_initial_research.customer_insights.reddit_researcher import create_reddit_researcher
from app.agents.stage_2_initial_research.customer_insights.insights_analyzer import create_insights_analyzer
from app.agents.stage_2_initial_research.customer_insights.insights_critic import create_insights_critic
from app.agents.example.reporter import create_reporter
from app.engine.tools.file_writer import write_file
from llama_index.core.workflow import Context, Event, StartEvent, StopEvent, Workflow, step
from app.workflows.single import AgentRunEvent, AgentRunResult, FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.prompts.base import PromptTemplate
from app.settings import Settings
from app.utils.json_validator import JsonValidationHelper

from pydantic import BaseModel, Field
from typing import List

class CustomerSearchQueries(BaseModel):
    search_queries: List[str] = Field(description="Queries for Reddit search")

class CustomerInsight(BaseModel):
    pain_point: str = Field(description="Description of customer pain point or need")
    summary: str = Field(description="Brief summary of the pain point/need")
    severity: str = Field(description="How severe/important this pain point is")
    evidence: List[str] = Field(
        description="Supporting evidence such as: quotes, specific examples, user stories, or other data points that validate this pain point"
    )
    willingness_to_pay: str = Field(description="Any indication of pricing expectations or willingness to pay")

class CustomerInsightsReport(BaseModel):
    overall_summary: str = Field(description="High-level summary of customer pain points and needs")
    key_insights: List[CustomerInsight] = Field(
        description="List of significant customer insights with supporting evidence"
    )
    user_demographics: List[str] = Field(
        description="Identified user demographics and characteristics"
    )
    competitor_insights: List[str] = Field(
        description="Insights about competitors and existing solutions"
    )
    sources: List[str] = Field(description="List of sources analyzed")

class CustomerReportCritique(BaseModel):
    satisfied: bool = Field(description="Whether the critique is satisfied")
    critique: str = Field(description="Critique of the insights analysis")
    feedback: str = Field(description="Feedback on the insights analysis")

class ExecuteSearchEvent(Event):
    query: str

class CombineSearchesEvent(Event):
    pass

class AnalyzeInsightsEvent(Event):
    input: str

class CritiqueInsightsEvent(Event):
    input: str

class ReportEvent(Event):
    input: str

class CustomerInsightsWorkflow(Workflow):
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
                name="Customer Insights starter",
                msg=f"Starting customer insights research on task: {ev.input}",
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
                name="Customer Insights starter",
                msg=f"Generated {len(queries.search_queries)} search queries, which are: {queries.search_queries}",
            )
        )
        
        # Send events for each search
        for query in queries.search_queries[:self.num_queries]:
            ctx.send_event(ExecuteSearchEvent(query=query))
            
        return None

    @step(num_workers=3)
    async def execute_reddit_search(self, ctx: Context, ev: ExecuteSearchEvent) -> CombineSearchesEvent:
        prompt = f"""
            We are researching customer insights for this task: {ctx.data["task"]}
            Please analyze Reddit discussions using this query: {ev.query}
        """
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Reddit researcher",
                msg=f"Searching Reddit for insights using query: {ev.query}",
            )
        )
        
        reddit_researcher = create_reddit_researcher(chat_history=[])
        
        result = await self.run_agent(ctx, reddit_researcher, prompt)
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Reddit researcher", 
                msg=f"Done searching Reddit for insights using query: {ev.query}",
            )
        )
        
        # Store results
        ctx.data.setdefault("reddit_search_results", []).append(result.response.message.content)
        
        # Track completed searches
        ctx.data["num_completed"] = ctx.data.get("num_completed", 0) + 1
        
        return CombineSearchesEvent()

    @step()
    async def combine_searches(self, ctx: Context, ev: CombineSearchesEvent) -> AnalyzeInsightsEvent:
        # Only proceed if all searches are complete
        completed_searches = ctx.data.get("num_completed", 0)
        if completed_searches < self.num_queries:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Search combiner",
                    msg=f"{completed_searches} out of {self.num_queries} searches complete, waiting for more searches",
                )
            )
            return None
            
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Search combiner",
                msg=f"All {self.num_queries} Reddit searches complete, combining results for analysis",
            )
        )
        
        # Initialize critic iteration counter
        ctx.data["critic_iteration"] = 0
        
        return AnalyzeInsightsEvent(input="")

    @step()
    async def analyze(
        self, ctx: Context, ev: AnalyzeInsightsEvent, insights_analyzer: FunctionCallingAgent
    ) -> CritiqueInsightsEvent | ReportEvent:
        if ctx.data.get("critic_iteration", 0) == 0:
            prompt = dedent(f"""
                We are researching customer insights for this task: {ctx.data['task']}
                
                Here are the findings from Reddit discussions:
                {ctx.data.get('reddit_search_results', [])}
                
                Please analyze these findings and provide a comprehensive customer insights report.
            """)
        else:
            prompt = dedent(f"""
                We are researching customer insights for this task: {ctx.data['task']}
                
                The critic provided this feedback on your previous analysis: {ev.input}
                
                Please refine the analysis based on this feedback.
            """)
            
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Insights analyzer",
                msg=f"Analyzing all research found across Reddit",
            )
        )
        result = await self.run_agent(ctx, insights_analyzer, prompt)
        ctx.data["insights_analysis_result"] = result.response.message.content
        
        # If we have reached the max number of critic iterations, return the final analysis to the reporter
        if ctx.data.get("critic_iteration", 0) >= self.max_critic_iterations:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Insights analyzer",
                    msg=f"Reached max critic iterations, returning final analysis to reporter",
                )
            )
            return ReportEvent(input=ctx.data["insights_analysis_result"])
        
        # Otherwise, return the analysis to the critic
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Insights analyzer",
                msg=f"Returning analysis to critic for feedback",
            )
        )
        ctx.data["critic_iteration"] = ctx.data.get("critic_iteration", 0) + 1
        return CritiqueInsightsEvent(input=ctx.data["insights_analysis_result"])

    @step()
    async def critique(
        self, ctx: Context, ev: CritiqueInsightsEvent, insights_critic: FunctionCallingAgent
    ) -> AnalyzeInsightsEvent | ReportEvent:
        result = await self.run_agent(
            ctx, insights_critic,
            f"""We are researching customer insights for this task: {ctx.data['task']}
            Please critique this insights analysis and provide actionable feedback: {ev.input}"""
        )
        
        parser = JsonValidationHelper(CustomerReportCritique, Settings.llm)
        parsed_response = await parser.validate_and_fix(result.response.message.content)
        
        if parsed_response and parsed_response.satisfied:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Insights critic",
                    msg=f"Critique satisfied, returning analysis to reporter",
                )
            )
            return ReportEvent(input=ctx.data["insights_analysis_result"])
            
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Insights critic",
                msg=f"Critique not satisfied, returning analysis to analyzer for refinement",
            )
        )
        return AnalyzeInsightsEvent(input=result.response.message.content)

    @step()
    async def report(
        self, ctx: Context, ev: ReportEvent, reporter: FunctionCallingAgent
    ) -> StopEvent:
        try:
            result = await self.run_agent(
                ctx, reporter,
                f"""We have completed customer insights research for this task: {ctx.data['task']}
                Here is the final analysis: {ev.input}
                Please create a clear, actionable report."""
            )
            
            # Save all research data
            reddit_search_results = '\n'.join(ctx.data.get('reddit_search_results', []))
            write_file(
                content=dedent(f"""
                    # Customer Insights Analysis
                    
                    ### Task
                    {ctx.data["task"]}
                    
                    ### Research Results
                    #### Reddit Search Results:
                    {reddit_search_results}
                    
                    ### Final Report
                    {ctx.data["insights_analysis_result"]}
                    
                    ### Sources
                    {ctx.data.get('sources', [])}
                """),
                file_name="customer_insights_report.txt",
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
    ) -> CustomerSearchQueries:
        prompt_template = PromptTemplate(
            dedent("""
                ### Instructions
                You are an expert at generating effective search queries for customer research. Given a user's product idea, generate {num_queries} search queries that can help understand customer pain points, needs, and behaviors:

                1. Break down the idea into core components
                2. For each component, generate targeted search queries that focus on:
                   
                   Pain Points & Problems:
                   - "Biggest problems with [product/service] Reddit"
                   - "Alternatives to [competitor's product] Reddit"
                   - "What customers wish existed for [niche/industry]"
                   
                   Customer Needs & Behaviors:
                   - How do people do [task] / solve [problem] in [industry]
                   - "Common pain points with [product/service] in [industry]"
                   - "Challenges customers face with [industry product/service]"
                   - "What's missing in [product/service] in [industry]"
                   
                   Willingness to Pay:
                   - "How much would you pay for [solution]"
                   - "Is [product/service] worth it Reddit"
                   - "Alternatives to expensive [product/service]"
                
                ### Output Format
                Return a JSON object with this structure:
                {{
                    "search_queries": ["query1", "query2", "query3"]
                }}
                
                ### Task:
                {task}
            """)
        )
        
        prompt = prompt_template.format(
            task=task,
            num_queries=num_queries
        )
        
        output = await Settings.llm.acomplete(prompt)
        validator = JsonValidationHelper(CustomerSearchQueries, Settings.llm)  
        json_content = await validator.validate_and_fix(output.text)
        return json_content

def create_customer_insights_workflow(
    session_id: str,
    chat_history: List[ChatMessage],
    email: str | None = None,
    num_queries: int = 3,
    max_critic_iterations: int = 3,
    timeout: int = 1800,
):
    workflow = CustomerInsightsWorkflow(
        session_id=session_id,
        timeout=timeout,
        chat_history=chat_history,
        num_queries=num_queries,
        max_critic_iterations=max_critic_iterations,
    )
    
    # Create report team
    insights_analyzer = create_insights_analyzer(chat_history=[])
    insights_critic = create_insights_critic(chat_history=[])
    insights_reporter = create_reporter(
        chat_history=chat_history, 
        session_id=session_id,
        email=email
    )
    
    workflow.add_workflows(
        insights_analyzer=insights_analyzer,
        insights_critic=insights_critic,
        reporter=insights_reporter,
    )
    
    return workflow
