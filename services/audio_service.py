"""Audio processing for speech-to-text and text-to-speech."""

import base64
import os
from typing import Optional


class AudioService:
    """Handles STT and TTS operations using Gemini API.
    
    Uses gemini-2.5-flash for STT and gemini-2.5-flash-preview-tts for TTS.
    """

    def __init__(self):
        """Initialize audio service."""
        self.supported_languages = ["en-GB", "en-US", "fr-FR"]

    async def speech_to_text(self, audio_bytes: bytes, language: str = "en-GB", mime_type: str = "audio/webm") -> tuple[str, float]:
        """Convert speech to text.
        
        Args:
            audio_bytes: Raw audio bytes.
            language: Language code (e.g., 'en-GB').
            mime_type: MIME type of the audio (e.g., 'audio/webm', 'audio/wav').
            
        Returns:
            Tuple of (transcription, confidence_score).
        """
        if language not in self.supported_languages:
            raise ValueError(f"Language {language} not supported")

        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                        types.Part.from_text(text="Transcribe this audio exactly. Do not add any conversational text or formatting.")
                    ]
                )
            ]

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents
            )
            
            transcription = response.text.strip() if response.text else ""
            confidence = 0.95  # Gemini does not natively return a confidence score
            
            return transcription, confidence
        
        except Exception as e:
            raise RuntimeError(f"STT processing failed: {str(e)}")

    async def text_to_speech(self, text: str, voice: str = "en-GB-Neural2-A") -> str:
        """Convert text to speech.
        
        Args:
            text: Text to synthesize.
            voice: Google Cloud voice ID.
            
        Returns:
            Base64-encoded audio data.
        """
        if not text:
            raise ValueError("Invalid text length for TTS")

        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

            # Map voice ID to Gemini native voices
            voice_name = "Aoede"
            if voice == "en-GB-Neural2-A": voice_name = "Aoede"
            elif voice == "en-GB-Neural2-B": voice_name = "Puck"
            elif voice == "en-GB-Neural2-C": voice_name = "Kore"
            elif voice == "en-GB-Neural2-D": voice_name = "Charon"

            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name
                            )
                        )
                    )
                )
            )
            
            if not response.candidates or not response.candidates[0].content.parts:
                raise RuntimeError("No audio data returned by Gemini.")
            
            import struct
            
            audio_bytes = response.candidates[0].content.parts[0].inline_data.data
            
            # Gemini returns raw PCM 16-bit 24kHz mono audio.
            # We must wrap it in a WAV header to make it a playable standard format.
            def create_wav_header(data_size, sample_rate=24000, num_channels=1, bits_per_sample=16):
                header = b"RIFF"
                header += struct.pack("<L", 36 + data_size)
                header += b"WAVEfmt "
                header += struct.pack("<L", 16)
                header += struct.pack("<H", 1)
                header += struct.pack("<H", num_channels)
                header += struct.pack("<L", sample_rate)
                header += struct.pack("<L", sample_rate * num_channels * bits_per_sample // 8)
                header += struct.pack("<H", num_channels * bits_per_sample // 8)
                header += struct.pack("<H", bits_per_sample)
                header += b"data"
                header += struct.pack("<L", data_size)
                return header

            wav_data = create_wav_header(len(audio_bytes)) + audio_bytes
            audio_b64 = base64.b64encode(wav_data).decode('utf-8')
            
            return audio_b64
        
        except Exception as e:
            raise RuntimeError(f"TTS processing failed: {str(e)}")

    @staticmethod
    def validate_audio(audio_data: str, max_size_mb: int = 10) -> bool:
        """Validate audio data.
        
        Args:
            audio_data: Base64-encoded audio.
            max_size_mb: Maximum allowed size in MB.
            
        Returns:
            True if audio is valid.
        """
        try:
            decoded = base64.b64decode(audio_data, validate=True)
            if not decoded:
                return False

            size_mb = len(decoded) / (1024 * 1024)
            return size_mb <= max_size_mb
        except Exception:
            return False


# Singleton instance
_audio_service = None


def get_audio_service() -> AudioService:
    """Get or create audio service singleton."""
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioService()
    return _audio_service
