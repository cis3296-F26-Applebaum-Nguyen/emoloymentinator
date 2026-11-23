"""Handles Discord slash command behavior."""

from asyncio import to_thread
from collections.abc import Callable

from discord.errors import NotFound

from .formatting import DISCORD_MESSAGE_LIMIT, format_job_list, format_job_review, split_message
from ..core.models import JobPosting, JobReview
from ..core.query_parser import SearchParseError, parse_search_request
from ..core.job_search import JobSearchError, search_jobs_async
from ..core.job_review import review_posting
from ..core.result_store import (
    InvalidJobNumberError,
    NoSearchResultsError,
    get_job,
)


def placeholder_results(query: str) -> list[JobPosting]:
    samples = [
        ("Junior", "Acme Software", "Philadelphia, PA"),
        ("Senior", "Globex Corp", "Remote"),
        ("Intern", "Initech", "New York, NY"),
        ("Lead", "Umbrella Labs", "Boston, MA"),
        ("Associate", "Hooli", "Remote"),
    ]
    return [
        JobPosting(title=f"{level} {query}", company=company, location=location)
        for level, company, location in samples
    ]


def fake_review(job: JobPosting) -> JobReview:
    return JobReview(
        summary=f"Review of {job.title} at {job.company}",
        tips=["Review the responsibilities carefully."],
    )


def build_review_message(
    user_id: int,
    number: int,
    review_fn: Callable[[JobPosting], JobReview | str] = fake_review,
) -> str:
    try:
        job = get_job(user_id, number)
    except NoSearchResultsError:
        return "You haven't searched yet. Use /search first, then /review <number>."
    except InvalidJobNumberError as error:
        return f"Job {error.number} isn't in your list. Pick a number from 1 to {error.total}."

    try:
        answer = review_fn(job)
    except Exception as error:
        return f"I couldn't complete that review: {error}"
    message = format_job_review(answer) if isinstance(answer, JobReview) else answer
    if len(message) > DISCORD_MESSAGE_LIMIT:
        message = split_message(message)[0]
    return message


async def handle_search(
    interaction,
    query: str,
    parse_fn=parse_search_request,
    search_fn=search_jobs_async,
    save_fn=None,
) -> None:
    if not query.strip():
        await interaction.response.send_message("Please provide a job search query.")
        return

    await interaction.response.send_message("Working on it...")
    try:
        request = parse_fn(query.strip())
        jobs = await search_fn(request)
    except SearchParseError as error:
        await interaction.followup.send(str(error))
        return
    except JobSearchError as error:
        await interaction.followup.send(f"Job search is unavailable: {error}")
        return
    except Exception:
        await interaction.followup.send("I couldn't complete that search. Please try again.")
        return

    if not jobs:
        await interaction.followup.send("No jobs found. Try a different search.")
        return

    if save_fn is not None:
        save_fn(interaction.user.id, jobs)
    for piece in split_message(format_job_list(query.strip(), jobs)):
        await interaction.followup.send(piece)


async def handle_review(
    interaction,
    number: int,
    review_fn: Callable[[JobPosting], JobReview | str] = fake_review,
) -> None:
    try:
        await interaction.response.defer()
        await interaction.followup.send("Working on it...")
    except NotFound as error:
        if error.code == 10062:
            return
        raise

    message = await to_thread(
        build_review_message,
        interaction.user.id,
        number,
        review_fn,
    )
    for piece in split_message(message):
        try:
            await interaction.followup.send(piece)
        except NotFound as error:
            if error.code == 10062:
                return
            raise
