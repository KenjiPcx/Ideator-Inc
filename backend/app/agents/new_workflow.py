from textwrap import dedent
from typing import AsyncGenerator, List, Optional, Dict
from enum import Enum

# Import our agent team
from app.agents.stage_1_problem_definition.problem_validator import ProblemValidatorFeedback, problem_validator_prompt_instructions
from app.agents.stage_2_initial_research import create_market_research, create_competitor_analysis, create_customer_insights, create_online_trends
from app.agents.stage_3_research_reviewer import create_research_reviewer
from app.agents.stage_4_feasibility_research import create_finance_feasibility, create_operations_feasibility, create_tech_feasibility
from app.agents.stage_5_strategy_research import create_go_to_market, create_monetization, create_risk_analysis
from app.agents.stage_6_output_production import create_landing_page_poc, create_podcaster, create_summarizer

from app.workflows.single import AgentRunEvent, AgentRunResult, FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.prompts import PromptTemplate
from llama_index.core.settings import Settings
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
    '''
    Fired when the user has a question for the AI
    '''
    input: str

class ResearchWorkflowEvent(Event):
    '''
    Fired when the user has a research query
    '''
    input: str

class StartResearchPipelineEvent(Event):
    '''
    Fired when the user has provided enough information to start the research pipeline
    '''
    input: str

class GetCritiqueEvent(Event):
    '''
    Fired when an analyst has completed their research and needs feedback
    '''
    input: str

### Initial Research Events ###
class CompetitorAnalysisCompleteEvent(Event):
    '''
    Fired when the competitor analysis is complete
    '''
    input: str

class CustomerInsightsCompleteEvent(Event):
    '''
    Fired when the customer insights are complete
    '''
    input: str

class OnlineTrendsCompleteEvent(Event):
    '''
    Fired when the online trends are complete
    '''
    input: str

class MarketResearchCompleteEvent(Event):
    '''
    Fired when the market research is complete
    '''
    input: str

class MarketResearchFeedbackEvent(Event):
    '''
    Fired when the market research critique gives feedback
    '''
    input: str

### Feasibility Research Events ###
class StartFeasibilityResearchEvent(Event):
    '''
    Fired when the user has provided enough information to start the feasibility research pipeline
    '''
    input: str

class IdeaResearchWorkflow(Workflow):
    def __init__(
        self, timeout: int = 600, chat_history: Optional[List[ChatMessage]] = None
    ):
        super().__init__(timeout=timeout)
        self.chat_history = chat_history or []

    @step()
    async def start(self, ctx: Context, ev: StartEvent) -> QnaWorkflowEvent | ResearchWorkflowEvent:
        # set streaming
        ctx.data["streaming"] = getattr(ev, "streaming", False)
        # start the workflow with researching about a topic
        ctx.data["task"] = ev.input
        ctx.data["user_input"] = ev.input

        # Decision-making process
        prompt_template = PromptTemplate(
            dedent(
                """
                ### High Level Context
                You are part of a workflow to help users do autonomous research and idea validation for their business ideas.

                ### Your Role
                You are an expert in decision-making, given the chat history and the new user request, decide whether the user request is a research query (including providing more information for an existing research query) or a question for the AI.

                Here is the chat history:
                {chat_history}

                The current user request is:
                {input}

                Decision (respond with either 'research' or 'qna'):
            """
            )
        )

        chat_history_str = "\n".join(
            [f"{msg.role}: {msg.content}" for msg in self.chat_history]
        )
        prompt = prompt_template.format(chat_history=chat_history_str, input=ev.input)

        output = await Settings.llm.acomplete(prompt)
        decision = output.text.strip().lower()

        if decision == "research":
            return ResearchWorkflowEvent(input=f"User input: {ev.input}")
        else:
            return QnaWorkflowEvent(input=f"User input: {ev.input}")

    @step()
    async def validate_problem_statement(self, ctx: Context, ev: ResearchWorkflowEvent) -> StartResearchPipelineEvent | StopEvent:
        chat_history_str = "\n".join(
            [f"{msg.role}: {msg.content}" for msg in self.chat_history]
        )
        prompt = problem_validator_prompt_instructions.format(chat_history=chat_history_str, input=ev.input)

        output = await Settings.llm.as_structured_llm(output_cls=ProblemValidatorFeedback).acomplete(prompt)
        result: ProblemValidatorFeedback = output.raw
        if result.enough_information:
            return StartResearchPipelineEvent(input=result.refined_problem_statement)
        else:
            return StopEvent(input=result.feedback)

    @step()
    async def qna(self, ctx: Context, ev: QnaWorkflowEvent) -> StopEvent:
        messages = self.chat_history + [ChatMessage(role="user", content=ev.input)]
        result = await Settings.llm.achat(messages)
        return StopEvent(result=result.content)
    
    ### Initial Research Analysts Team 1 ###
    @step()
    async def market_research(self, ctx: Context, ev: StartResearchPipelineEvent | MarketResearchCompleteEvent) -> GetCritiqueEvent:
        return GetCritiqueEvent(input=ev.input)

    @step()
    async def critique_market_research(self, ctx: Context, ev: GetCritiqueEvent) -> MarketResearchCompleteEvent | MarketResearchFeedbackEvent:
        return MarketResearchCompleteEvent(input=ev.input)


    ### Collect Initial Research Feedback ###
    @step()
    async def review_initial_research(self, ctx: Context, ev: GetCritiqueEvent) -> StartFeasibilityResearchEvent:
        print("Received event ", ev.result)

        # wait until we receive 3 events
        if (
            ctx.collect_events(
                ev,
                [CompetitorAnalysisCompleteEvent, CustomerInsightsCompleteEvent, OnlineTrendsCompleteEvent],
            )
            is None
        ):
            return None
        return StartFeasibilityResearchEvent(input=ev.input)

    async def run_agent(
        self,
        ctx: Context,
        agent: FunctionCallingAgent,
        input: str,
        streaming: bool = False,
    ) -> AgentRunResult | AsyncGenerator:
        handler = agent.run(input=input, streaming=streaming)
        # bubble all events while running the executor to the planner
        async for event in handler.stream_events():
            # Don't write the StopEvent from sub task to the stream
            if type(event) is not StopEvent:
                ctx.write_event_to_stream(event)
        return await handler

def create_idea_research_workflow(chat_history: Optional[List[ChatMessage]] = None, **kwargs):
    # Create all the necessary agents here

    # # Initial Research Team
    # market_research_agent = create_market_research_agent(chat_history=chat_history, **kwargs)
    # competitor_analysis_agent = create_competitor_analysis_agent(chat_history=chat_history, **kwargs)
    # customer_insights_agent = create_customer_insights_agent(chat_history=chat_history, **kwargs)
    # trends_research_agent = create_trends_research_agent(chat_history=chat_history, **kwargs)
    
    # # Review & Refine
    # reviewer_refiner_agent = create_reviewer_refiner_agent(chat_history=chat_history, **kwargs)
    
    # # Post-Research Team
    # risk_analysis_agent = create_risk_analysis_agent(chat_history=chat_history, **kwargs)
    # monetization_agent = create_monetization_agent(chat_history=chat_history, **kwargs)
    # gtm_strategy_agent = create_gtm_strategy_agent(chat_history=chat_history, **kwargs)
    
    # # Post-Research Review Team
    # technical_feasibility_agent = create_technical_feasibility_agent(chat_history=chat_history, **kwargs)
    # financial_feasibility_agent = create_financial_feasibility_agent(chat_history=chat_history, **kwargs)
    # operational_feasibility_agent = create_operational_feasibility_agent(chat_history=chat_history, **kwargs)
    
    # # Final Output
    # podcast_summary_agent = create_podcast_summary_agent(chat_history=chat_history, **kwargs)
    # summarizer_agent = create_summarizer_agent(chat_history=chat_history, **kwargs)
    # landing_page_design_agent = create_landing_page_design_agent(chat_history=chat_history, **kwargs)

    workflow = IdeaResearchWorkflow(timeout=3600, chat_history=chat_history)

    workflow.add_workflows(
        # problem_definition=problem_definition_agent,
        # market_research=market_research_agent,
        # competitor_analysis=competitor_analysis_agent,
        # customer_insights=customer_insights_agent,
        # trends_research=trends_research_agent,
        # reviewer_refiner=reviewer_refiner_agent,
        # risk_analysis=risk_analysis_agent,
        # monetization=monetization_agent,
        # gtm_strategy=gtm_strategy_agent,
        # technical_feasibility=technical_feasibility_agent,
        # financial_feasibility=financial_feasibility_agent,
        # operational_feasibility=operational_feasibility_agent,
        # podcast_summary=podcast_summary_agent,
        # summarizer=summarizer_agent,
        # landing_page_design=landing_page_design_agent,
    )
    return workflow

# class IdeaValidationWorkflow(Workflow):
#     def __init__(
#         self, timeout: int = 3600, chat_history: Optional[List[ChatMessage]] = None
#     ):
#         super().__init__(timeout=timeout)
#         self.chat_history = chat_history or []
#         self.research_results: Dict[str, str] = {}

#     @step()
#     async def start(self, ctx: Context, ev: StartEvent) -> IdeaValidationEvent:
#         ctx.data["streaming"] = getattr(ev, "streaming", False)
#         ctx.data["idea"] = ev.input
#         return IdeaValidationEvent(stage=IdeaValidationStage.PROBLEM_DEFINITION, input=ev.input)

#     @step()
#     async def problem_definition(
#         self, ctx: Context, ev: IdeaValidationEvent, problem_definition: FunctionCallingAgent, critic: FunctionCallingAgent
#     ) -> IdeaValidationEvent:
#         result = await self.run_agent(ctx, problem_definition, ev.input)
#         critique = await self.run_agent(ctx, critic, result.response.message.content)
        
#         if critique.response.message.content.lower().startswith("approved"):
#             return IdeaValidationEvent(stage=IdeaValidationStage.INITIAL_RESEARCH, input=result.response.message.content)
#         else:
#             return IdeaValidationEvent(stage=IdeaValidationStage.PROBLEM_DEFINITION, input=f"{ev.input}\nCritique: {critique.response.message.content}")

#     @step()
#     async def initial_research(
#         self, ctx: Context, ev: IdeaValidationEvent, 
#         market_research: FunctionCallingAgent, competitor_analysis: FunctionCallingAgent, 
#         customer_insights: FunctionCallingAgent, trends_research: FunctionCallingAgent,
#         critic: FunctionCallingAgent
#     ) -> IdeaValidationEvent:
#         research_tasks = {
#             "market_research": market_research,
#             "competitor_analysis": competitor_analysis,
#             "customer_insights": customer_insights,
#             "trends_research": trends_research,
#         }
        
#         for task, agent in research_tasks.items():
#             result = await self.run_agent(ctx, agent, ev.input)
#             critique = await self.run_agent(ctx, critic, result.response.message.content)
            
#             if critique.response.message.content.lower().startswith("approved"):
#                 self.research_results[task] = result.response.message.content
#             else:
#                 return IdeaValidationEvent(stage=IdeaValidationStage.INITIAL_RESEARCH, input=f"{ev.input}\nTask: {task}\nCritique: {critique.response.message.content}")
        
#         return IdeaValidationEvent(stage=IdeaValidationStage.REVIEW_REFINE, input=str(self.research_results))

#     @step()
#     async def review_refine(
#         self, ctx: Context, ev: IdeaValidationEvent, reviewer_refiner: FunctionCallingAgent
#     ) -> IdeaValidationEvent:
#         result = await self.run_agent(ctx, reviewer_refiner, ev.input)
#         refined_idea = result.response.message.content
        
#         if "REFINE" in refined_idea.upper():
#             return IdeaValidationEvent(stage=IdeaValidationStage.INITIAL_RESEARCH, input=refined_idea)
#         else:
#             return IdeaValidationEvent(stage=IdeaValidationStage.POST_RESEARCH, input=refined_idea)

#     @step()
#     async def post_research(
#         self, ctx: Context, ev: IdeaValidationEvent,
#         risk_analysis: FunctionCallingAgent, monetization: FunctionCallingAgent,
#         gtm_strategy: FunctionCallingAgent, critic: FunctionCallingAgent
#     ) -> IdeaValidationEvent:
#         research_tasks = {
#             "risk_analysis": risk_analysis,
#             "monetization": monetization,
#             "gtm_strategy": gtm_strategy,
#         }
        
#         for task, agent in research_tasks.items():
#             result = await self.run_agent(ctx, agent, ev.input)
#             critique = await self.run_agent(ctx, critic, result.response.message.content)
            
#             if critique.response.message.content.lower().startswith("approved"):
#                 self.research_results[task] = result.response.message.content
#             else:
#                 return IdeaValidationEvent(stage=IdeaValidationStage.POST_RESEARCH, input=f"{ev.input}\nTask: {task}\nCritique: {critique.response.message.content}")
        
#         return IdeaValidationEvent(stage=IdeaValidationStage.POST_RESEARCH_REVIEW, input=str(self.research_results))

#     @step()
#     async def post_research_review(
#         self, ctx: Context, ev: IdeaValidationEvent,
#         technical_feasibility: FunctionCallingAgent, financial_feasibility: FunctionCallingAgent,
#         operational_feasibility: FunctionCallingAgent, critic: FunctionCallingAgent
#     ) -> IdeaValidationEvent:
#         research_tasks = {
#             "technical_feasibility": technical_feasibility,
#             "financial_feasibility": financial_feasibility,
#             "operational_feasibility": operational_feasibility,
#         }
        
#         for task, agent in research_tasks.items():
#             result = await self.run_agent(ctx, agent, ev.input)
#             critique = await self.run_agent(ctx, critic, result.response.message.content)
            
#             if critique.response.message.content.lower().startswith("approved"):
#                 self.research_results[task] = result.response.message.content
#             else:
#                 return IdeaValidationEvent(stage=IdeaValidationStage.POST_RESEARCH_REVIEW, input=f"{ev.input}\nTask: {task}\nCritique: {critique.response.message.content}")
        
#         return IdeaValidationEvent(stage=IdeaValidationStage.FINAL_OUTPUT, input=str(self.research_results))

#     @step()
#     async def final_output(
#         self, ctx: Context, ev: IdeaValidationEvent,
#         podcast_summary: FunctionCallingAgent, summarizer: FunctionCallingAgent,
#         landing_page_design: FunctionCallingAgent
#     ) -> StopEvent:
#         podcast_result = await self.run_agent(ctx, podcast_summary, ev.input)
#         summary_result = await self.run_agent(ctx, summarizer, ev.input)
#         landing_page_result = await self.run_agent(ctx, landing_page_design, ev.input)
        
#         final_output = {
#             "podcast_summary": podcast_result.response.message.content,
#             "executive_summary": summary_result.response.message.content,
#             "landing_page_design": landing_page_result.response.message.content,
#         }
        
#         return StopEvent(result=final_output)

#     async def run_agent(
#         self,
#         ctx: Context,
#         agent: FunctionCallingAgent,
#         input: str,
#         streaming: bool = False,
#     ) -> AgentRunResult | AsyncGenerator:
#         handler = agent.run(input=input, streaming=streaming)
#         async for event in handler.stream_events():
#             if type(event) is not StopEvent:
#                 ctx.write_event_to_stream(event)
#         return await handler
