"""
Temporarily stores job search results for each user.
Allows users to retrieve jobs for later review.
"""

from collections.abc import Sequence

from src.core.models import JobPosting

# Maps a Discord user ID to the results of that user's most recent search.
_results: dict[int, list[JobPosting]] = {}


class NoSearchResultsError(Exception):
    """The user has no saved search results."""


class InvalidJobNumberError(Exception):
    """The requested job number is outside the saved list."""

    def __init__(self, number: int, total: int):
        super().__init__(f"Job number {number} is not in the list of {total}.")
        self.number = number
        self.total = total


def save_results(user_id: int, jobs: Sequence[JobPosting]) -> None:
    """Save a user's latest search results, replacing any earlier ones."""
    _results[user_id] = list(jobs)


def get_job(user_id: int, number: int) -> JobPosting:
    """
    Return job `number` (1-based, as shown in the list) from the user's
    last search.

    Raises NoSearchResultsError if the user has not searched yet, and
    InvalidJobNumberError if the number is out of range.
    """
    jobs = _results.get(user_id)
    if not jobs:
        raise NoSearchResultsError()
    if number < 1 or number > len(jobs):
        raise InvalidJobNumberError(number, len(jobs))
    return jobs[number - 1]


def clear_results() -> None:
    """Remove all saved results (used by tests)."""
    _results.clear()
