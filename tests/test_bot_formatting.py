from bot.formatting import DISCORD_MESSAGE_LIMIT, format_error, format_search_results
from core.models import JobPosting


def make_posting(title="Software Engineer", url="https://example.com/jobs/1"):
    return JobPosting(
        title=title,
        company="Acme",
        location="Orlando, FL",
        job_url=url,
        site="indeed",
        salary="USD 60,000–80,000",
    )


def test_results_are_numbered_and_linked():
    message = format_search_results([make_posting()])

    assert "**1 job(s) found**" in message
    assert "1. **[Software Engineer](https://example.com/jobs/1)**" in message
    assert "Acme" in message
    assert "/review <number>" in message


def test_empty_results_get_a_friendly_message():
    message = format_search_results([])

    assert "No jobs matched" in message


def test_long_messages_fit_discord_limit():
    postings = [make_posting(title=f"Role {i}", url=f"https://example.com/{i}")
                for i in range(100)]

    message = format_search_results(postings)

    assert len(message) <= DISCORD_MESSAGE_LIMIT
    assert message.endswith("…")


def test_error_messages_are_prefixed():
    assert format_error("Bad prompt").startswith("⚠️")
