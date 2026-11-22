"""Formats bot output for Discord."""

from collections.abc import Sequence

from ..core.models import JobPosting, JobReview

DISCORD_MESSAGE_LIMIT = 2000


def split_message(text: str, limit: int = DISCORD_MESSAGE_LIMIT) -> list[str]:
    if len(text) <= limit:
        return [text]

    pieces = []
    start = 0
    while start < len(text):
        end = min(start + limit, len(text))
        if end < len(text):
            newline = text.rfind("\n", start, end)
            if newline > start:
                end = newline + 1
        pieces.append(text[start:end])
        start = end
    return pieces


def format_job_list(query: str, jobs: Sequence[JobPosting]) -> str:
    lines = [f"Found {len(jobs)} jobs for **{query}**:", ""]
    for number, job in enumerate(jobs, start=1):
        location = f" ({job.location})" if job.location else ""
        lines.append(f"**{number}.** {job.title} - {job.company}{location}")
    lines.append("")
    lines.append("Use `/review <number>` to get an AI review of a job.")
    return "\n".join(lines)


def format_job_review(review: JobReview) -> str:
    lines = [review.summary]
    if review.skills:
        lines.append("")
        lines.append("Skills: " + ", ".join(review.skills))
    if review.cover_letter_required is not None:
        lines.append("")
        lines.append(
            "Cover letter: "
            + ("required" if review.cover_letter_required else "not mentioned")
        )
    if review.tips:
        lines.append("")
        lines.append("Tips:")
        lines.extend(f"- {tip}" for tip in review.tips)
    return "\n".join(lines)
