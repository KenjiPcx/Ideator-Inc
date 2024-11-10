from textwrap import dedent
from typing import List, Optional
from pathlib import Path
from app.agents.stage_6_output_production.executive_summarizer.analyzer import create_analyzer
from llama_index.core.workflow import Context, Event, StartEvent, StopEvent, Workflow, step
from llama_index.core.chat_engine.types import ChatMessage
from app.workflows.single import AgentRunEvent, AgentRunResult, FunctionCallingAgent
from app.settings import Settings
from app.utils.json_validator import JsonValidationHelper
from .models import ExecutiveSummaryOutline, ExecutiveCritique
import logging
from .outline_writer import create_outline_writer
from app.agents.example.analyst import create_analyst
from app.agents.example.reporter import create_reporter
from .critic import create_critic

logger = logging.getLogger(__name__)

class GenerateOutlineEvent(Event):
    pass

class AnalyzeContentEvent(Event):
    analysis: str

class CritiqueAnalysisEvent(Event):
    analysis: str

class GenerateReportEvent(Event):
    analysis: str

class ExecutiveSummaryWorkflow(Workflow):
    def __init__(self, 
                 session_id: str,
                 chat_history: Optional[List[ChatMessage]] = None,
                 email: Optional[str] = None,
                 timeout: int = 360,
                 max_iterations: int = 3):
        super().__init__(timeout=timeout)
        self.chat_history = chat_history or []
        self.session_id = session_id
        self.email = email
        self.max_iterations = max_iterations
        
    @step()
    async def start(self, ctx: Context, ev: StartEvent) -> GenerateOutlineEvent:
        ctx.data["task"] = ev.input
        
        # Read all research files from data/<session_id> directory
        current_file = Path(__file__)
        data_dir = current_file.parent.parent.parent.parent.parent / "data" / self.session_id
        research_files = list(data_dir.glob("**/*"))
        
        research_content = []
        for file in research_files:
            if file.is_file():
                with open(file, "r") as f:
                    content = f.read()
                    research_content.append(f"=== {file.name} ===\n\n{content}\n\n")
        
        research = dedent("\n".join(research_content))
        ctx.data["research"] = research
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Executive Summary Workflow",
                msg=f"Reading research from {data_dir}, found {len(research_files)} files"
            )
        )
        
        if len(research_files) == 0:
            return StopEvent(result="No research files found")
        
        return GenerateOutlineEvent()

    @step()
    async def generate_outline(self, ctx: Context, ev: GenerateOutlineEvent, outline_writer: FunctionCallingAgent) -> AnalyzeContentEvent:
        prompt = dedent(f"""
            Generate an executive summary outline based on the following research done by 4 other junior analysts:
            {ctx.data["research"]}
        """)
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name=outline_writer.name,
                msg=f"Generating executive summary outline",
            )
        )
        
        result = await self.run_agent(ctx, outline_writer, prompt)
        validator = JsonValidationHelper(ExecutiveSummaryOutline, Settings.llm)
        outline = await validator.validate_and_fix(result.response.message.content)
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name=outline_writer.name,
                msg=f"Generated executive summary outline:\n{outline.model_dump_json(indent=2)}\nPassing to analyzer"
            )
        )
        
        return AnalyzeContentEvent(analysis=result.response.message.content)

    @step()
    async def analyze(
        self, ctx: Context, ev: AnalyzeContentEvent, analyzer: FunctionCallingAgent
    ) -> CritiqueAnalysisEvent | GenerateReportEvent:
        if ctx.data.get("critic_iteration", 0) == 0:
            prompt = dedent(f"""
                Here is the executive summary outline and the research data to analyze:
                
                Outline:
                {ev.analysis}
                
                Research:
                {ctx.data["research"]}
                
                Please analyze this data and provide a comprehensive executive summary analysis.
            """)
        else:
            prompt = dedent(f"""
                The critic provided this feedback on your previous analysis: {ev.analysis}
                
                Please refine the analysis based on this feedback.
            """)
            
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Executive analyzer",
                msg=f"Analyzing research data for executive summary",
            )
        )
        result = await self.run_agent(ctx, analyzer, prompt)
        ctx.data["analysis_result"] = result.response.message.content
        
        # If we have reached the max number of critic iterations, return the final analysis to the reporter
        if ctx.data.get("critic_iteration", 0) >= self.max_iterations:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Executive analyzer",
                    msg=f"Reached max critic iterations, returning final analysis to reporter",
                )
            )
            return GenerateReportEvent(analysis=ctx.data["analysis_result"])
        
        # Otherwise, return the analysis to the critic
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Executive analyzer",
                msg=f"Returning analysis to critic for feedback",
            )
        )
        ctx.data["critic_iteration"] = ctx.data.get("critic_iteration", 0) + 1
        return CritiqueAnalysisEvent(analysis=ctx.data["analysis_result"])

    @step()
    async def critique(
        self, ctx: Context, ev: CritiqueAnalysisEvent, critic: FunctionCallingAgent
    ) -> AnalyzeContentEvent | GenerateReportEvent:
        result = await self.run_agent(
            ctx, critic,
            f"""Please critique this executive summary analysis and provide actionable feedback: {ev.analysis}"""
        )
        
        parser = JsonValidationHelper(ExecutiveCritique, Settings.llm)
        parsed_response = await parser.validate_and_fix(result.response.message.content)
        
        if parsed_response and parsed_response.satisfied:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Executive critic",
                    msg=f"Critique satisfied, returning analysis to reporter",
                )
            )
            return GenerateReportEvent(analysis=ctx.data["analysis_result"])
            
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Executive critic",
                msg=f"Critique not satisfied, returning analysis to analyzer for refinement",
            )
        )
        return AnalyzeContentEvent(analysis=result.response.message.content)

    @step()
    async def generate_report(self, ctx: Context, ev: GenerateReportEvent, reporter: FunctionCallingAgent) -> StopEvent:
        prompt = dedent(f"""
            Generate a comprehensive executive summary report based on this analysis:
            {ev.analysis}
        """)
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Executive reporter",
                msg=f"Generating executive summary report",
            )
        )
        
        result = await self.run_agent(ctx, reporter, prompt)

        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Executive reporter",
                msg=f"Generated executive summary report:\n{result.response.message.content}",
            )
        )
        
        return StopEvent(result=result.response.message.content)

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

def create_executive_summary_workflow(session_id: str, chat_history: List[ChatMessage], email: Optional[str] = None):
    workflow = ExecutiveSummaryWorkflow(
        session_id=session_id,
        chat_history=chat_history,
        email=email,
        timeout=1000,
        max_iterations=3
    )
    
    outline_writer = create_outline_writer(chat_history)
    analyzer = create_analyzer(chat_history, session_id)
    critic = create_critic(chat_history)
    reporter = create_reporter(chat_history, session_id, email)
    
    workflow.add_workflows(
        outline_writer=outline_writer,
        analyzer=analyzer,
        reporter=reporter,
        critic=critic
    )
    
    return workflow
