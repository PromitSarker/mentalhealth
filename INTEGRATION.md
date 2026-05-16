"""API Integration Examples - AI Therapy Platform."""

import requests
import json
import base64
from datetime import datetime

# Base URL (adjust for your deployment)

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

class TherapyPlatformClient:
"""Python client for AI Therapy Platform API."""

    def __init__(self, base_url: str = BASE_URL):
        """Initialize API client.

        Args:
            base_url: API server base URL.
        """
        self.base_url = base_url
        self.session_id = None
        self.user_id = None

    def health_check(self) -> dict:
        """Check API health status."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def start_session(self, user_id: str) -> str:
        """Initialize new therapy session.

        Args:
            user_id: Anonymized user identifier.

        Returns:
            Session ID.
        """
        self.user_id = user_id

        response = requests.post(
            f"{self.base_url}/ai/chat/session-start",
            params={"user_id": user_id},
            headers=HEADERS
        )
        response.raise_for_status()

        data = response.json()
        self.session_id = data["session_id"]
        return self.session_id

    def chat_interact(self, user_message: str) -> dict:
        """Send message and receive therapy response.

        Args:
            user_message: User's input message.

        Returns:
            Chat response with AI reply and risk assessment.
        """
        if not self.session_id or not self.user_id:
            raise ValueError("Session not initialized. Call start_session() first.")

        payload = {
            "session_id": self.session_id,
            "user_message": user_message,
            "user_id": self.user_id,
        }

        response = requests.post(
            f"{self.base_url}/ai/chat/interact",
            json=payload,
            headers=HEADERS
        )
        response.raise_for_status()

        return response.json()

    def speech_to_text(self, audio_file_path: str, language: str = "en-GB") -> dict:
        """Convert speech to text.

        Args:
            audio_file_path: Path to audio file.
            language: Language code (default: en-GB).

        Returns:
            Transcription response.
        """
        if not self.session_id:
            raise ValueError("Session not initialized.")

        # Read and encode audio file
        with open(audio_file_path, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode()

        payload = {
            "session_id": self.session_id,
            "audio_data": audio_data,
            "language": language,
        }

        response = requests.post(
            f"{self.base_url}/ai/audio/stt",
            json=payload,
            headers=HEADERS
        )
        response.raise_for_status()

        return response.json()

    def text_to_speech(self, text: str, voice: str = "en-GB-Neural2-A") -> bytes:
        """Convert text to speech.

        Args:
            text: Text to synthesize.
            voice: Voice ID (default: en-GB-Neural2-A).

        Returns:
            Audio data (bytes).
        """
        if not self.session_id:
            raise ValueError("Session not initialized.")

        payload = {
            "session_id": self.session_id,
            "text": text,
            "voice": voice,
        }

        response = requests.post(
            f"{self.base_url}/ai/audio/tts",
            json=payload,
            headers=HEADERS
        )
        response.raise_for_status()

        data = response.json()
        return base64.b64decode(data["audio_data"])

    def generate_report(self, survey_responses: dict, include_audit: bool = True) -> dict:
        """Generate clinical report with GAD-7/PHQ-9 scores.

        Args:
            survey_responses: Dictionary with survey items (gad7_1-7, phq9_1-9).
            include_audit: Include audit trail (default: True).

        Returns:
            Clinical report with scores and recommendations.
        """
        if not self.session_id or not self.user_id:
            raise ValueError("Session not initialized.")

        payload = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "survey_responses": survey_responses,
            "include_audit_trail": include_audit,
        }

        response = requests.post(
            f"{self.base_url}/ai/report/generate",
            json=payload,
            headers=HEADERS
        )
        response.raise_for_status()

        return response.json()

    def gdpr_delete_user(self, reason: str = None) -> dict:
        """Request right-to-be-forgotten (GDPR Article 17).

        Args:
            reason: Reason for deletion (optional).

        Returns:
            Deletion request status.
        """
        if not self.user_id:
            raise ValueError("User ID not set.")

        payload = {
            "user_id": self.user_id,
            "reason": reason or "User-requested deletion",
        }

        response = requests.post(
            f"{self.base_url}/ai/gdpr/delete",
            json=payload,
            headers=HEADERS
        )
        response.raise_for_status()

        return response.json()

    def gdpr_export_user(self) -> dict:
        """Export all user data (GDPR Article 15).

        Returns:
            User data export.
        """
        if not self.user_id:
            raise ValueError("User ID not set.")

        response = requests.post(
            f"{self.base_url}/ai/gdpr/export",
            params={"user_id": self.user_id},
            headers=HEADERS
        )
        response.raise_for_status()

        return response.json()

    def end_session(self) -> dict:
        """End therapy session securely."""
        if not self.session_id:
            raise ValueError("Session not initialized.")

        response = requests.post(
            f"{self.base_url}/ai/chat/session-end",
            json={"session_id": self.session_id},
            headers=HEADERS
        )
        response.raise_for_status()

        self.session_id = None
        return response.json()

# ============================================================================

# USAGE EXAMPLES

# ============================================================================

if **name** == "**main**": # Initialize client
client = TherapyPlatformClient()

    # Check API health
    print("Health Check:", client.health_check())

    # Start session
    user_id = "user-12345-anonymized"
    session_id = client.start_session(user_id)
    print(f"Session Started: {session_id}")

    # Example chat interaction
    chat_response = client.chat_interact(
        "I've been feeling anxious and struggling to sleep lately"
    )
    print(f"\nAI Response: {chat_response['ai_response']}")
    print(f"Risk Level: {chat_response['risk_level']}")
    print(f"Flagged for Review: {chat_response['flagged_for_review']}")

    # Example clinical assessment
    survey_data = {
        # GAD-7 items (0-3 scale)
        "gad7_1": 2,  # Nervous, anxious
        "gad7_2": 2,  # Worrying too much
        "gad7_3": 1,  # Trouble relaxing
        "gad7_4": 3,  # Restless
        "gad7_5": 2,  # Irritable
        "gad7_6": 1,  # Afraid something bad
        "gad7_7": 2,  # Difficulty controlling worry
        # PHQ-9 items (0-3 scale)
        "phq9_1": 2,  # Little interest
        "phq9_2": 1,  # Feeling down
        "phq9_3": 2,  # Trouble sleeping
        "phq9_4": 0,  # Tired/fatigue
        "phq9_5": 1,  # Appetite change
        "phq9_6": 1,  # Feeling bad about yourself
        "phq9_7": 2,  # Trouble concentrating
        "phq9_8": 1,  # Moving/speaking slowly
        "phq9_9": 0,  # Thoughts of harm
    }

    report = client.generate_report(survey_data)
    print(f"\nGAD-7 Score: {report['gad7_score']}/21 ({report['gad7_severity']})")
    print(f"PHQ-9 Score: {report['phq9_score']}/27 ({report['phq9_severity']})")
    print(f"\nClinical Summary:\n{report['clinical_summary']}")
    print(f"\nRecommended Next Steps:")
    for i, step in enumerate(report['recommended_next_steps'], 1):
        print(f"  {i}. {step}")

    # End session
    client.end_session()
    print("\nSession Ended")
