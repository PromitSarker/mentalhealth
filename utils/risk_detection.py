"""High-risk detection for self-harm and suicidal ideation."""

import re
from enum import Enum


class RiskLevel(str, Enum):
    """Risk severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


RISK_LEVEL_RANK = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


class RiskDetector:
    """Detects high-risk content in user inputs and AI responses."""

    # Keywords indicating self-harm or suicidal ideation
    CRITICAL_KEYWORDS = {
        "suicide", "kill myself", "end my life", "jump", "hang myself",
        "overdose", "cut myself", "self harm", "harm myself", "hurt myself",
        "noose", "wrist", "blade", "knife", "pills", "poison",
    }

    # Keywords indicating severe distress
    HIGH_RISK_KEYWORDS = {
        "hopeless", "worthless", "better off dead", "want to die",
        "can't take it anymore", "give up", "trapped", "helpless",
        "despair", "nothing matters", "pointless",
    }

    MEDIUM_RISK_KEYWORDS = {
        "sad", "depressed", "anxious", "stressed", "overwhelmed",
        "lonely", "tired of living", "struggling",
    }

    @classmethod
    def analyze(cls, text: str) -> tuple[RiskLevel, list[str]]:
        """Analyze text for high-risk content.
        
        Args:
            text: User input or AI response to analyze.
            
        Returns:
            Tuple of (risk_level, detected_keywords).
        """
        text_lower = text.lower()
        detected = []

        # Check critical keywords
        for keyword in cls.CRITICAL_KEYWORDS:
            if cls._word_boundary_search(text_lower, keyword):
                detected.append(keyword)
                return RiskLevel.CRITICAL, detected

        # Check high-risk keywords
        for keyword in cls.HIGH_RISK_KEYWORDS:
            if cls._word_boundary_search(text_lower, keyword):
                detected.append(keyword)

        if len(detected) >= 2:
            return RiskLevel.HIGH, detected
        elif len(detected) >= 1:
            return RiskLevel.MEDIUM, detected

        # Check medium-risk keywords
        medium_detected = []
        for keyword in cls.MEDIUM_RISK_KEYWORDS:
            if cls._word_boundary_search(text_lower, keyword):
                medium_detected.append(keyword)

        if len(medium_detected) >= 3:
            return RiskLevel.MEDIUM, medium_detected
        elif len(medium_detected) >= 1:
            return RiskLevel.LOW, medium_detected

        return RiskLevel.LOW, []

    @staticmethod
    def _word_boundary_search(text: str, keyword: str) -> bool:
        """Search for keyword with word boundaries."""
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return bool(re.search(pattern, text))

    @classmethod
    def should_flag_for_review(cls, risk_level: RiskLevel) -> bool:
        """Determine if content should be flagged for human review.
        
        Args:
            risk_level: Detected risk level.
            
        Returns:
            True if content should be reviewed by a human.
        """
        return risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    @classmethod
    def max_risk_level(cls, *risk_levels: RiskLevel) -> RiskLevel:
        """Return the highest-severity risk level."""
        return max(risk_levels, key=lambda level: RISK_LEVEL_RANK[level])

    @classmethod
    def get_safety_message(cls, risk_level: RiskLevel) -> str | None:
        """Get appropriate safety message for risk level.
        
        Args:
            risk_level: Detected risk level.
            
        Returns:
            Safety message or None for low risk.
        """
        messages = {
            RiskLevel.CRITICAL: (
                "I've detected concerning content in your message. "
                "Please reach out to the Samaritans: 116 123 (24/7, free). "
                "Your safety is our priority."
            ),
            RiskLevel.HIGH: (
                "I'm concerned about what you've shared. "
                "Please consider contacting a mental health professional. "
                "Samaritans: 116 123"
            ),
            RiskLevel.MEDIUM: (
                "I notice you're going through a difficult time. "
                "Professional support can help. Consider reaching out."
            ),
        }
        return messages.get(risk_level)
