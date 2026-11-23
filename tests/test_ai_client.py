from types import SimpleNamespace
from unittest.mock import patch

from google.genai import errors
from src.core.ai_client import ask_ai


def test_429_waits_and_retries_once():
    calls = []

    def fake_generate_content(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise errors.APIError(
                429, {"error": {"message": "Too many requests"}}
            )
        return SimpleNamespace(text="fake review")

    fake_client = SimpleNamespace(
        models=SimpleNamespace(generate_content=fake_generate_content)
    )

    with patch("src.core.ai_client.time.sleep") as pause:
        result = ask_ai("test prompt", client=fake_client)

    assert result == "fake review"
    assert len(calls) == 2
    assert [call.args[0] for call in pause.call_args_list] == [6, 12]


def test_503_waits_and_retries_once():
    calls = []

    def fake_generate_content(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise errors.APIError(
                503, {"error": {"message": "Service unavailable"}}
            )
        return SimpleNamespace(text="fake review")

    fake_client = SimpleNamespace(
        models=SimpleNamespace(generate_content=fake_generate_content)
    )

    with patch("src.core.ai_client.time.sleep"):
        result = ask_ai("test prompt", client=fake_client)

    assert result == "fake review"
    assert len(calls) == 2