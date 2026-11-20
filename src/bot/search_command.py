"""
/search command logic without a hard dependency on discord.py.

The real Discord objects are duck-typed here, so the whole workflow can be
tested with tiny fakes. discord_bot.py is the only file that imports discord.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from bot.formatting import format_error, format_search_results
from core.job_search import JobSearchError, search_jobs
from core.models import JobPosting, SearchRequest
from core.query_parser import SearchParseError, parse_search_request

LOGGER = logging.getLogger(__name__)

ParseFn = Callable[[str], SearchRequest]
SearchFn = Callable[[SearchRequest], list[JobPosting]]
Formatter = Callable[[list[JobPosting]], str]


def make_handler(
    *,
    parse: ParseFn = parse_search_request,
    search: SearchFn = search_jobs,
    formatter: Formatter = format_search_results,
) -> Callable[[Any, str], Any]:
    """Build the async callback used by the /search slash command."""

    async def handler(interaction: Any, prompt: str) -> None:
        # Scraping and AI calls take longer than Discord's 3-second ack window.
        await interaction.response.defer(thinking=True)

        try:
            request = parse(prompt)          # 1. plain English -> validated params
            postings = search(request)       # 2. params -> JobSpy results
        except SearchParseError as exc:
            message = format_error(str(exc))
        except JobSearchError as exc:
            message = format_error(str(exc))
        except Exception:
            LOGGER.exception("Unexpected failure while handling /search")
            message = format_error("Something went wrong while searching. Please try again.")
        else:
            message = formatter(postings)    # 3. results -> Discord message

        await interaction.followup.send(message)

    return handler


def register_search_command(tree: Any, *, handler: Callable[[Any, str], Any]):
    """Attach the command to a discord.py CommandTree (or a fake in tests)."""

    @tree.command(
        name="search",
        description="Search job boards using a plain-English request",
    )
    async def search(interaction: Any, prompt: str) -> None:
        await handler(interaction, prompt)

    return search
