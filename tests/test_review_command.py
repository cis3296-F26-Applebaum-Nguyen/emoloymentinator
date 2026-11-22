import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.commands import build_review_message, handle_review
from src.core.models import JobPosting
from src.core.result_store import (
    InvalidJobNumberError,
    NoSearchResultsError,
    clear_results,
    get_job,
    save_results,
)


@pytest.fixture(autouse=True)
def empty_store():
    clear_results()
    yield
    clear_results()


def make_jobs(count=3):
    return [JobPosting(title=f"Job {i}", company=f"Co {i}") for i in range(1, count + 1)]


def echo_review(job):
    return f"review:{job.title}"


# --- result store ---

def test_save_and_get_job_is_one_based():
    jobs = make_jobs()
    save_results(1, jobs)
    assert get_job(1, 1) is jobs[0]
    assert get_job(1, 3) is jobs[2]


def test_new_search_replaces_old_results():
    save_results(1, make_jobs(3))
    save_results(1, make_jobs(1))
    with pytest.raises(InvalidJobNumberError):
        get_job(1, 2)


def test_results_are_kept_separate_per_user():
    save_results(1, [JobPosting(title="Mine", company="A")])
    save_results(2, [JobPosting(title="Theirs", company="B")])
    assert get_job(1, 1).title == "Mine"
    assert get_job(2, 1).title == "Theirs"


def test_get_job_without_search_raises():
    with pytest.raises(NoSearchResultsError):
        get_job(1, 1)


@pytest.mark.parametrize("number", [0, -1, 4])
def test_get_job_bad_number_raises(number):
    save_results(1, make_jobs(3))
    with pytest.raises(InvalidJobNumberError) as err:
        get_job(1, number)
    assert err.value.total == 3


# --- message building ---

def test_review_message_uses_review_function():
    save_results(1, make_jobs())
    assert build_review_message(1, 2, echo_review) == "review:Job 2"


def test_review_message_no_search():
    assert "/search" in build_review_message(1, 1, echo_review)


def test_review_message_bad_number_names_valid_range():
    save_results(1, make_jobs(3))
    assert "1 to 3" in build_review_message(1, 9, echo_review)


def test_default_fake_review_mentions_job():
    save_results(1, make_jobs())
    assert "Job 1" in build_review_message(1, 1)


def test_long_review_is_truncated_to_discord_limit():
    save_results(1, make_jobs())
    message = build_review_message(1, 1, lambda job: "x" * 5000)
    assert len(message) <= 2000


# --- /search saves results so /review can find them ---

def test_search_then_review_finds_saved_job():
    from src.bot.discord_bot import search

    search_interaction = MagicMock()
    search_interaction.user.id = 7
    search_interaction.response.send_message = AsyncMock()
    asyncio.run(search.callback(search_interaction, "python"))

    assert "python" in get_job(7, 1).title
    assert get_job(7, 5).company
    assert "1 to 5" in build_review_message(7, 9, echo_review)


def test_blank_search_does_not_save_results():
    from src.bot.discord_bot import search

    interaction = MagicMock()
    interaction.user.id = 8
    interaction.response.send_message = AsyncMock()
    asyncio.run(search.callback(interaction, "  "))

    with pytest.raises(NoSearchResultsError):
        get_job(8, 1)


# --- slash command handler ---

def test_handle_review_defers_then_sends_followup():
    save_results(42, make_jobs())
    interaction = MagicMock()
    interaction.user.id = 42
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()

    asyncio.run(handle_review(interaction, 3, echo_review))

    interaction.response.defer.assert_awaited_once()
    interaction.followup.send.assert_awaited_once_with("review:Job 3")
