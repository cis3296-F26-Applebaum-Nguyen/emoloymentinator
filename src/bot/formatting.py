"""Pure text formatting for Discord messages. No discord import here."""
from __future__ import annotations

from collections.abc import Iterable

from core.models import JobPosting

DISCORD_MESSAGE_LIMIT = 1900


def _shorten(text: str, limit: int = DISCORD_MESSAGE_LIMIT) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _job_line(number: int, posting: JobPosting) -> str:
    title = f"[{posting.title}]({posting.job_url})" if posting.job_url else posting.title
    extras = []
    if posting.company:
        extras.append(posting.company)
    if posting.location:
        extras.append(posting.location)
    if posting.salary:
        extras.append(posting.salary)
    if posting.site:
        extras.append(posting.site)
    detail = " · ".join(extras)
    return f"{number}. **{title}**" + (f" — {detail}" if detail else "")


def format_search_results(postings: Iterable[JobPosting]) -> str:
    """Create the message posted after /search."""
    postings = list(postings)
    if not postings:
        return "No jobs matched that search. Try a broader title or fewer filters."

    lines = [f"**{len(postings)} job(s) found**"]
    lines.extend(_job_line(number, posting)
                 for number, posting in enumerate(postings, start=1))
    lines.append("Use `/review <number>` to have the AI review one of these jobs.")
    return _shorten("\n".join(lines))


def format_error(message: str) -> str:
    """Create a user-safe error message."""
    return f"⚠️ {message}"
