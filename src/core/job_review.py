"""Reviews a job posting using the shared AI client."""

import json

from .ai_client import ask_ai as default_ask_ai
from .models import JobPosting, JobReview


def build_review_prompt(job: JobPosting) -> str:
    text = "\n".join(
        value for value in (
            f"Title: {job.title}",
            f"Company: {job.company}",
            f"Location: {job.location}" if job.location else "",
            job.description or "",
        ) if value
    )
    if not text.strip():
        raise ValueError("Job posting cannot be empty")

    return f"""Review this job posting. Return only JSON with these fields:
- summary: a short string
- skills: a list of required skills
- cover_letter_required: true, false, or null if not stated
- tips: a list of useful application tips

Job posting:
{text}
"""


def parse_review_response(response: str) -> JobReview:
    try:
        data = json.loads(response)
    except json.JSONDecodeError as error:
        raise ValueError("AI returned invalid JSON") from error

    if not isinstance(data, dict):
        raise ValueError("AI review must be an object")
    if not isinstance(data.get("summary"), str) or not data["summary"].strip():
        raise ValueError("AI review is missing a summary")
    if not isinstance(data.get("skills"), list):
        raise ValueError("AI review is missing skills")
    if not isinstance(data.get("tips"), list):
        raise ValueError("AI review is missing tips")

    cover_letter = data.get("cover_letter_required")
    if "cover_letter_required" not in data or (
        cover_letter is not None and not isinstance(cover_letter, bool)
    ):
        raise ValueError("AI review has an invalid cover letter answer")

    return JobReview(
        summary=data["summary"].strip(),
        skills=data["skills"],
        cover_letter_required=cover_letter,
        tips=data["tips"],
    )


def review_posting(job: JobPosting, ask_ai=default_ask_ai) -> JobReview:
    prompt = build_review_prompt(job)
    for attempt in range(2):
        try:
            return parse_review_response(ask_ai(prompt))
        except ValueError as error:
            if attempt == 1:
                raise ValueError(
                    "AI returned an invalid job review after two attempts"
                ) from error
