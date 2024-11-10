from textwrap import dedent
from typing import List, Optional, Dict, Any
from app.engine.tools.podcast_generator import ElevenLabsGenerator
from llama_index.core.workflow import Context, Event, StartEvent, StopEvent, Workflow, step
from llama_index.core.chat_engine.types import ChatMessage
from app.workflows.single import AgentRunEvent, AgentRunResult, FunctionCallingAgent
from app.settings import Settings
from app.utils.json_validator import JsonValidationHelper
from .models import PodcastOutline, PodcastScript, ScriptCritique
from pathlib import Path
import json
import logging
from .outline_writer import create_outline_writer
from .script_writer import create_script_writer
from .script_critic import create_script_critic

logger = logging.getLogger(__name__)

class GenerateOutlineEvent(Event):
    pass

class WriteScriptEvent(Event):
    outline: PodcastOutline

class ReviseScriptEvent(Event):
    critique: ScriptCritique

class CritiqueScriptEvent(Event):
    script: PodcastScript

class GenerateAudioEvent(Event):
    script: PodcastScript

class PodcastWorkflow(Workflow):
    def __init__(self, 
                 session_id: str,
                 chat_history: Optional[List[ChatMessage]] = None,
                 timeout: int = 1800,
                 max_iterations: int = 3):
        super().__init__(timeout=timeout)
        self.chat_history = chat_history or []
        self.max_iterations = max_iterations
        self.session_id = session_id
        
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
                name="Podcast Workflow",
                msg=f"Reading research from {data_dir}, found {len(research_files)} files which are {[research_file.name for research_file in research_files]}"
            )
        )
        
        if len(research_files) == 0:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Podcast Workflow",
                    msg="No research files found, skipping outline generation"
                )
            )
            return StopEvent()
        
        return GenerateOutlineEvent()

    @step()
    async def generate_outline(self, ctx: Context, ev: GenerateOutlineEvent, outline_writer: FunctionCallingAgent) -> WriteScriptEvent:
        result = await self.run_agent(ctx, outline_writer, ctx.data["research"])
        validator = JsonValidationHelper(PodcastOutline, Settings.llm)
        outline = await validator.validate_and_fix(result.response.message.content)     
        ctx.write_event_to_stream(
            AgentRunEvent(
                name=outline_writer.name,
                msg=f"Generated podcast outline:\n{outline.model_dump_json(indent=2)}"
            )
        )
        ctx.data["podcast_title"] = outline.title
        
        return WriteScriptEvent(outline=outline)

    @step()
    async def generate_script(self, ctx: Context, ev: WriteScriptEvent | ReviseScriptEvent, script_writer: FunctionCallingAgent) -> CritiqueScriptEvent:
        if isinstance(ev, WriteScriptEvent):
            prompt = dedent(f"""
                Here is the podcast outline, generate a script for it:
                {ev.outline.model_dump_json(indent=2)}
            """)
        else:
            prompt = dedent(f"""
                Please revise the script based on the following critique:
                {ev.critique.model_dump_json(indent=2)}
            """)
        result = await self.run_agent(ctx, script_writer, prompt)
        validator = JsonValidationHelper(PodcastScript, Settings.llm)
        script = await validator.validate_and_fix(result.response.message.content)
        ctx.write_event_to_stream(
            AgentRunEvent(
                name=script_writer.name,
                msg=f"Generated podcast script:\n{script.model_dump_json(indent=2)}"
            )
        )
        
        if ctx.data.get("critique_iteration", 0) >= self.max_iterations:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Podcast Workflow",
                    msg="Reached maximum critique iterations, passing to podcast generator to generate audio"
                )
            )
            return GenerateAudioEvent(script=script)
        
        ctx.data["critique_iteration"] = ctx.data.get("critique_iteration", 0) + 1
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Podcast Workflow",
                msg=f"Asking for critique of the script, iteration {ctx.data['critique_iteration']} of {self.max_iterations}"
            )
        )
        return CritiqueScriptEvent(script=script)

    @step()
    async def critique_script(self, ctx: Context, ev: CritiqueScriptEvent, script_critic: FunctionCallingAgent) -> ReviseScriptEvent | GenerateAudioEvent:
        prompt = dedent(f"""
            Here is the podcast script, critique it:
            {ev.script.model_dump_json(indent=2)}
        """)
        result = await self.run_agent(ctx, script_critic, prompt)
        validator = JsonValidationHelper(ScriptCritique, Settings.llm)
        critique = await validator.validate_and_fix(result.response.message.content)
        
        if critique.satisfied:
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name=script_critic.name,
                    msg="Script critique satisfied, passing to podcast generator to generate audio"
                )
            )
            return GenerateAudioEvent(script=ev.script)
            
        ctx.write_event_to_stream(
            AgentRunEvent(
                name=script_critic.name,
                msg=f"Script critique not satisfied, asking for revision"
            )
        )
        return ReviseScriptEvent(critique=critique)

    @step()
    async def generate_audio(self, ctx: Context, ev: GenerateAudioEvent) -> StopEvent:
        try:
            segments = [(segment.speaker.strip(), segment.text.strip().strip('"')) for segment in ev.script.segments]
            elevenlabs_generator = ElevenLabsGenerator()
            
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Podcast Generator",
                    msg=f"Generating podcast with title: {ctx.data['podcast_title']}"
                )
            )
            
            output_path = elevenlabs_generator.generate_podcast(segments, filename=ctx.data["podcast_title"], session_id=self.session_id)
            
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Podcast Generator",
                    msg=f"Generated podcast at: {output_path}"
                )
            )
            
            return StopEvent(result=f"Podcast generated at: {output_path}")

        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            raise
        
    async def run_agent(self, ctx: Context, agent: FunctionCallingAgent, input: str) -> AgentRunResult:
        try:
            handler = agent.run(input=input, streaming=False)
            async for event in handler.stream_events():
                if type(event) is not StopEvent:
                    if isinstance(event, AgentRunEvent):
                        event.workflow_id = "Podcaster"
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

def create_podcast_workflow(session_id: str, chat_history: List[ChatMessage], timeout: int = 1800):
    workflow = PodcastWorkflow(
        session_id=session_id,
        chat_history=chat_history,
        timeout=timeout
    )
    
    outline_writer = create_outline_writer(chat_history)
    script_writer = create_script_writer(chat_history)
    script_critic = create_script_critic(chat_history)
    
    workflow.add_workflows(
        outline_writer=outline_writer,
        script_writer=script_writer,
        script_critic=script_critic
    )
    
    return workflow
