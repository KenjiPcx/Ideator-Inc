from textwrap import dedent
from typing import List, Tuple, Dict, Any
import torch
from pydantic import BaseModel, Field
from app.workflows.single import FunctionCallingAgent
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.tools import FunctionTool

# Input/Output Models for Transcript Writer
class TranscriptInput(BaseModel):
    cleaned_text: str = Field(description="Research text to convert into a natural podcast dialogue")

class TranscriptOutput(BaseModel):
    transcript: str = Field(description="Initial transcript with key points")
    segments: List[str] = Field(description="Major segments of the podcast")
    key_points: List[str] = Field(description="Main business insights and takeaways")
    structure: Dict[str, str] = Field(description="Podcast structure including intro, body, and conclusion")
    pacing: Dict[str, str] = Field(description="Timing guidelines for each segment")

# Input/Output Models for Dramatic Rewriter
class DramaticInput(BaseModel):
    transcript: TranscriptOutput = Field(description="Initial transcript to enhance with dramatic elements")

class SpeakerRules(BaseModel):
    style: str = Field(description="Speaking style for the character")
    characteristics: List[str] = Field(description="Key speaking characteristics")
    pacing: List[str] = Field(description="Pacing and timing guidelines")
    expressions: List[str] = Field(description="Allowed expressions and interjections", default_factory=list)
    interruptions: List[str] = Field(description="Types of interruptions allowed", default_factory=list)

class FormatRules(BaseModel):
    start_directly: bool = Field(description="Whether to start directly with content")
    return_as_tuples: bool = Field(description="Return format as speaker-text tuples")
    include_clickbait_welcome: bool = Field(description="Include engaging welcome message")
    maintain_realism: bool = Field(description="Keep conversation natural")
    use_hyphens_for_pauses: bool = Field(description="Use hyphens to indicate pauses")

class DramaticOutput(BaseModel):
    enhanced_transcript: List[List[str]] = Field(
        description="Enhanced transcript with speaker assignments",
        # Explicitly define the array items structure
        examples=[[["Alex", "Opening hook with analogy"], ["Jamie", "Excited interruption"]]]
    )
    speaker_rules: Dict[str, SpeakerRules] = Field(description="Rules for each speaker")
    format_rules: FormatRules = Field(description="Formatting guidelines")

# Input/Output Models for TTS Preparation
class TTSInput(BaseModel):
    dramatic_content: DramaticOutput = Field(description="Dramatically enhanced content to optimize for TTS")

class VoiceSettings(BaseModel):
    model: str = Field(description="TTS model to use")
    voice: str = Field(description="Voice profile name")
    description: str = Field(description="Voice characteristics description", default="")
    constraints: List[str] = Field(description="Voice generation constraints", default_factory=list)
    sampling_rate: int = Field(description="Voice sampling rate", default=24000)
    generation_params: Dict[str, float] = Field(description="Generation parameters", default_factory=dict)
    expression_markers: Dict[str, Any] = Field(description="Expression marking rules", default_factory=dict)

class AudioSettings(BaseModel):
    sample_rate: int = Field(description="Audio sample rate")
    bitrate: str = Field(description="Audio bitrate")
    format: str = Field(description="Audio format")
    parameters: List[str] = Field(description="Audio processing parameters")

class SegmentProcessing(BaseModel):
    add_pauses: bool = Field(description="Add pauses between segments")
    normalize_volume: bool = Field(description="Normalize audio volume")
    clean_transitions: bool = Field(description="Clean up speaker transitions")
    requirements: Dict[str, Any] = Field(description="Technical requirements")

class TTSOutput(BaseModel):
    tts_ready_segments: List[List[str]] = Field(
        description="Segments ready for TTS processing",
        # Explicitly define the array items structure
        examples=[[["Alex", "Text for Alex"], ["Jamie", "Text for Jamie"]]]
    )
    voice_settings: Dict[str, VoiceSettings] = Field(description="Voice settings for each speaker")
    audio_settings: AudioSettings = Field(description="Audio processing settings")
    segment_processing: SegmentProcessing = Field(description="Segment processing rules")
    fallback_models: Dict[str, List[str]] = Field(description="Backup TTS models")
def _create_transcript_writer_tool():
    def generate_transcript(
        input_data: TranscriptInput = Field(description="Input data for transcript generation")
    ) -> TranscriptOutput:
        """Generates initial podcast transcript using Llama-3.1-70B-Instruct style."""
        return TranscriptOutput(
            transcript="Initial transcript with key points",
            segments=["Market analysis", "Customer insights", "Recommendations"],
            key_points=["Business insight 1", "Market trend 2"],
            structure={
                "intro": "Clickbait-style hook",
                "body": "Main insights with analogies",
                "conclusion": "Key takeaways and call to action"
            },
            pacing={
                "intro_length": "30-45 seconds",
                "segment_length": "2-3 minutes",
                "total_target": "10-15 minutes"
            }
        )
    
    return FunctionTool.from_defaults(generate_transcript)

def _create_dramatic_rewriter_tool():
    def enhance_drama(
        input_data: DramaticInput = Field(description="Input data for dramatic enhancement")
    ) -> DramaticOutput:
        """Enhances transcript with dramatic elements using Llama-3.1-8B-Instruct style."""
        return DramaticOutput(
            enhanced_transcript=[
                ("Alex", "Opening hook with analogy"),
                ("Jamie", "Excited interruption with question")
            ],
            speaker_rules={
                "Alex": SpeakerRules(
                    style="oscar_winning_screenwriter",
                    characteristics=[
                        "No umms or hmms (TTS limitation)",
                        "Straight, clear text",
                        "Captivating teacher style"
                    ],
                    pacing=[
                        "Clear pauses after key points",
                        "Natural breathing spots"
                    ]
                ),
                "Jamie": SpeakerRules(
                    style="curious_learner",
                    expressions=[
                        "umm", "hmm", "[sigh]", "[laughs]",
                        "[gasps]", "[clears throat]"
                    ],
                    interruptions=[
                        "Wild but relevant tangents",
                        "Super excited reactions"
                    ],
                    pacing=[
                        "Quick interjections",
                        "Natural hesitations"
                    ]
                )
            },
            format_rules=FormatRules(
                start_directly=True,
                return_as_tuples=True,
                include_clickbait_welcome=True,
                maintain_realism=True,
                use_hyphens_for_pauses=True
            )
        )
    
    return FunctionTool.from_defaults(enhance_drama)

def _create_tts_preparation_tool():
    def prepare_for_tts(
        input_data: TTSInput = Field(description="Input data for TTS preparation")
    ) -> TTSOutput:
        """Optimizes content for TTS models with specific voice profiles."""
        return TTSOutput(
            tts_ready_segments=[
                ("Alex", "<confident>Business insight with clear explanation<pause>"),
                ("Jamie", "<curious>Engaging follow-up question<emphasis>")
            ],
            voice_settings={
                "Alex": VoiceSettings(
                    model="parler-tts/parler-tts-mini-v1",
                    voice="Laura",
                    description="Expressive and dramatic delivery",
                    constraints=["No speech artifacts", "Clean pronunciation"],
                    sampling_rate=24000
                ),
                "Jamie": VoiceSettings(
                    model="bark/suno",
                    voice_preset="v2/en_speaker_6",
                    generation_params={"temperature": 0.9, "semantic_temperature": 0.8},
                    sampling_rate=24000
                )
            },
            audio_settings=AudioSettings(
                sample_rate=24000,
                bitrate="192k",
                format="mp3",
                parameters=["-q:a", "0"]
            ),
            segment_processing=SegmentProcessing(
                add_pauses=True,
                normalize_volume=True,
                clean_transitions=True,
                requirements={
                    "transformers_version": "4.43.3",
                    "device": "cuda" if torch.cuda.is_available() else "cpu"
                }
            ),
            fallback_models={
                "primary_alternatives": [
                    "myshell-ai/MeloTTS-English",
                    "WhisperSpeech/WhisperSpeech"
                ],
                "experimental": [
                    "coqui/xtts",
                    "fishaudio/fish-speech-1.4"
                ]
            }
        )
    
    return FunctionTool.from_defaults(prepare_for_tts)

def _get_podcaster_params() -> Tuple[List[FunctionTool], str, str]:
    tools = [
        _create_transcript_writer_tool(),
        _create_dramatic_rewriter_tool(),
        _create_tts_preparation_tool()
    ]
    
    prompt_instructions = dedent(
        """
        You are an international oscar winning screenwriter who has worked with multiple award-winning podcasters.
        Your job is to transform business research into engaging podcast content following a specific 3-step process...
        
        1. Create an engaging podcast transcript by calling the generate_transcript tool
        2. Call the dramatic_writer tool with the transcript to enhance it with dramatic elements
        3. Call the prepare_for_tts tool with the dramatic content to optimize it for TTS models
        4. Return the audio file path
        
        """
    )

    
    description = "Oscar-winning screenwriter creating engaging business podcasts with optimized TTS delivery"
    
    return tools, prompt_instructions, description

def create_podcaster(chat_history: List[ChatMessage]):
    tools, prompt_instructions, description = _get_podcaster_params()

    return FunctionCallingAgent(
        name="podcaster",
        tools=tools,
        description=description,
        system_prompt=dedent(prompt_instructions),
        chat_history=chat_history,
    )