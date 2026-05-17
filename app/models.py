"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat interaction request."""
    user_message: str = Field(..., description="User's message", min_length=1, max_length=5000)
    session_id: str = Field(
        default="default",
        description="Session identifier for conversation memory. Use a unique ID per user/conversation.",
        min_length=1,
        max_length=128,
    )
    gad7_score: Optional[int] = Field(None, ge=0, le=21, description="GAD-7 Anxiety Score")
    phq9_score: Optional[int] = Field(None, ge=0, le=27, description="PHQ-9 Depression Score")


class ChatResponse(BaseModel):
    """Chat interaction response."""
    ai_response: str
    risk_level: str
    timestamp: datetime
    flagged_for_review: bool
    session_id: str
    message_count: int = Field(default=0, description="Total messages in this session so far")


class AudioSTTRequest(BaseModel):
    """Speech-to-text request."""
    audio_data: str = Field(..., description="Base64-encoded audio data")
    language: str = Field(default="en-GB", description="Language code")


class AudioSTTResponse(BaseModel):
    """Speech-to-text response."""
    transcription: str
    confidence: float = Field(ge=0.0, le=1.0)


class AudioTTSRequest(BaseModel):
    """Text-to-speech request."""
    text: str = Field(..., min_length=1)
    voice: str = Field(default="en-GB-Neural2-A")


class AudioTTSResponse(BaseModel):
    """Text-to-speech response."""
    audio_data: str = Field(description="Base64-encoded audio")


class GADPHQResponse(BaseModel):
    """GAD-7 and PHQ-9 scoring response."""
    gad7_score: int = Field(ge=0, le=21)
    gad7_severity: str
    phq9_score: int = Field(ge=0, le=27)
    phq9_severity: str
    clinical_summary: str
    recommended_next_steps: list[str]


class SurveyResponse(BaseModel):
    """Single survey response with question and answer."""
    question: str = Field(..., description="Survey question")
    answer: str = Field(..., description="Answer text (Not at all, Several days, More than half the days, Nearly every day)")


class ReportGenerateRequest(BaseModel):
    """Report generation request - accepts text-based survey responses."""
    survey_responses: list[SurveyResponse] | dict[str, int] = Field(..., description="Survey response data (list of Q&A or numeric dict)")


class ConversationSummaryRequest(BaseModel):
    """Request model for conversation summarization.

    Accepts a list of messages where each message is an object with `role` and `content`.
    """
    messages: list[dict] = Field(..., description="List of message objects with 'role' and 'content'")


class ConversationSummaryResponse(BaseModel):
    """Response model for conversation summarization."""
    summary: str
    message_count: int
