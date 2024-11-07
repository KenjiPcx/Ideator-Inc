import requests
from pathlib import Path
from typing import List, Tuple, Optional
import logging
from pydantic import BaseModel, Field
import os
import re
from llama_index.core.tools import FunctionTool

logger = logging.getLogger(__name__)

OUTPUT_DIR = "output/tools"

class VoiceSettings(BaseModel):
    stability: float = Field(default=0.5, ge=0, le=1)
    similarity_boost: float = Field(default=0.75, ge=0, le=1) 
    style: float = Field(default=0.5, ge=0, le=1)
    use_speaker_boost: bool = Field(default=True)

class TTSRequest(BaseModel):
    text: str
    model_id: str = "eleven_multilingual_v2"
    voice_settings: VoiceSettings = Field(default_factory=VoiceSettings)

class ElevenLabsGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ElevenLabs API key not provided")
        
        self.output_dir = Path(OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Default voice IDs for different roles
        self.voice_mapping = {
            "alex": "21m00Tcm4TlvDq8ikWAM",  # Rachel
            "jamie": "AZnzlk1XvdvUeBnXmlld",  # Domi
            "default": "21m00Tcm4TlvDq8ikWAM"  # Rachel
        }
        
    def _get_voice_id(self, speaker: str) -> str:
        """Get voice ID for speaker role"""
        return self.voice_mapping.get(speaker.lower(), self.voice_mapping["default"])

    def generate_audio_segment(self, text: str, speaker: str) -> bytes:
        """Generate audio for a single segment"""
        voice_id = self._get_voice_id(speaker)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        request = TTSRequest(text=text)
        
        try:
            response = requests.post(
                url, 
                headers=headers,
                json=request.model_dump()
            )
            response.raise_for_status()
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to generate audio for text: {text[:50]}...")
            logger.exception(e)
            raise

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by:
        1. Converting to lowercase
        2. Replacing spaces and special chars with underscores
        3. Ensuring .mp3 extension
        """
        # Remove or replace special characters
        clean_name = re.sub(r'[^\w\s-]', '', filename)
        # Replace spaces with underscores
        clean_name = re.sub(r'[-\s]+', '_', clean_name).strip('-_')
        # Convert to lowercase
        clean_name = clean_name.lower()
        # Ensure .mp3 extension
        if not clean_name.endswith('.mp3'):
            clean_name = f"{clean_name}.mp3"
        return clean_name

    def generate_podcast(self, segments: List[Tuple[str, str]], filename: str, session_id: str) -> str:
        """Generate podcast audio from segments"""
        try:
            # Sanitize the filename
            clean_filename = self._sanitize_filename(filename)
            os.makedirs(self.output_dir / session_id, exist_ok=True)
            output_path = str(self.output_dir / session_id / clean_filename)
            
            # Generate and concatenate audio segments
            from pydub import AudioSegment
            final_audio = None
            
            for speaker, text in segments:
                # Generate audio bytes
                audio_bytes = self.generate_audio_segment(text, speaker)
                
                # Save to temporary file
                temp_path = str(self.output_dir / session_id / f"temp_{speaker}.mp3")
                with open(temp_path, "wb") as f:
                    f.write(audio_bytes)
                
                # Load audio segment
                audio_segment = AudioSegment.from_mp3(temp_path)
                
                # Add to final audio
                if final_audio is None:
                    final_audio = audio_segment
                else:
                    final_audio += audio_segment
                
                # Clean up temp file
                Path(temp_path).unlink()
            
            # Export final audio
            final_audio.export(output_path, format="mp3")
            logger.info(f"Podcast generated at: {output_path}")
            
            file_url = f"{os.getenv('FILESERVER_URL_PREFIX')}/{output_path}"
            return file_url
            
        except Exception as e:
            logger.error("Failed to generate podcast audio")
            logger.exception(e)
            raise 

def get_tools(**kwargs):
    return [FunctionTool.from_defaults(
        ElevenLabsGenerator(**kwargs).generate_podcast,
        name="generate_podcast",
        description="Generate a podcast from a list of text segments with different speakers"
    )]