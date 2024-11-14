from textwrap import dedent
from typing import AsyncGenerator, List, Optional

# Import our agent team
from app.agents.stage_2_initial_research import create_competitor_analysis_workflow, create_customer_insights_workflow, create_online_trends_workflow, create_market_research_workflow
from app.agents.stage_6_output_production import create_podcast_workflow, create_executive_summary_workflow

from app.workflows.single import AgentRunEvent, AgentRunResult
from llama_index.core.llms import ChatMessage, ChatResponse
from llama_index.core.workflow import (
    Context,
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)
from app.settings import Settings
from llama_index.core.prompts import PromptTemplate

class StartCompetitorAnalysisResearchEvent(Event):
    input: str

class StartCustomerInsightsResearchEvent(Event):
    input: str

class StartOnlineTrendsResearchEvent(Event):
    input: str

class StartMarketResearchEvent(Event):
    input: str

class CombineResearchResultsEvent(Event):
    input: str
    
class CreatePodcastEvent(Event):
    input: str

class CreateExecutiveSummaryEvent(Event):
    input: str

class CombinePostProductionResultsEvent(Event):
    pass

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
    async def start(self, ctx: Context, ev: StartEvent) -> StartMarketResearchEvent | StartCustomerInsightsResearchEvent | StartOnlineTrendsResearchEvent | StartCompetitorAnalysisResearchEvent:
        ctx.data["idea"] = ev.input
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Starting research on idea: {ev.input}",
                workflow_name="Research Manager"
            )
        )
        
        ctx.send_event(StartCompetitorAnalysisResearchEvent(input=ev.input))
        ctx.send_event(StartCustomerInsightsResearchEvent(input=ev.input))  
        ctx.send_event(StartOnlineTrendsResearchEvent(input=ev.input))
        ctx.send_event(StartMarketResearchEvent(input=ev.input))
        
        return None
    
    ### Initial Research Analysts Team 1 ###
    @step()
    async def competitor_research(self, ctx: Context, ev: StartCompetitorAnalysisResearchEvent, competitor_researcher: Workflow) -> CombineResearchResultsEvent:
        prompt = f"Conduct a competitor analysis session based on the following idea: {ev.input}"
        res = await self.run_sub_workflow(ctx, competitor_researcher, prompt, workflow_name="Competitor Analysis Analyst")
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Competitor research completed",
                workflow_name="Research Manager"
            )
        )
        
        ctx.data["competitor_research_result"] = res.response.message.content
        ctx.data["research_completed"] = ctx.data.get("research_completed", 0) + 1
        return CombineResearchResultsEvent(input=res.response.message.content)
    
    @step()
    async def customer_insights(self, ctx: Context, ev: StartCustomerInsightsResearchEvent, customer_insights_researcher: Workflow) -> CombineResearchResultsEvent:
        prompt = f"Conduct a customer insights session based on the following idea: {ev.input}"
        res = await self.run_sub_workflow(ctx, customer_insights_researcher, prompt, workflow_name="Customer Insights Analyst")
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Customer insights research completed",
                workflow_name="Research Manager"
            )
        )
        
        ctx.data["customer_insights_result"] = res.response.message.content
        ctx.data["research_completed"] = ctx.data.get("research_completed", 0) + 1
        return CombineResearchResultsEvent(input=res.response.message.content)
    
    @step()
    async def online_trends(self, ctx: Context, ev: StartOnlineTrendsResearchEvent, online_trends_researcher: Workflow) -> CombineResearchResultsEvent:
        prompt = f"Conduct a online trends research session based on the following idea: {ev.input}"
        res = await self.run_sub_workflow(ctx, online_trends_researcher, prompt, workflow_name="Online Trends Analyst")
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Online trends research completed",
                workflow_name="Research Manager"
            )
        )
        
        ctx.data["online_trends_result"] = res.response.message.content
        ctx.data["research_completed"] = ctx.data.get("research_completed", 0) + 1
        return CombineResearchResultsEvent(input=res.response.message.content)
    
    @step()
    async def market_research(self, ctx: Context, ev: StartMarketResearchEvent, market_research_researcher: Workflow) -> CombineResearchResultsEvent:
        prompt = f"Conduct a market research session based on the following idea: {ev.input}"
        res = await self.run_sub_workflow(ctx, market_research_researcher, prompt, workflow_name="Market Research Analyst")
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Market research completed",
                workflow_name="Research Manager"
            )
        )
        
        ctx.data["market_research_result"] = res.response.message.content
        ctx.data["research_completed"] = ctx.data.get("research_completed", 0) + 1
        return CombineResearchResultsEvent(input=res.response.message.content)

    @step()
    async def combine_research_results(self, ctx: Context, ev: CombineResearchResultsEvent) -> CreatePodcastEvent | CreateExecutiveSummaryEvent:
    
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
        ctx.send_event(CreatePodcastEvent(input=ev.input))
        ctx.send_event(CreateExecutiveSummaryEvent(input=ev.input))
        return None

    ### Output Production ###
    @step()
    async def podcast_generation(self, ctx: Context, ev: CreatePodcastEvent, podcast_generator: Workflow) -> CombinePostProductionResultsEvent:
        res = await self.run_sub_workflow(ctx, podcast_generator, ev.input, workflow_name="Podcaster")
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Podcast generation completed",
                workflow_name="Research Manager"
            )
        )
        
        ctx.data["podcast_result"] = res
        ctx.data["post_production_completed"] = ctx.data.get("post_production_completed", 0) + 1
        return CombinePostProductionResultsEvent()
    
    @step()
    async def executive_summary_generation(self, ctx: Context, ev: CreateExecutiveSummaryEvent, executive_summarizer: Workflow) -> CombinePostProductionResultsEvent:
        res = await self.run_sub_workflow(ctx, executive_summarizer, ev.input, workflow_name="Executive Summarizer")
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Executive summary generation completed",
                workflow_name="Research Manager"
            )
        )
        
        ctx.data["executive_summary_result"] = res
        ctx.data["post_production_completed"] = ctx.data.get("post_production_completed", 0) + 1
        return CombinePostProductionResultsEvent()
    
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
        
        responses = f"""
        Market Research Result: 
        {ctx.data.get('market_research_result', "None")}
        Customer Insights Result: 
        {ctx.data.get('customer_insights_result', "None")}
        Online Trends Result: 
        {ctx.data.get('online_trends_result', "None")}
        Competitor Analysis Result: 
        {ctx.data.get('competitor_research_result', "None")}
        Podcast Result: 
        {ctx.data.get('podcast_result', "None")}
        Executive Summary Result: 
        {ctx.data.get('executive_summary_result', "None")}
        """

        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Ideator Inc Workflow",
                msg=f"Post production completed and combined results:\n{responses}",
                workflow_name="Research Manager"
            )
        )
        
        # prompt = PromptTemplate(
        #     dedent("""
        #         ### Instructions
        #         Summarize the research results into a concise message, except for the URLs.
        #         And create a clean, readable message that lists all the URLs mentioned in the research results.
        #         Format it as a simple list with clear labels for each URL.
                
        #         ### Research Results
        #         {responses}

        #         ### Output Format
        #         Here are your research results:
        #         <Summarized message>

        #         Here are the artifacts generated from the research:
        #         Market Research: [URL]
        #         Customer Insights: [URL]
        #         Online Trends Analysis: [URL]
        #         Competitor Analysis: [URL]
        #         Podcast: [URL]
        #         Executive Summary: [URL]
                
        #         ### Output Message
        #     """)
        # )
        
        # formatted_prompt = prompt.format(responses=responses)
        # clean_output = await Settings.llm.acomplete(formatted_prompt)
        
        return StopEvent(result=responses)
    
    async def run_sub_workflow(
        self,
        ctx: Context,
        workflow: Workflow,
        input: str,
        streaming: bool = False,
        workflow_name: str = ""
    ) -> AgentRunResult | AsyncGenerator:
        try:
            handler = workflow.run(input=input, streaming=streaming)
            # bubble all events while running the executor to the planner
            async for event in handler.stream_events():
                # Don't write the StopEvent from sub task to the stream
                if type(event) is not StopEvent:
                    if isinstance(event, AgentRunEvent):
                        event.workflow_name = workflow_name
                    ctx.write_event_to_stream(event)
            return await handler
        except Exception as e:
            error_message = f"Error in {workflow_name}: {str(e)}"
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Ideator Inc Workflow",
                    msg=error_message,
                    workflow_name=workflow_name
                )
            )
            # Return a failed result object
            return AgentRunResult(
                response=ChatResponse(
                    message=ChatMessage(
                        content=f"Failed to complete {workflow_name} due to an error: {str(e)}"
                    )
                ),
                sources=[]
            )
    
def create_idea_research_workflow(session_id: str, chat_history: Optional[List[ChatMessage]] = None, email: Optional[str] = None, **kwargs):
    # Initial Research Team
    timeout = 1200
    competitor_researcher = create_competitor_analysis_workflow(
        session_id=session_id, 
        chat_history=chat_history, 
        email=email, 
        num_queries=2, 
        max_critic_iterations=2, 
        timeout=timeout
    )
    customer_insights_researcher = create_customer_insights_workflow(
        session_id=session_id, 
        chat_history=chat_history, 
        email=email, 
        num_queries=2, 
        max_critic_iterations=2, 
        timeout=timeout
    )
    online_trends_researcher = create_online_trends_workflow(
        session_id=session_id, 
        chat_history=chat_history, 
        email=email, 
        num_queries=2, 
        max_critic_iterations=2, 
        timeout=timeout
    )
    market_research_researcher = create_market_research_workflow(
        session_id=session_id, 
        chat_history=chat_history, 
        email=email, 
        num_queries=2, 
        max_critic_iterations=2, 
        timeout=timeout
    )
    
    # Final Output
    podcast_generator = create_podcast_workflow(
        session_id=session_id, 
        chat_history=chat_history, 
        timeout=1800,
        max_iterations=1
    )
    executive_summarizer = create_executive_summary_workflow(
        session_id=session_id, 
        chat_history=chat_history, 
        email=email,
        timeout=1800,
        max_iterations=1
    )

    workflow = IdeatorIncWorkflow(session_id=session_id, timeout=3600, chat_history=chat_history, initial_team_size=4, post_production_team_size=2)

    workflow.add_workflows(
        competitor_researcher=competitor_researcher,
        customer_insights_researcher=customer_insights_researcher,
        online_trends_researcher=online_trends_researcher,
        market_research_researcher=market_research_researcher,
        podcast_generator=podcast_generator,
        executive_summarizer=executive_summarizer,
    )
    return workflow
