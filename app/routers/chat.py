"""Chat interaction endpoints with per-session conversation memory."""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse
from services.gemini_service import get_gemini_service
from services.session_store import get_session_store
from utils.risk_detection import RiskDetector
from datetime import datetime
import logging


router = APIRouter(prefix="/ai/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/interact", response_model=ChatResponse)
async def chat_interact(request: ChatRequest) -> ChatResponse:
    """Chat interaction with Gemini API, risk detection, and session memory.

    Pass the same `session_id` on every message to maintain conversation
    context.  Omit it (or use "default") for a stateless, single-turn call.

    Args:
        request: Chat request with user message and optional session_id.

    Returns:
        ChatResponse with AI response, risk assessment, and session metadata.
    """
    try:
        session_store = get_session_store()
        gemini_service = get_gemini_service()
        risk_detector = RiskDetector()

        # ── 1. Retrieve existing history for this session ──────────────
        history = session_store.get_history(request.session_id)

        # ── 2. Risk-check the incoming user message ────────────────────
        user_risk_level, _ = risk_detector.analyze(request.user_message)

        # ── 3. Generate AI response, passing full history ──────────────
        logger.info(f"Generating response for session '{request.session_id}' with {len(history)} history messages.")
        ai_response = gemini_service.generate_response(
            user_message=request.user_message,
            conversation_history=history,
            gad7_score=request.gad7_score,
            phq9_score=request.phq9_score,
        )

        # ── 4. Risk-check the AI response ──────────────────────────────
        response_risk_level, _ = risk_detector.analyze(ai_response)
        final_risk_level = risk_detector.max_risk_level(user_risk_level, response_risk_level)

        # ── 5. Persist both turns to session memory ────────────────────
        # We store the raw response to ensure subsequent turns have the full context
        session_store.append(request.session_id, role="user", content=request.user_message)
        session_store.append(request.session_id, role="model", content=ai_response)

        # ── 6. Append safety message if needed (non-destructive) ────────
        if risk_detector.should_flag_for_review(final_risk_level):
            safety_msg = risk_detector.get_safety_message(final_risk_level)
            # We only append to the response returned to the user, not the history
            ai_response = f"{ai_response}\n\n**Support Available**: {safety_msg}"
            logger.warning(f"High-risk content detected: {final_risk_level}")

        message_count = session_store.message_count(request.session_id)
        logger.info(
            f"Session '{request.session_id}': {message_count} messages | risk={final_risk_level}"
        )

        return ChatResponse(
            ai_response=ai_response,
            risk_level=final_risk_level.value,
            timestamp=datetime.utcnow(),
            flagged_for_review=risk_detector.should_flag_for_review(final_risk_level),
            session_id=request.session_id,
            message_count=message_count,
        )

    except Exception as e:
        logger.error(f"Chat interaction error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Chat processing failed")


@router.delete("/session/{session_id}", summary="Clear session memory")
async def clear_session(session_id: str) -> dict:
    """Delete all conversation history for the given session.

    Useful when starting a fresh conversation for the same user.

    Args:
        session_id: The session to clear.

    Returns:
        Confirmation dict.
    """
    store = get_session_store()
    existed = store.clear(session_id)
    return {
        "session_id": session_id,
        "cleared": existed,
        "message": f"Session '{session_id}' cleared." if existed else "Session not found.",
    }
