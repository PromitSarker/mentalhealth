"""Report generation endpoints for clinical assessments."""

from fastapi import APIRouter, HTTPException
from app.models import ReportGenerateRequest, GADPHQResponse, SurveyResponse
from services.scoring_service import ScoringService
import logging


router = APIRouter(prefix="/ai", tags=["reports"])
logger = logging.getLogger(__name__)


def convert_text_to_numeric(survey_responses: list[SurveyResponse]) -> dict:
    """Convert text-based survey responses to numeric scores (0-3).
    
    Maps:
    - "Not at all" → 0
    - "Several days" → 1
    - "More than half the days" → 2
    - "Nearly every day" → 3
    """
    answer_map = {
        "not at all": 0,
        "several days": 1,
        "more than half the days": 2,
        "nearly every day": 3,
    }
    
    numeric_responses = {}
    
    if len(survey_responses) != 16:
        raise ValueError("Expected 16 survey responses: 7 GAD-7 items and 9 PHQ-9 items")

    for idx, response in enumerate(survey_responses):
        answer_lower = response.answer.strip().lower()
        score = answer_map.get(answer_lower)
        
        if score is None:
            raise ValueError(f"Invalid answer '{response.answer}' for question '{response.question}'")
        
        # GAD-7: questions 0-6, PHQ-9: questions 7-15 (16 total)
        if idx < 7:
            numeric_responses[f"gad7_{idx + 1}"] = score
        elif idx < 16:
            numeric_responses[f"phq9_{idx - 6}"] = score
    
    return numeric_responses


@router.post("/report/generate", response_model=GADPHQResponse)
async def generate_report(request: ReportGenerateRequest) -> GADPHQResponse:
    """Generate clinical report with GAD-7 and PHQ-9 scoring.
    
    Accepts survey data in two formats:
    1. Text-based: list of {question, answer} with text answers
    2. Numeric: dict with keys gad7_1-7, phq9_1-9 with scores 0-3
    
    Args:
        request: Report request with survey responses.
        
    Returns:
        GADPHQResponse with scores, severity, and recommendations.
    """
    try:
        # Prepare combined responses for AI scoring
        if isinstance(request.survey_responses, list):
            # Convert list of SurveyResponse objects to a dictionary
            # The ScoringService will handle mapping questions to standard keys
            responses = {r.question: r.answer for r in request.survey_responses}
        else:
            # Already in dictionary format
            responses = request.survey_responses
        
        scoring_service = ScoringService()
        
        # Use AI-powered scoring to calculate scores and generate report
        ai_result = scoring_service.score_and_analyse(responses)
        
        logger.info(f"Report generated: gad7={ai_result['gad7_score']}, phq9={ai_result['phq9_score']}")
        
        return GADPHQResponse(
            gad7_score=ai_result["gad7_score"],
            gad7_severity=ai_result["gad7_severity"],
            phq9_score=ai_result["phq9_score"],
            phq9_severity=ai_result["phq9_severity"],
            clinical_summary=ai_result["clinical_summary"],
            recommended_next_steps=ai_result["recommended_next_steps"],
        )
    
    except ValueError as e:
        logger.error(f"Scoring error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Report generation failed")
