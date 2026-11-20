import asyncio

import pytest

from bot.search_command import make_handler, register_search_command
from core.job_search import JobSearchError
from core.models import JobPosting
from core.query_parser import SearchParseError


class FakeResponse:
    def __init__(self):
        self.calls = []

    async def defer(self, **kwargs):
        self.calls.append(kwargs)


class FakeFollowup:
    def __init__(self):
        self.messages = []

    async def send(self, message):
        self.messages.append(message)


class FakeInteraction:
    def __init__(self):
        self.response = FakeResponse()
        self.followup = FakeFollowup()


class FakeTree:
    def __init__(self):
        self.commands = {}

    def command(self, **kwargs):
        def decorator(func):
            self.commands[kwargs["name"]] = func
            return func
        return decorator


FAKE_POSTING = JobPosting(
    title="Software Engineer",
    company="Acme",
    location="Orlando, FL",
    job_url="https://example.com/jobs/1",
)


def test_handler_defers_then_posts_search_results():
    interaction = FakeInteraction()
    handler = make_handler(
        parse=lambda prompt: object(),
        search=lambda request: [FAKE_POSTING],
    )

    asyncio.run(handler(interaction, "find me software dev jobs"))

    assert interaction.response.calls == [{"thinking": True}]
    assert "Software Engineer" in interaction.followup.messages[0]


def test_parse_error_is_posted_and_search_is_skipped():
    interaction = FakeInteraction()
    search_calls = []

    def broken_parse(prompt):
        raise SearchParseError("Try including a job title.")

    handler = make_handler(
        parse=broken_parse,
        search=lambda request: search_calls.append(request),
    )

    asyncio.run(handler(interaction, "find me a job"))

    assert "Try including a job title." in interaction.followup.messages[0]
    assert search_calls == []


def test_search_error_is_posted():
    interaction = FakeInteraction()

    def broken_search(request):
        raise JobSearchError("The job search failed. Please try again.")

    handler = make_handler(parse=lambda prompt: object(), search=broken_search)

    asyncio.run(handler(interaction, "anything"))

    assert "job search failed" in interaction.followup.messages[0]


def test_register_search_command_wires_the_callback():
    tree = FakeTree()
    seen = []

    async def handler(interaction, prompt):
        seen.append(prompt)

    register_search_command(tree, handler=handler)
    interaction = FakeInteraction()

    assert "search" in tree.commands
    asyncio.run(tree.commands["search"](interaction, "python jobs"))
    assert seen == ["python jobs"]
