"""AI-powered clinical scoring service for GAD-7 and PHQ-9 assessments.

Uses Google Gemini to calculate scores and generate clinical reports while
strictly adhering to validated GAD-7 and PHQ-9 scoring rules.
"""

import json
import os
import re
import logging
from datetime import datetime
from typing import Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Scoring constants (reference for validation)
# ---------------------------------------------------------------------------

# GAD-7: each item 0-3, total 0-21
GAD7_SEVERITY_BANDS = [
    (0, 4, "minimal"),
    (5, 9, "mild"),
    (10, 14, "moderate"),
    (15, 21, "severe"),
]

# PHQ-9: each item 0-3, total 0-27
PHQ9_SEVERITY_BANDS = [
    (0, 4, "minimal"),
    (5, 9, "mild"),
    (10, 14, "moderate"),
    (15, 19, "moderately severe"),
    (20, 27, "severe"),
]

# ---------------------------------------------------------------------------
# GAD-7 question text (for context in the AI prompt)
# ---------------------------------------------------------------------------
GAD7_QUESTIONS = [
    "Feeling nervous, anxious, or on edge",
    "Not being able to stop or control worrying",
    "Worrying too much about different things",
    "Trouble relaxing",
    "Being so restless that it's hard to sit still",
    "Becoming easily annoyed or irritable",
    "Feeling afraid as if something awful might happen",
]

# ---------------------------------------------------------------------------
# PHQ-9 question text (for context in the AI prompt)
# ---------------------------------------------------------------------------
PHQ9_QUESTIONS = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
    "Trouble concentrating on things, such as reading the newspaper or watching television",
    "Moving or speaking so slowly that other people could have noticed, or the opposite — being so fidgety or restless that you have been moving around a lot more than usual",
    "Thoughts that you would be better off dead, or of hurting yourself in some way",
]

SCORING_SYSTEM_PROMPT = """You are an elite Clinical Psychologist and Psychiatric Diagnostician.
Your task is to conduct a rigorous analysis of GAD-7 and PHQ-9 psychometric data and produce a professional Clinical Assessment Report.

You MUST adhere to the following validated clinical scoring frameworks:

GAD-7 (Generalised Anxiety Disorder-7):
- Scoring: 0–3 per item (Not at all=0, Several days=1, More than half the days=2, Nearly every day=3)
- Range: 0–21
- Severity Indices: 0–4: Minimal; 5–9: Mild; 10–14: Moderate; 15–21: Severe
- Threshold: Score ≥10 indicates clinically significant anxiety.

PHQ-9 (Patient Health Questionnaire-9):
- Scoring: 0–3 per item (Scale as above)
- Range: 0–27
- Severity Indices: 0–4: Minimal; 5–9: Mild; 10–14: Moderate; 15–19: Moderately Severe; 20–27: Severe
- Threshold: Score ≥10 indicates clinically significant depressive pathology.
- Critical Item: Item 9 (Suicidality/Self-harm) requires immediate clinical flag if score > 0.

CLINICAL NARRATIVE REQUIREMENTS (clinical_summary):
- Use formal psychiatric terminology (e.g., "affective dysregulation", "somatic preoccupation", "anhedonia", "psychomotor alterations").
- Structure: 
  1. Overview: State the primary clinical profile based on score aggregations.
  2. Symptomatic Analysis: Identify specific clusters (e.g., "prominent cognitive-worry components" or "vegetative symptoms of depression").
  3. Risk Assessment: Explicitly mention suicidality (Item 9) or severe distress.
  4. Clinical Impression: Synthesise the findings without providing a definitive diagnosis (use "suggestive of", "indicative of").
- Tone: Professional, objective, and clinically detached yet precise.

OUTPUT FORMAT:
Return a JSON object with EXACTLY these fields:
{
  "gad7_score": <int>,
  "gad7_severity": "<minimal|mild|moderate|severe>",
  "phq9_score": <int>, 
  "phq9_severity": "<minimal|mild|moderate|moderately severe|severe>",
  "clinical_summary": "<Professional clinical narrative (200-300 words). Use formal clinical syntax.>",
  "recommended_next_steps": [
    "<Step 1 — NICE-aligned intervention>",
    ...
  ]
}

INTERVENTION HIERARCHY (recommended_next_steps):
- Must strictly align with NICE Guidelines for Anxiety and Depression.
- Urgent: If PHQ9 Item 9 > 0 or GAD7/PHQ9 ≥ 15, the first step MUST be immediate risk assessment/crisis referral.
- Moderate (Score 10-14): Recommend High-Intensity IAPT, CBT, and formal GP Review.
- Mild (Score 5-9): Recommend Low-Intensity psychosocial interventions, guided self-help, or watchful waiting.
- Sub-clinical (< 5): Recommend wellness monitoring and psychoeducation.
"""


def _validate_and_normalize_score(score_val, item_name):
    """Validate and normalize a score to 0-3 integer range."""
    # Handle numeric scores
    if isinstance(score_val, int):
        if 0 <= score_val <= 3:
            return score_val
        else:
            raise ValueError(f"Score for {item_name} must be between 0 and 3, got {score_val}")
    
    # Handle text scores
    if isinstance(score_val, str):
        score_lower = score_val.strip().lower()
        text_to_score = {
            "not at all": 0,
            "several days": 1,
            "more than half the days": 2,
            "nearly every day": 3
        }
        if score_lower in text_to_score:
            return text_to_score[score_lower]
        else:
            raise ValueError(f"Invalid text response for {item_name}: '{score_val}'. Expected: 'Not at all', 'Several days', 'More than half the days', or 'Nearly every day'")
    
    raise ValueError(f"Score for {item_name} must be integer 0-3 or valid text response, got {score_val}")


def _calculate_score_based_on_responses(responses_dict, scale_items, scale_name):
    """Helper to calculate score from responses with validation."""
    total = 0
    item_scores = {}
    
    for i, item_key in enumerate(scale_items, 1):
        if item_key not in responses_dict:
            raise ValueError(f"Missing required response for {scale_name} item {i}")
        
        score = _validate_and_normalize_score(responses_dict[item_key], f"{scale_name} item {i}")
        item_scores[item_key] = score
        total += score
    
    return total, item_scores


def _get_severity(score: int, bands: list[tuple]) -> str:
    """Look up severity label from score using the provided bands."""
    for min_s, max_s, label in bands:
        if min_s <= score <= max_s:
            return label
    raise ValueError(f"Score {score} is out of valid range for {scale_name}")


def _build_scoring_prompt(text_responses: dict, numeric_responses: dict = None) -> str:
    """Build a detailed prompt for AI-based scoring and analysis."""
    
    # Prepare responses for the prompt - prefer text responses, fall back to numeric
    all_responses = {}
    if numeric_responses:
        all_responses.update(numeric_responses)
    if text_responses:
        all_responses.update(text_responses)
    
    # Format GAD-7 items
    gad7_items_text = ""
    for i, question in enumerate(GAD7_QUESTIONS, 1):
        item_key = f"gad7_{i}"
        value = all_responses.get(item_key, "NOT PROVIDED")
        if isinstance(value, str):
            gad7_items_text += f"  GAD-7 Item {i} ({question}): {value}\\n"
        else:
            # Convert numeric to text for display
            num_to_text = {0: "Not at all", 1: "Several days", 2: "More than half the days", 3: "Nearly every day"}
            display_value = num_to_text.get(value, str(value))
            gad7_items_text += f"  GAD-7 Item {i} ({question}): {display_value} ({value})\\n"
    
    # Format PHQ-9 items
    phq9_items_text = ""
    for i, question in enumerate(PHQ9_QUESTIONS, 1):
        item_key = f"phq9_{i}"
        value = all_responses.get(item_key, "NOT PROVIDED")
        if isinstance(value, str):
            phq9_items_text += f"  PHQ-9 Item {i} ({question}): {value}\\n"
        else:
            # Convert numeric to text for display
            num_to_text = {0: "Not at all", 1: "Several days", 2: "More than half the days", 3: "Nearly every day"}
            display_value = num_to_text.get(value, str(value))
            phq9_items_text += f"  PHQ-9 Item {i} ({question}): {display_value} ({value})\\n"
    
    return f"""Please conduct a formal clinical analysis of the psychometric data provided below. 

=== CLINICAL DATA: GAD-7 & PHQ-9 ===

[SURVEY RESPONSES]
GAD-7 (Generalised Anxiety Disorder):
{gad7_items_text}

PHQ-9 (Patient Health Questionnaire):
{phq9_items_text}

=== CLINICAL INSTRUCTIONS ===

1. Score Calculation: Verify 0-3 weighting for each item and aggregate totals.
2. Severity Mapping: Determine severity based on validated bands (0-4 Min, 5-9 Mild, 10-14 Mod, 15+ Sev).
3. Clinical Summary: Draft a professional narrative using psychiatric terminology. Focus on symptom clusters, distress levels, and functional impact as suggested by the data.
4. Recommendations: Provide a phased intervention plan aligned with the stepped-care model (NICE).

=== JSON SCHEMA OUTPUT ===

{{
  "gad7_score": <int>,
  "gad7_severity": "<string>",
  "phq9_score": <int>, 
  "phq9_severity": "<string>",
  "clinical_summary": "<string: structured clinical narrative>",
  "recommended_next_steps": ["<string: intervention 1>", "<string: intervention 2>", ...]
}}

FINAL VALIDATION:
- Verify mathematical accuracy of scores.
- Ensure "clinical_summary" is professional and avoids colloquialisms.
- Do NOT include any preamble or post-script; return valid JSON only.
"""


class ScoringService:
    """AI-powered GAD-7 and PHQ-9 scoring service using Google Gemini.

    The AI calculates scores from survey responses following validated clinical rules,
    then generates clinical summaries and recommendations.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self.client = genai.Client(api_key=self.api_key)

    def _call_gemini_for_scoring(self, text_responses: dict, numeric_responses: dict = None) -> dict:
        """Make a Gemini API call for scoring and analysis.

        Returns:
            Parsed dict with all required fields.

        Raises:
            RuntimeError: If the API call fails or response is unparseable.
            ValueError: If AI output fails validation.
        """
        prompt = _build_scoring_prompt(text_responses, numeric_responses)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=SCORING_SYSTEM_PROMPT,
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
                temperature=0.2,   # Low temperature for consistent, rule-following output
                top_p=0.95,
                top_k=40,
                max_output_tokens=4096,
            ),
        )

        raw = response.text if response else ""
        result = self._parse_and_validate_json_response(raw)
        return result

    def _parse_and_validate_json_response(self, raw: str) -> dict:
        """Extract, parse, and validate the JSON block from the AI response."""
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()

        # Try direct parse first
        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to extract JSON object via regex
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            else:
                raise RuntimeError(f"Could not parse JSON from AI response: {raw[:200]}")

        # Validate required fields
        required_fields = ["gad7_score", "gad7_severity", "phq9_score", "phq9_severity", "clinical_summary", "recommended_next_steps"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field in AI response: {field}")

        # Validate score ranges and types
        try:
            gad7_score = int(result["gad7_score"])
            phq9_score = int(result["phq9_score"])
            
            if not (0 <= gad7_score <= 21):
                raise ValueError(f"GAD-7 score must be between 0-21, got {gad7_score}")
            if not (0 <= phq9_score <= 27):
                raise ValueError(f"PHQ-9 score must be between 0-27, got {phq9_score}")
                
            result["gad7_score"] = gad7_score
            result["phq9_score"] = phq9_score
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid score format: {e}")

        # Validate severity labels
        valid_gad7_severities = {"minimal", "mild", "moderate", "severe"}
        valid_phq9_severities = {"minimal", "mild", "moderate", "moderately severe", "severe"}
        
        if result["gad7_severity"] not in valid_gad7_severities:
            raise ValueError(f"Invalid GAD-7 severity: {result['gad7_severity']}. Must be one of {valid_gad7_severities}")
        if result["phq9_severity"] not in valid_phq9_severities:
            raise ValueError(f"Invalid PHQ-9 severity: {result['phq9_severity']}. Must be one of {valid_phq9_severities}")

        # Validate severity matches score (double-check AI followed rules)
        expected_gad7_severity = _get_severity(gad7_score, GAD7_SEVERITY_BANDS)
        expected_phq9_severity = _get_severity(phq9_score, PHQ9_SEVERITY_BANDS)
        
        if result["gad7_severity"] != expected_gad7_severity:
            raise ValueError(f"GAD-7 severity mismatch: AI said '{result['gad7_severity']}' but score {gad7_score} should be '{expected_gad7_severity}'")
        if result["phq9_severity"] != expected_phq9_severity:
            raise ValueError(f"PHQ-9 severity mismatch: AI said '{result['phq9_severity']}' but score {phq9_score} should be '{expected_phq9_severity}'")

        # Validate recommendations is a list
        if not isinstance(result["recommended_next_steps"], list):
            raise ValueError("recommended_next_steps must be a list")
        if not all(isinstance(step, str) for step in result["recommended_next_steps"]):
            raise ValueError("All recommended_next_steps must be strings")

        return result

    def _normalize_responses(self, responses: dict) -> dict:
        """Normalize responses by mapping question text to gad7_N/phq9_N keys if missing.
        
        This ensures that the AI prompt builder and fallback calculators have
        the expected keys even if the input uses full question text.
        """
        normalized = {}
        
        # 1. Copy existing standard keys (gad7_1-7, phq9_1-9)
        for k, v in responses.items():
            k_lower = str(k).lower().strip()
            if k_lower.startswith(("gad7_", "phq9_")):
                normalized[k_lower] = v
        
        # 2. Try to map question text to missing standard keys
        for k, v in responses.items():
            k_clean = str(k).strip().lower()
            if k_clean.startswith(("gad7_", "phq9_")):
                continue
                
            # Try to match against GAD-7 questions
            for i, q in enumerate(GAD7_QUESTIONS, 1):
                item_key = f"gad7_{i}"
                if item_key not in normalized:
                    # Match if the question text is exactly the same or a significant part of it
                    if q.lower() in k_clean or k_clean in q.lower():
                        normalized[item_key] = v
                        break
            
            # Try to match against PHQ-9 questions
            for i, q in enumerate(PHQ9_QUESTIONS, 1):
                item_key = f"phq9_{i}"
                if item_key not in normalized:
                    if q.lower() in k_clean or k_clean in q.lower():
                        normalized[item_key] = v
                        break
        
        # 3. If still missing keys and we have exactly 16 responses, try index-based mapping
        # This is a common pattern for clinical data exports
        if len(normalized) < 16 and len(responses) == 16:
            # Get list of values in original order if it was a list (passed as dict keys)
            # This is risky but helpful as a last resort
            all_values = list(responses.values())
            for i in range(1, 8):
                if f"gad7_{i}" not in normalized:
                    normalized[f"gad7_{i}"] = all_values[i-1]
            for i in range(1, 10):
                if f"phq9_{i}" not in normalized:
                    normalized[f"phq9_{i}"] = all_values[i+6]

        # 4. Include any extra keys as-is
        for k, v in responses.items():
            if k not in normalized and k.lower() not in normalized:
                normalized[k] = v
                
        return normalized

    # ------------------------------------------------------------------
    # Public scoring methods
    # ------------------------------------------------------------------

    def calculate_gad7(self, responses: dict) -> tuple[int, str]:
        """Calculate GAD-7 score and severity using AI.

        Args:
            responses: Dict with keys 'gad7_1' through 'gad7_7' 
                      (values can be text responses or integers 0-3).

        Returns:
            Tuple of (score, severity_label).
        """
        # Extract and normalize GAD-7 responses
        norm_responses = self._normalize_responses(responses)
        gad7_responses = {k: v for k, v in norm_responses.items() if k.startswith("gad7_")}
        
        result = self._call_gemini_for_scoring(gad7_responses)
        return result["gad7_score"], result["gad7_severity"]

    def calculate_phq9(self, responses: dict) -> tuple[int, str]:
        """Calculate PHQ-9 score and severity using AI.

        Args:
            responses: Dict with keys 'phq9_1' through 'phq9_9' 
                      (values can be text responses or integers 0-3).

        Returns:
            Tuple of (score, severity_label).
        """
        # Extract and normalize PHQ-9 responses
        norm_responses = self._normalize_responses(responses)
        phq9_responses = {k: v for k, v in norm_responses.items() if k.startswith("phq9_")}
        
        result = self._call_gemini_for_scoring(phq9_responses)
        return result["phq9_score"], result["phq9_severity"]

    def generate_clinical_summary(self, gad7_score: int, gad7_severity: str,
                                  phq9_score: int, phq9_severity: str,
                                  responses: Optional[dict] = None) -> str:
        """Generate clinical summary - for backward compatibility.
        
        Note: This method now expects pre-calculated scores. For full AI scoring,
        use score_and_analyse() instead.
        """
        # For backward compatibility, we'll generate a summary based on given scores
        # but we still need the responses to generate meaningful content
        if responses is None:
            responses = {}
        
        # Use AI to generate just the summary and recommendations
        try:
            norm_responses = self._normalize_responses(responses)
            result = self._call_gemini_for_scoring(norm_responses)
            return result.get("clinical_summary", self._fallback_summary(
                gad7_score, gad7_severity, phq9_score, phq9_severity
            ))
        except Exception:
            return self._fallback_summary(gad7_score, gad7_severity, phq9_score, phq9_severity)

    def get_recommended_next_steps(self, gad7_score: int, phq9_score: int,
                                   responses: Optional[dict] = None) -> list[str]:
        """Generate recommended next steps - for backward compatibility."""
        if responses is None:
            responses = {}
        
        try:
            norm_responses = self._normalize_responses(responses)
            result = self._call_gemini_for_scoring(norm_responses)
            steps = result.get("recommended_next_steps")
            if isinstance(steps, list) and steps:
                return steps
        except Exception:
            pass

        return self._fallback_recommendations(gad7_score, phq9_score, responses)

    def score_and_analyse(self, responses: dict) -> dict:
        """Full AI-powered scoring pipeline - calculates scores and generates report.

        This is the main method that uses AI for everything: score calculation,
        severity determination, clinical summary, and recommendations.

        Args:
            responses: Dict with survey responses. Can include:
                      - Text responses: "Not at all", "Several days", etc.
                      - Numeric responses: 0, 1, 2, 3
                      - Keys: gad7_1-7, phq9_1-9

        Returns:
            Dict with keys: gad7_score, gad7_severity, phq9_score, phq9_severity,
            clinical_summary, recommended_next_steps.
        """
        # Normalize input to ensure standard keys are present
        responses = self._normalize_responses(responses)
        
        try:
            ai_result = self._call_gemini_for_scoring(responses)
            return {
                "gad7_score": ai_result["gad7_score"],
                "gad7_severity": ai_result["gad7_severity"],
                "phq9_score": ai_result["phq9_score"],
                "phq9_severity": ai_result["phq9_severity"],
                "clinical_summary": ai_result["clinical_summary"],
                "recommended_next_steps": ai_result["recommended_next_steps"],
            }
        except Exception as e:
            logger.warning(f"AI scoring failed, using rule-based fallback: {str(e)}")
            # Fallback to rule-based calculation if AI fails
            gad7_score, gad7_severity = self._calculate_gad7_fallback(responses)
            phq9_score, phq9_severity = self._calculate_phq9_fallback(responses)
            
            return {
                "gad7_score": gad7_score,
                "gad7_severity": gad7_severity,
                "phq9_score": phq9_score,
                "phq9_severity": phq9_severity,
                "clinical_summary": self._fallback_summary(gad7_score, gad7_severity, phq9_score, phq9_severity),
                "recommended_next_steps": self._fallback_recommendations(gad7_score, phq9_score, responses),
            }

    # ------------------------------------------------------------------
    # Fallback methods (rule-based, used when AI fails)
    # ------------------------------------------------------------------

    def _calculate_gad7_fallback(self, responses: dict) -> tuple[int, str]:
        """Fallback GAD-7 calculation using validated clinical rules."""
        items = [f"gad7_{i}" for i in range(1, 8)]
        total = 0
        for item in items:
            if item not in responses:
                raise ValueError(f"Missing required response: {item}")
            total += _validate_and_normalize_score(responses[item], item)
        return total, _get_severity(total, GAD7_SEVERITY_BANDS)

    def _calculate_phq9_fallback(self, responses: dict) -> tuple[int, str]:
        """Fallback PHQ-9 calculation using validated clinical rules."""
        items = [f"phq9_{i}" for i in range(1, 10)]
        total = 0
        for item in items:
            if item not in responses:
                raise ValueError(f"Missing required response: {item}")
            total += _validate_and_normalize_score(responses[item], item)
        return total, _get_severity(total, PHQ9_SEVERITY_BANDS)

    @staticmethod
    def _fallback_summary(gad7_score: int, gad7_severity: str,
                          phq9_score: int, phq9_severity: str) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        return (
            f"CLINICAL ASSESSMENT REPORT\n"
            f"Date of Assessment: {now}\n"
            f"Instruments: GAD-7, PHQ-9\n"
            f"--------------------------------------------------\n\n"
            f"EXECUTIVE SUMMARY:\n"
            f"The clinical assessment indicates a presentation of {gad7_severity} anxiety symptoms "
            f"(GAD-7 Score: {gad7_score}/21) and {phq9_severity} depressive symptoms "
            f"(PHQ-9 Score: {phq9_score}/27).\n\n"
            f"CLINICAL IMPRESSION:\n"
            f"The patient's psychometric profile is suggestive of {gad7_severity} generalized anxiety "
            f"and {phq9_severity} depressive pathology. Scores in these ranges indicate "
            f"{'clinically significant distress' if (gad7_score >= 10 or phq9_score >= 10) else 'sub-clinical levels of distress'}.\n\n"
            f"SYMPTOM ANALYSIS:\n"
            f"- Anxiety: The GAD-7 score of {gad7_score} falls within the {gad7_severity} range.\n"
            f"- Depression: The PHQ-9 score of {phq9_score} falls within the {phq9_severity} range.\n\n"
            f"Note: This is an automated summary generated due to high system load. "
            f"For the full enhanced AI clinical narrative, please re-run the assessment."
        )

    @staticmethod
    def _fallback_recommendations(gad7_score: int, phq9_score: int,
                                  responses: dict) -> list[str]:
        recs = []
        phq9_item9 = responses.get("phq9_9", 0)

        # Convert text response to numeric if needed
        if isinstance(phq9_item9, str):
            phq9_item9 = _validate_and_normalize_score(phq9_item9, "phq9_9")

        if phq9_item9 > 0:
            recs.append("Urgent: Conduct immediate safety assessment for suicidal/self-harm ideation")

        if gad7_score >= 15 or phq9_score >= 15:
            recs.append("Urgent: Consider urgent mental health referral")
            recs.append("Contact crisis support if in immediate distress")

        if gad7_score >= 10:
            recs.append("Consult with GP regarding anxiety management")
            recs.append("Consider CBT or other evidence-based psychotherapy")
            recs.append("Explore relaxation and mindfulness techniques")

        if phq9_score >= 10:
            recs.append("Arrange GP appointment for depression assessment")
            recs.append("Engage in behavioural activation and self-care strategies")

        if not recs:
            recs.append("Continue current self-care and monitoring")
            recs.append("Maintain regular exercise and social engagement")
            recs.append("Schedule follow-up assessment in 4-6 weeks")

        return recs