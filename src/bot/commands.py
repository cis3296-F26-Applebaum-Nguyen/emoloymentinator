"""
Handles Discord slash commands such as /search and /review.
Connects user commands to the backend functionality.
"""

from collections.abc import Callable

from src.core.models import JobPosting
from src.core.result_store import (
    InvalidJobNumberError,
    NoSearchResultsError,
    get_job,
)

DISCORD_MESSAGE_LIMIT = 2000


def placeholder_results(query: str) -> list[JobPosting]:
    """
    Stand-in search results until the real search (#14) is wired into /search.
    Replace the call in bot/discord_bot.py with the real job list.
    """
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


def fake_review(job: JobPosting) -> str:
    """
    Placeholder review used until review_posting() from issue #9 exists.
    Swap it out by passing review_posting as `review_fn`.
    """
    return (
        f"**Review of {job.title} at {job.company}**\n"
        "(Placeholder review: the real AI review is not hooked up yet.)"
    )


def build_review_message(
    user_id: int,
    number: int,
    review_fn: Callable[[JobPosting], str] = fake_review,
) -> str:
    """Return the text to send for `/review <number>`."""
    try:
        job = get_job(user_id, number)
    except NoSearchResultsError:
        return "You haven't searched yet. Use /search first, then /review <number>."
    except InvalidJobNumberError as err:
        return (
            f"Job {err.number} isn't in your list. "
            f"Pick a number from 1 to {err.total}."
        )

    message = review_fn(job)
    if len(message) > DISCORD_MESSAGE_LIMIT:
        message = message[: DISCORD_MESSAGE_LIMIT - 3] + "..."
    return message


async def handle_review(
    interaction,
    number: int,
    review_fn: Callable[[JobPosting], str] = fake_review,
) -> None:
    """Respond to a /review interaction."""
    # The real AI review can take longer than Discord's 3-second limit,
    # so acknowledge the command first and send the answer as a follow-up.
    await interaction.response.defer()
    message = build_review_message(interaction.user.id, number, review_fn)
    await interaction.followup.send(message)
