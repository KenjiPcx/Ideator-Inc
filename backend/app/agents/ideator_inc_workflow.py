from typing import AsyncGenerator, List, Optional

# Import our agent team
from app.agents.stage_2_initial_research import create_competitor_analysis
from app.agents.stage_6_output_production import create_podcast_workflow

from app.workflows.single import AgentRunResult
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.workflow import (
    Context,
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)

### High Level Events ###
class QnaWorkflowEvent(Event):
    input: str

class ResearchWorkflowEvent(Event):
    input: str

class StartResearchPipelineEvent(Event):
    input: str

class GetCritiqueEvent(Event):
    input: str

### Initial Research Events ###
class CompetitorAnalysisCompleteEvent(Event):
    input: str

class CustomerInsightsCompleteEvent(Event):
    input: str

class OnlineTrendsCompleteEvent(Event):
    input: str

class MarketResearchCompleteEvent(Event):
    input: str

class MarketResearchFeedbackEvent(Event):
    input: str

### Feasibility Research Events ###
class StartFeasibilityResearchEvent(Event):
    pass

### Output Production Events ###
class CreatePodcastEvent(Event):
    pass

class IdeatorIncWorkflow(Workflow):
    def __init__(
        self,
        session_id: str,
        timeout: int = 1800, 
        chat_history: Optional[List[ChatMessage]] = None
    ):
        '''This is a very long running multi-step workflow, so we set a default timeout of 30 minutes'''
        super().__init__(timeout=timeout)
        self.session_id = session_id
        self.chat_history = chat_history or []
    
    ### Initial Research Analysts Team 1 ###
    @step()
    async def competitor_research(self, ctx: Context, ev: StartEvent, competitor_researcher: Workflow) -> CreatePodcastEvent:
        prompt = f"Conduct a competitor analysis session based on the following idea: {ev.input}"
        self.run_sub_workflow(ctx, competitor_researcher, prompt)
        return CreatePodcastEvent(input=ev.input)

    ### Output Production ###
    @step()
    async def podcast_generation(self, ctx: Context, ev: CreatePodcastEvent) -> StopEvent:
        return StopEvent(result=ev.input)
    
    async def run_sub_workflow(
        self,
        ctx: Context,
        workflow: Workflow,
        input: str,
        streaming: bool = False,
    ) -> AgentRunResult | AsyncGenerator:
        handler = workflow.run(input=input, streaming=streaming)
        # bubble all events while running the executor to the planner
        async for event in handler.stream_events():
            # Don't write the StopEvent from sub task to the stream
            if type(event) is not StopEvent:
                ctx.write_event_to_stream(event)
        return await handler
    
def create_idea_research_workflow(session_id: str, chat_history: Optional[List[ChatMessage]] = None, **kwargs):
    # Create all the necessary agents here
    
    # Initial Research Team
    competitor_researcher = create_competitor_analysis(session_id=session_id, chat_history=chat_history, **kwargs)
    
    # Final Output
    podcast_generator = create_podcast_workflow(session_id=session_id, chat_history=chat_history, **kwargs)

    workflow = IdeatorIncWorkflow(session_id=session_id, timeout=3600, chat_history=chat_history)

    workflow.add_workflows(
        competitor_researcher=competitor_researcher,
        podcast_generator=podcast_generator,
    )
    return workflow
