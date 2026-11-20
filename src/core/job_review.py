"""
Uses AI to analyze job postings.
Summarizes job details, requirements, and recommendations.
"""
import json
from .ai_client import ask_ai as default_ask_ai

def build_review_prompt(job_posting: str) -> str:
    if not job_posting.strip():
        raise ValueError("Job posting cannot be empty")

    return f"""Review this job posting. Return only JSON with these fields:
- summary: a short string
- skills: a list of required skills
- cover_letter_required: true, false, or null if not stated
- tips: a list of useful application tips

Job posting:
{job_posting}
"""
def parse_review_response(response: str) -> dict:
    try:
        review = json.loads(response)
    except json.JSONDecodeError as error:
        raise ValueError("AI returned invalid JSON") from error

    if not isinstance(review, dict):
        raise ValueError("AI review must be an object")

    if not isinstance(review.get("summary"), str) or not review["summary"].strip():
        raise ValueError("AI review is missing a summary")

    for field in ("skills", "tips"):
        if not isinstance(review.get(field), list):
            raise ValueError(f"AI review is missing {field}")

    cover_letter = review.get("cover_letter_required")
    if "cover_letter_required" not in review or (
        cover_letter is not None and not isinstance(cover_letter, bool)
    ):
        raise ValueError("AI review has an invalid cover letter answer")

    return review
def review_posting(job_posting: str, ask_ai=default_ask_ai) -> dict:
    prompt = build_review_prompt(job_posting)

    for attempt in range(2):
        try:
            response = ask_ai(prompt)
            return parse_review_response(response)
        except ValueError as error:
            if attempt == 1:
                raise ValueError(
                    "AI returned an invalid job review after two attempts"
                ) from error