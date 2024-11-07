import requests
from pathlib import Path
from typing import List, Tuple, Optional
import logging
from pydantic import BaseModel, Field
import os

logger = logging.getLogger(__name__)

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
        
        self.output_dir = Path("./resources")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Default voice IDs for different roles
        self.voice_mapping = {
            "host": "21m00Tcm4TlvDq8ikWAM",  # Rachel
            "guest": "AZnzlk1XvdvUeBnXmlld",  # Domi
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

    def generate_podcast(self, segments: List[Tuple[str, str]], output_path: Optional[str] = None) -> str:
        """Generate podcast audio from segments"""
        try:
            if output_path is None:
                output_path = str(self.output_dir / "podcast.mp3")
            
            # Generate and concatenate audio segments
            from pydub import AudioSegment
            final_audio = None
            
            for speaker, text in segments:
                # Generate audio bytes
                audio_bytes = self.generate_audio_segment(text, speaker)
                
                # Save to temporary file
                temp_path = str(self.output_dir / f"temp_{speaker}.mp3")
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
            
            return output_path
            
        except Exception as e:
            logger.error("Failed to generate podcast audio")
            logger.exception(e)
            raise 