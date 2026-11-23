"""Reviews a job posting using the shared AI client."""

import json
from .ai_client import ask_ai as default_ask_ai
from .models import JobPosting, JobReview
from pathlib import Path

REVIEW_PROMPT = (Path(__file__).parent / "prompts" / "review_prompt.txt").read_text(
    encoding="utf-8"
)
# Job descriptions can be huge. Trimming keeps the request small.
MAX_DESCRIPTION_CHARS = 6000


def build_review_prompt(job: JobPosting) -> str:
    description = (job.description or "")[:MAX_DESCRIPTION_CHARS]
    text = "\n".join(
        value for value in (
            f"Title: {job.title}",
            f"Company: {job.company}",
            f"Location: {job.location}" if job.location else "",
            description,
        ) if value
    )
    # Plain concatenation, not .format(): the prompt contains JSON braces
    # that .format() would try to treat as placeholders and crash on.
    return f"{REVIEW_PROMPT}\n\n<job_posting>\n{text}\n</job_posting>"


def clean_text_list(value) -> list[str]:
    # Anything that isn't a list becomes an empty list instead of crashing
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


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
    years = data.get("years_experience")
    if not isinstance(years, str) or not years.strip():
        years = None

    return JobReview(
        summary=data["summary"].strip(),
        skills=data["skills"],
        cover_letter_required=cover_letter,
        tips=data["tips"],
        years_experience=years,
        tech_stack=clean_text_list(data.get("tech_stack")),
        other_requirements=clean_text_list(data.get("other_requirements")),
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
