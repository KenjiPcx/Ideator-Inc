from textwrap import dedent
from typing import List, Optional, Dict, Any
from llama_index.core.workflow import Context, Event, StartEvent, StopEvent, Workflow, step
from llama_index.core.chat_engine.types import ChatMessage
from app.workflows.single import AgentRunEvent, AgentRunResult, FunctionCallingAgent
from app.settings import Settings
from .models import PodcastScript, ScriptCritique
from .elevenlabs_generator import ElevenLabsGenerator
from pathlib import Path
import json
import logging
from .outline_writer import create_outline_writer
from .script_writer import create_script_writer
from .script_critic import create_script_critic

logger = logging.getLogger(__name__)

class GenerateOutlineEvent(Event):
    research: Dict[str, Any]

class WriteScriptEvent(Event):
    outline: Dict[str, Any]

class CritiqueScriptEvent(Event):
    script: PodcastScript
    iteration: int = 0

class ReviseScriptEvent(Event):
    script: PodcastScript
    critique: ScriptCritique

class GenerateAudioEvent(Event):
    script: PodcastScript

class PodcastWorkflow(Workflow):
    def __init__(self, 
                 chat_history: Optional[List[ChatMessage]] = None,
                 timeout: int = 360,
                 max_iterations: int = 3):
        super().__init__(timeout=timeout)
        self.chat_history = chat_history or []
        self.tts_generator = ElevenLabsGenerator()
        self.output_dir = Path("./resources")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_iterations = max_iterations

    @step()
    async def start(self, ctx: Context, ev: StartEvent) -> GenerateOutlineEvent:
        ctx.data["research"] = ev.input
        return GenerateOutlineEvent(research=ev.input)

    @step()
    async def generate_outline(self, ctx: Context, ev: GenerateOutlineEvent, outline_writer: FunctionCallingAgent) -> WriteScriptEvent:
        result = await outline_writer.acomplete(
            json.dumps(ev.research, indent=2)
        )
        outline = result.json()
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name=outline_writer.name,
                msg=f"Generated podcast outline with {len(outline['segments'])} segments"
            )
        )
        
        return WriteScriptEvent(outline=outline)

    @step()
    async def generate_script(self, ctx: Context, ev: WriteScriptEvent) -> CritiqueScriptEvent:
        script_writer = create_script_writer(self.chat_history)
        result = await script_writer.acomplete(
            json.dumps(ev.outline, indent=2)
        )
        script = PodcastScript.model_validate(result.json())
        
        return CritiqueScriptEvent(script=script, iteration=0)

    @step()
    async def critique_script(self, ctx: Context, ev: CritiqueScriptEvent) -> WriteScriptEvent | GenerateAudioEvent:
        if ev.iteration >= self.max_iterations:
            return GenerateAudioEvent(script=ev.script)
            
        script_critic = create_script_critic(self.chat_history)
        result = await script_critic.acomplete(
            json.dumps(ev.script.model_dump(), indent=2)
        )
        critique = ScriptCritique.model_validate(result.json())
        
        ctx.write_event_to_stream(
            AgentRunEvent(
                name=script_critic.name,
                msg=f"Critique #{ev.iteration + 1}: Rating {critique.overall_rating}/10"
            )
        )
        
        if critique.satisfied:
            return GenerateAudioEvent(script=ev.script)
            
        return ReviseScriptEvent(script=ev.script, critique=critique)

    @step()
    async def generate_audio(self, ctx: Context, ev: GenerateAudioEvent) -> StopEvent:
        try:
            segments = [(s.speaker, s.text) for s in ev.script.segments]
            output_path = self.tts_generator.generate_podcast(segments)
            
            metadata = {
                **ev.script.model_dump(),
                "audio_path": output_path
            }
            
            metadata_path = self.output_dir / "podcast_metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            return StopEvent(result=metadata)
            
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            raise
        
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

def create_podcast_workflow(chat_history: List[ChatMessage], **kwargs):
    workflow = PodcastWorkflow(
        chat_history=chat_history,
        timeout=600
    )
    
    outline_writer = create_outline_writer(chat_history)
    script_writer = create_script_writer(chat_history)
    script_critic = create_script_critic(chat_history)
    
    workflow.add_workflows(
        outline_writer,
        script_writer,
        script_critic
    )
    
    return workflow
