# tests/test_query_parser.py
import pytest
from core import query_parser
from core.query_parser import parse_search_request, SearchParseError


def test_valid_reply_becomes_a_search_request(monkeypatch):
    fake_reply = {
        "is_job_search": True, "error": None,
        "jobspy_params": {"search_term": "software engineer", "location": None,
                          "distance": None, "job_type": None, "is_remote": None,
                          "hours_old": None, "country_indeed": None},
        "post_filters": {"min_salary_annual": None, "skills": []},
    }
    # monkeypatch temporarily swaps in a fake translate_request, so no API call happens
    monkeypatch.setattr(query_parser, "translate_request", lambda text: fake_reply)

    request = parse_search_request("anything")
    assert request.jobspy.search_term == "software engineer"


def test_non_job_request_raises_with_the_ais_reason(monkeypatch):
    fake_reply = {"is_job_search": False, "error": "Not about jobs.",
                  "jobspy_params": None, "post_filters": None}
    monkeypatch.setattr(query_parser, "translate_request", lambda text: fake_reply)

    with pytest.raises(SearchParseError, match="Not about jobs"):
        parse_search_request("what's the weather?")


def test_broken_reply_raises_search_parse_error(monkeypatch):
    monkeypatch.setattr(query_parser, "translate_request", lambda text: {"nonsense": 1})

    with pytest.raises(SearchParseError):
        parse_search_request("find me a job")