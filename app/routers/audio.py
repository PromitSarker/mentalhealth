"""Audio processing endpoints for STT and TTS."""

from fastapi import APIRouter, HTTPException, Response, UploadFile, File, Form
from app.models import AudioSTTResponse, AudioTTSRequest, AudioTTSResponse
from services.audio_service import get_audio_service
import logging
import base64


router = APIRouter(prefix="/ai/audio", tags=["audio"])
logger = logging.getLogger(__name__)


@router.post("/stt", response_model=AudioSTTResponse)
async def speech_to_text(
    file: UploadFile = File(..., description="Audio file to transcribe (webm, wav, mp3, ogg, etc.)"),
    language: str = Form(default="en-GB", description="Language code e.g. en-GB, en-US")
) -> AudioSTTResponse:
    """Convert speech to text for voice interaction.
    
    Accepts a direct audio file upload (multipart/form-data).
    Supports multiple languages including UK English (en-GB).
    
    Returns:
        AudioSTTResponse with transcription and confidence score.
    """
    try:
        audio_service = get_audio_service()
        
        audio_bytes = await file.read()
        if not audio_bytes:
            raise ValueError("Uploaded file is empty")
        
        # Detect mime type from upload, fallback to webm
        mime_type = file.content_type or "audio/webm"
        
        transcription, confidence = await audio_service.speech_to_text(
            audio_bytes,
            language,
            mime_type=mime_type
        )
        
        logger.info(f"STT processed: confidence={confidence:.2%}")
        
        return AudioSTTResponse(
            transcription=transcription,
            confidence=confidence,
        )
    
    except ValueError as e:
        logger.error(f"Invalid audio: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"STT processing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Speech-to-text processing failed")


@router.post("/tts")
async def text_to_speech(request: AudioTTSRequest):
    """Convert text to speech and return a playable WAV audio file directly.
    
    Args:
        request: TTS request with text and voice selection.
        
    Returns:
        Raw WAV audio/wav response (not JSON).
    """
    try:
        audio_service = get_audio_service()
        
        audio_b64 = await audio_service.text_to_speech(
            request.text,
            request.voice
        )
        
        audio_bytes = base64.b64decode(audio_b64)
        logger.info("TTS processed")
        
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={"Content-Disposition": 'attachment; filename="tts_output.wav"'}
        )
    
    except Exception as e:
        logger.error(f"TTS processing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Text-to-speech processing failed")


@router.get("/tts/download")
async def text_to_speech_download(text: str, voice: str = "en-GB-Neural2-A"):
    """Convert text to speech and return a playable/downloadable audio file.
    
    This endpoint returns the raw WAV audio instead of a JSON wrapper.
    """
    try:
        audio_service = get_audio_service()
        audio_b64 = await audio_service.text_to_speech(text, voice)
        
        # Decode the base64 back into raw bytes to send directly
        audio_bytes = base64.b64decode(audio_b64)
        
        return Response(
            content=audio_bytes, 
            media_type="audio/wav",
            headers={"Content-Disposition": f'attachment; filename="tts_output.wav"'}
        )
    except Exception as e:
        logger.error(f"TTS download error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Text-to-speech processing failed")


@router.get("/voices")
async def list_voices() -> dict:
    """List available voices for TTS.
    
    Returns:
        Dictionary with supported voices grouped by language.
    """
    voices = {
        "en-GB": [
            {"id": "en-GB-Neural2-A", "name": "Amy (Female)"},
            {"id": "en-GB-Neural2-B", "name": "Brian (Male)"},
            {"id": "en-GB-Neural2-C", "name": "Emma (Female)"},
            {"id": "en-GB-Neural2-D", "name": "Oliver (Male)"},
        ],
    }
    return voices
