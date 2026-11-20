import pytest

from core.job_search import JobSearchError, search_jobs
from core.models import JobSpyParams, PostFilters, SearchRequest


class FakeDataFrame:
    """Just enough of a pandas DataFrame for our adapter."""

    def __init__(self, rows):
        self.rows = rows

    def to_dict(self, orient):
        assert orient == "records"
        return self.rows


def make_request(min_salary=None, skills=None):
    return SearchRequest(
        jobspy=JobSpyParams(search_term="software engineer", location="Florida"),
        filters=PostFilters(min_salary_annual=min_salary, skills=skills or []),
    )


def test_ai_params_go_to_jobspy_but_filters_do_not():
    seen = {}

    def fake_scraper(**kwargs):
        seen.update(kwargs)
        return FakeDataFrame([])

    search_jobs(make_request(min_salary=50000, skills=["Python"]), scraper=fake_scraper)

    assert seen["search_term"] == "software engineer"
    assert seen["location"] == "Florida"
    assert seen["site_name"] == ["indeed"]
    assert seen["results_wanted"] == 20
    assert seen["enforce_annual_salary"] is True
    assert "skills" not in seen
    assert "min_salary_annual" not in seen


def test_jobspy_rows_become_job_postings():
    row = {
        "title": "Software Engineer",
        "company": "Acme",
        "location": "Orlando, FL",
        "job_url": "https://example.com/jobs/1",
        "site": "indeed",
        "min_amount": 60000,
        "max_amount": 80000,
        "currency": "USD",
        "description": "Work with Python.",
    }

    postings = search_jobs(
        make_request(), scraper=lambda **_: FakeDataFrame([row])
    )

    assert len(postings) == 1
    assert postings[0].title == "Software Engineer"
    assert postings[0].company == "Acme"
    assert postings[0].job_url == "https://example.com/jobs/1"
    assert "60,000" in postings[0].salary


def test_min_salary_filter_drops_low_and_unknown_salaries():
    rows = [
        {"title": "Low", "min_amount": 40000, "max_amount": 45000},
        {"title": "High", "min_amount": 60000, "max_amount": 80000},
        {"title": "Unknown"},
    ]

    postings = search_jobs(
        make_request(min_salary=50000), scraper=lambda **_: FakeDataFrame(rows)
    )

    assert [posting.title for posting in postings] == ["High"]


def test_skills_filter_matches_case_insensitively():
    rows = [
        {"title": "Python role", "description": "We use Python daily."},
        {"title": "Java role", "description": "We use Java daily."},
        {"title": "No description"},
    ]

    postings = search_jobs(
        make_request(skills=["python"]), scraper=lambda **_: FakeDataFrame(rows)
    )

    assert [posting.title for posting in postings] == ["Python role"]


def test_none_results_are_an_empty_list():
    assert search_jobs(make_request(), scraper=lambda **_: None) == []


def test_scraper_failure_becomes_job_search_error():
    def broken(**kwargs):
        raise RuntimeError("board blocked us")

    with pytest.raises(JobSearchError):
        search_jobs(make_request(), scraper=broken)
