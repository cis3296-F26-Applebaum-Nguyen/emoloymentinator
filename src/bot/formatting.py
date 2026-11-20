"""
Formats job search results and AI reviews into Discord messages.
"""

from collections.abc import Sequence

from src.core.models import JobPosting


def format_job_list(query: str, jobs: Sequence[JobPosting]) -> str:
    """Build the numbered list shown after /search."""
    lines = [f"Found {len(jobs)} jobs for **{query}**:", ""]
    for number, job in enumerate(jobs, start=1):
        where = f" ({job.location})" if job.location else ""
        lines.append(f"**{number}.** {job.title} - {job.company}{where}")
    lines.append("")
    lines.append("Use `/review <number>` to get an AI review of a job.")
    return "\n".join(lines)
