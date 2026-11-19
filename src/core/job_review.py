"""
Uses AI to analyze job postings.
Summarizes job details, requirements, and recommendations.
"""

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