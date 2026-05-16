"""Input validation and sanitization utilities."""

import re
from typing import Any


class InputValidator:
    """Validates user inputs to ensure data quality and security."""

    @staticmethod
    def validate_session_id(session_id: str) -> bool:
        """Validate session ID format.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            True if valid.
        """
        # Alphanumeric, hyphens, underscores only
        pattern = r'^[a-zA-Z0-9_-]{20,}$'
        return bool(re.match(pattern, session_id))

    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """Validate anonymized user ID.
        
        Args:
            user_id: User identifier.
            
        Returns:
            True if valid.
        """
        pattern = r'^[a-zA-Z0-9_-]{10,}$'
        return bool(re.match(pattern, user_id))

    @staticmethod
    def sanitize_text(text: str, max_length: int = 5000) -> str:
        """Sanitize user text input.
        
        Args:
            text: Text to sanitize.
            max_length: Maximum allowed length.
            
        Returns:
            Sanitized text.
        """
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove null bytes and control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        return text

    @staticmethod
    def validate_gad7_response(responses: dict) -> bool:
        """Validate GAD-7 survey responses.
        
        Args:
            responses: Survey response dictionary.
            
        Returns:
            True if valid.
        """
        required_keys = [f"gad7_{i}" for i in range(1, 8)]
        
        for key in required_keys:
            if key not in responses:
                return False
            
            value = responses[key]
            if not isinstance(value, int) or not (0 <= value <= 3):
                return False
        
        return True

    @staticmethod
    def validate_phq9_response(responses: dict) -> bool:
        """Validate PHQ-9 survey responses.
        
        Args:
            responses: Survey response dictionary.
            
        Returns:
            True if valid.
        """
        required_keys = [f"phq9_{i}" for i in range(1, 10)]
        
        for key in required_keys:
            if key not in responses:
                return False
            
            value = responses[key]
            if not isinstance(value, int) or not (0 <= value <= 3):
                return False
        
        return True
