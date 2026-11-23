import pytest
from src.core.job_review import review_posting
from src.core.models import JobPosting

GOOD_RESPONSE = (
    '{"summary":"Python job","skills":["Python"],'
    '"cover_letter_required":null,"tips":[]}'
)


def test_valid_review():
    result = review_posting(JobPosting(title="Python job", company="Acme"), lambda prompt: GOOD_RESPONSE)
    assert result.summary == "Python job"
    assert result.skills == ["Python"]
    assert result.cover_letter_required is None
    assert result.tips == []


def test_code_fenced_review_is_parsed():
    response = "```json\n" + GOOD_RESPONSE + "\n```"
    result = review_posting(
        JobPosting(title="Python job", company="Acme"),
        lambda prompt: response,
    )
    assert result.summary == "Python job"


def test_broken_answer_retries_once():
    answers = iter(["{}", GOOD_RESPONSE])
    calls = []

    def fake_ai(prompt):
        calls.append(prompt)
        return next(answers)

    assert review_posting(JobPosting(title="Python job", company="Acme"), fake_ai).summary == "Python job"
    assert len(calls) == 2


def test_two_broken_answers_give_error():
    calls = []

    def fake_ai(prompt):
        calls.append(prompt)
        return "{}"

    with pytest.raises(ValueError, match="after two attempts"):
        review_posting(JobPosting(title="Python job", company="Acme"), fake_ai)

    assert len(calls) == 2