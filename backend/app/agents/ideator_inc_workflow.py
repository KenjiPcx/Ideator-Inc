from typing import AsyncGenerator, List, Optional

# Import our agent team
from app.agents.stage_2_initial_research import create_competitor_analysis_workflow, create_customer_insights_workflow, create_online_trends_workflow, create_market_research_workflow
from app.agents.stage_6_output_production import create_podcast_workflow, create_executive_summary_workflow

from app.workflows.single import AgentRunEvent, AgentRunResult
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.workflow import (
    Context,
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)

class StartResearchEvent(Event):
    input: str

class CombineResearchResultsEvent(Event):
    input: str
    
class CreatePostProductionEvent(Event):
    input: str

class CombinePostProductionResultsEvent(Event):
    input: str

class IdeatorIncWorkflow(Workflow):
    def __init__(
        self,
        session_id: str,
        email: Optional[str] = None,
        timeout: int = 1800, 
        initial_team_size: int = 4,
        post_production_team_size: int = 2,
        chat_history: Optional[List[ChatMessage]] = None
    ):
        '''This is a very long running multi-step workflow, so we set a default timeout of 30 minutes'''
        super().__init__(timeout=timeout)
        self.session_id = session_id
        self.email = email
        self.chat_history = chat_history or []
        self.initial_team_size = initial_team_size
        self.post_production_team_size = post_production_team_size
        
    @step()
    async def start(self, ctx: Context, ev: StartEvent) -> StartResearchEvent:
        ctx.data["task"] = ev.input
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Starting research on task: {ev.input}",
                workflow_name="Research Manager"
            )
        )
        
        return StartResearchEvent(input=ev.input)
    
    ### Initial Research Analysts Team 1 ###
    @step()
    async def competitor_research(self, ctx: Context, ev: StartResearchEvent, competitor_researcher: Workflow) -> CombineResearchResultsEvent:
        prompt = f"Conduct a competitor analysis session based on the following idea: {ev.input}"
        res = await self.run_sub_workflow(ctx, competitor_researcher, prompt)
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Competitor research completed",
                workflow_name="Research Manager"
            )
        )
        
        ctx.data["research_completed"] = ctx.data.get("research_completed", 0) + 1
        return CombineResearchResultsEvent(input=res.response.message.content)
    
    @step()
    async def customer_insights(self, ctx: Context, ev: CombineResearchResultsEvent, customer_insights_researcher: Workflow) -> CombineResearchResultsEvent:
        prompt = f"Conduct a customer insights session based on the following idea: {ev.input}"
        res = await self.run_sub_workflow(ctx, customer_insights_researcher, prompt, workflow_name="Customer Insights Analyst")
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Customer insights research completed",
                workflow_name="Research Manager"
            )
        )
        
        ctx.data["research_completed"] = ctx.data.get("research_completed", 0) + 1
        return CombineResearchResultsEvent(input=res.response.message.content)
    
    @step()
    async def online_trends(self, ctx: Context, ev: CombineResearchResultsEvent, online_trends_researcher: Workflow) -> CombineResearchResultsEvent:
        prompt = f"Conduct a online trends research session based on the following idea: {ev.input}"
        res = await self.run_sub_workflow(ctx, online_trends_researcher, prompt, workflow_name="Online Trends Analyst")
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Online trends research completed",
                workflow_name="Research Manager"
            )
        )
        
        ctx.data["research_completed"] = ctx.data.get("research_completed", 0) + 1
        
        return CombineResearchResultsEvent(input=res.response.message.content)
    
    @step()
    async def market_research(self, ctx: Context, ev: CombineResearchResultsEvent, market_research_researcher: Workflow) -> CombineResearchResultsEvent:
        prompt = f"Conduct a market research session based on the following idea: {ev.input}"
        res = await self.run_sub_workflow(ctx, market_research_researcher, prompt, workflow_name="Market Research Analyst")
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Market research completed",
                workflow_name="Research Manager"
            )
        )
        
        ctx.data["research_completed"] = ctx.data.get("research_completed", 0) + 1
        return CombineResearchResultsEvent(input=res.response.message.content)

    @step()
    async def combine_research_results(self, ctx: Context, ev: CombineResearchResultsEvent) -> CreatePostProductionEvent:
    
        # Wait for all research to be completed before combining
        research_completed = ctx.data.get("research_completed", 0)
        if research_completed < self.initial_team_size:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Ideator Inc Workflow",
                    msg=f"Collected {research_completed} research results out of {self.initial_team_size}",
                    workflow_name="Research Manager"
                )
            )
            return None
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Combining research results",
                workflow_name="Research Manager"
            )
        )
        return CreatePostProductionEvent(input=ev.input)

    ### Output Production ###
    @step()
    async def podcast_generation(self, ctx: Context, ev: CreatePostProductionEvent, podcast_generator: Workflow) -> CombinePostProductionResultsEvent:
        res = await self.run_sub_workflow(ctx, podcast_generator, ev.input, workflow_name="Podcaster")
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Podcast generation completed",
                workflow_name="Research Manager"
            )
        )
        ctx.data["podcast_res"] = res.response.message.content
        ctx.data["post_production_completed"] = ctx.data.get("post_production_completed", 0) + 1
        return CombinePostProductionResultsEvent(input=res.response.message.content)
    
    @step()
    async def executive_summary_generation(self, ctx: Context, ev: CombinePostProductionResultsEvent, executive_summarizer: Workflow) -> CombinePostProductionResultsEvent:
        res = await self.run_sub_workflow(ctx, executive_summarizer, ev.input, workflow_name="Executive Summarizer")
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Executive summary generation completed",
                workflow_name="Research Manager"
            )
        )
        ctx.data["executive_summary_res"] = res.response.message.content
        ctx.data["post_production_completed"] = ctx.data.get("post_production_completed", 0) + 1
        return CombinePostProductionResultsEvent(input=res.response.message.content)
    
    @step()
    async def combine_post_production_results(self, ctx: Context, ev: CombinePostProductionResultsEvent) -> StopEvent:
        post_production_completed = ctx.data.get("post_production_completed", 0)
        if post_production_completed < self.post_production_team_size:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Ideator Inc Workflow",
                    msg=f"Collected {post_production_completed} post production results out of {self.post_production_team_size}",
                    workflow_name="Research Manager"
                )
            )
            return None
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Post production completed and combined results",
                workflow_name="Research Manager"
            )
        )
        
        final_output = f"{ctx.data.get('podcast_res', ev.input)} \n\n {ctx.data.get('executive_summary_res', ev.input)}"
        return StopEvent(result=final_output)
    
    async def run_sub_workflow(
        self,
        ctx: Context,
        workflow: Workflow,
        input: str,
        streaming: bool = False,
        workflow_name: str = ""
    ) -> AgentRunResult | AsyncGenerator:
        handler = workflow.run(input=input, streaming=streaming)
        # bubble all events while running the executor to the planner
        async for event in handler.stream_events():
            # Don't write the StopEvent from sub task to the stream
            if type(event) is not StopEvent:
                if isinstance(event, AgentRunEvent):
                    event.workflow_name = workflow_name
                ctx.write_event_to_stream(event)
        return await handler
    
def create_idea_research_workflow(session_id: str, chat_history: Optional[List[ChatMessage]] = None, email: Optional[str] = None, **kwargs):
    # Initial Research Team
    competitor_researcher = create_competitor_analysis_workflow(session_id=session_id, chat_history=chat_history, email=email, **kwargs)
    customer_insights_researcher = create_customer_insights_workflow(session_id=session_id, chat_history=chat_history, email=email, **kwargs)
    online_trends_researcher = create_online_trends_workflow(session_id=session_id, chat_history=chat_history, email=email, **kwargs)
    market_research_researcher = create_market_research_workflow(session_id=session_id, chat_history=chat_history, email=email, **kwargs)
    
    # Final Output
    podcast_generator = create_podcast_workflow(session_id=session_id, chat_history=chat_history, **kwargs)
    executive_summarizer = create_executive_summary_workflow(session_id=session_id, chat_history=chat_history, email=email, **kwargs)

    workflow = IdeatorIncWorkflow(session_id=session_id, timeout=2000, chat_history=chat_history)

    workflow.add_workflows(
        competitor_researcher=competitor_researcher,
        customer_insights_researcher=customer_insights_researcher,
        online_trends_researcher=online_trends_researcher,
        market_research_researcher=market_research_researcher,
        podcast_generator=podcast_generator,
        executive_summarizer=executive_summarizer,
    )
    return workflow
