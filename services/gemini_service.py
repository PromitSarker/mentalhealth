"""Gemini API integration for therapy-based dialogue."""

import os
import logging
from typing import Optional

from google import genai
from google.genai import types


class GeminiService:
    """Wrapper for Google Gemini API with therapy-focused configuration."""
    
    logger = logging.getLogger(__name__)

    THERAPY_SYSTEM_PROMPT = """You are a compassionate, evidence-based AI therapy assistant. 
Your role is to:
- Listen carefully and validate feelings
- Ask thoughtful, open-ended questions
- Suggest evidence-based coping strategies (CBT, mindfulness, grounding techniques)
- Maintain professional boundaries
- Never diagnose or prescribe medication
- Encourage professional help when appropriate
- Be concise and clear in responses

IMPORTANT: You are NOT a substitute for professional mental health care."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini service.
        
        Args:
            api_key: Gemini API key. If None, uses GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        self.client = genai.Client(api_key=self.api_key)

    def generate_response(
        self, 
        user_message: str, 
        conversation_history: Optional[list] = None,
        gad7_score: Optional[int] = None,
        phq9_score: Optional[int] = None
    ) -> str:
        """Generate therapy-based AI response.
        
        Args:
            user_message: User's input message.
            conversation_history: Previous messages in conversation.
            gad7_score: GAD-7 anxiety score.
            phq9_score: PHQ-9 depression score.
            
        Returns:
            AI-generated response.
        """
        try:
            # Build conversation context.
            contents = []
            if conversation_history:
                for msg in conversation_history:
                    contents.append(
                        types.Content(
                            role=msg.get("role", "user"),
                            parts=[types.Part.from_text(text=msg.get("content", ""))],
                        )
                    )
            
            # Add current message
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_message)],
                )
            )
            
            # Build dynamic system instruction based on clinical context
            system_instruction = self.THERAPY_SYSTEM_PROMPT
            clinical_context = []
            if gad7_score is not None:
                severity = "minimal" if gad7_score < 5 else "mild" if gad7_score < 10 else "moderate" if gad7_score < 15 else "severe"
                clinical_context.append(f"GAD-7 Anxiety Score: {gad7_score}/21 ({severity})")
            if phq9_score is not None:
                severity = "minimal" if phq9_score < 5 else "mild" if phq9_score < 10 else "moderate" if phq9_score < 15 else "moderately severe" if phq9_score < 20 else "severe"
                clinical_context.append(f"PHQ-9 Depression Score: {phq9_score}/27 ({severity})")
            
            if clinical_context:
                context_str = "\n".join(clinical_context)
                system_instruction += f"\n\nCURRENT PATIENT CLINICAL CONTEXT:\n{context_str}\n"
                system_instruction += "ADJUST YOUR APPROACH: For higher scores, prioritize safety, use more frequent validation, and offer more structured, grounded coping strategies. For lower scores, you can be more exploratory."

            # Generate response with safety settings
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    safety_settings=[
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                        ),
                    ],
                    temperature=0.7,
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=1024,
                ),
            )
            
            if not response or not response.text:
                self.logger.error(f"Gemini returned empty response. Response object: {response}")
                return "I'm sorry, I couldn't generate a response right now. Please try again."
            
            return response.text
        
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")





# Singleton instance
_gemini_service = None


def get_gemini_service() -> GeminiService:
    """Get or create Gemini service singleton."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
