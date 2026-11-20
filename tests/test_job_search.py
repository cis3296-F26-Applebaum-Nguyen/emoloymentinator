import pytest

from core.job_search import (
    CSV_FIELDS,
    JobSearchError,
    load_results,
    search_jobs,
)
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


def test_ai_params_go_to_jobspy_but_filters_do_not(tmp_path):
    seen = {}

    def fake_scraper(**kwargs):
        seen.update(kwargs)
        return FakeDataFrame([])

    search_jobs(
        make_request(min_salary=50000, skills=["Python"]),
        scraper=fake_scraper,
        csv_path=tmp_path / "jobs.csv",
    )

    assert seen["search_term"] == "software engineer"
    assert seen["location"] == "Florida"
    assert set(seen["site_name"]) >= {"linkedin", "indeed", "glassdoor", "zip_recruiter"}
    assert seen["results_wanted"] == 20
    assert seen["enforce_annual_salary"] is True
    assert "skills" not in seen
    assert "min_salary_annual" not in seen


def test_site_names_are_normalized(tmp_path):
    seen = {}

    def fake_scraper(**kwargs):
        seen.update(kwargs)
        return FakeDataFrame([])

    search_jobs(
        make_request(),
        scraper=fake_scraper,
        fixed_settings={"site_name": ["ziprecruiter", "indeed", "indeed"]},
        csv_path=tmp_path / "jobs.csv",
    )

    assert seen["site_name"] == ["zip_recruiter", "indeed"]


def test_unknown_site_names_raise_a_clear_error(tmp_path):
    with pytest.raises(JobSearchError, match="monster"):
        search_jobs(
            make_request(),
            scraper=lambda **_: FakeDataFrame([]),
            fixed_settings={"site_name": ["monster"]},
            csv_path=tmp_path / "jobs.csv",
        )


def test_jobspy_rows_become_job_postings(tmp_path):
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
        make_request(),
        scraper=lambda **_: FakeDataFrame([row]),
        csv_path=tmp_path / "jobs.csv",
    )

    assert len(postings) == 1
    assert postings[0].title == "Software Engineer"
    assert postings[0].company == "Acme"
    assert postings[0].job_url == "https://example.com/jobs/1"
    assert "60,000" in postings[0].salary


def test_nan_cells_become_empty_values(tmp_path):
    postings = search_jobs(
        make_request(),
        scraper=lambda **_: FakeDataFrame([{
            "title": float("nan"),
            "company": None,
            "description": float("nan"),
        }]),
        csv_path=tmp_path / "jobs.csv",
    )

    assert postings[0].title == "Untitled role"
    assert postings[0].company == "Unknown company"
    assert postings[0].description == ""


def test_min_salary_uses_lower_bound_of_a_range(tmp_path):
    rows = [
        {"title": "RangeBelow", "min_amount": 45000, "max_amount": 90000},
        {"title": "RangeAbove", "min_amount": 55000, "max_amount": 90000},
        {"title": "SingleAmount", "max_amount": 60000},
        {"title": "Unknown"},
    ]

    postings = search_jobs(
        make_request(min_salary=50000),
        scraper=lambda **_: FakeDataFrame(rows),
        csv_path=tmp_path / "jobs.csv",
    )

    assert [posting.title for posting in postings] == ["RangeAbove", "SingleAmount"]


def test_skills_filter_matches_case_insensitively(tmp_path):
    rows = [
        {"title": "Python role", "description": "We use Python daily."},
        {"title": "Java role", "description": "We use Java daily."},
        {"title": "No description"},
    ]

    postings = search_jobs(
        make_request(skills=["python"]),
        scraper=lambda **_: FakeDataFrame(rows),
        csv_path=tmp_path / "jobs.csv",
    )

    assert [posting.title for posting in postings] == ["Python role"]


def test_none_results_are_an_empty_list(tmp_path):
    assert search_jobs(
        make_request(), scraper=lambda **_: None, csv_path=tmp_path / "jobs.csv"
    ) == []


def test_scraper_failure_becomes_job_search_error(tmp_path):
    def broken(**kwargs):
        raise RuntimeError("board blocked us")

    with pytest.raises(JobSearchError):
        search_jobs(
            make_request(), scraper=broken, csv_path=tmp_path / "jobs.csv"
        )


def test_results_are_saved_and_overwritten(tmp_path):
    path = tmp_path / "jobs.csv"

    search_jobs(
        make_request(),
        scraper=lambda **_: FakeDataFrame([{"title": "First", "company": "A"}]),
        csv_path=path,
    )
    assert [posting.title for posting in load_results(path)] == ["First"]

    search_jobs(
        make_request(),
        scraper=lambda **_: FakeDataFrame([{"title": "Second", "company": "B"}]),
        csv_path=path,
    )
    assert [posting.title for posting in load_results(path)] == ["Second"]
    assert path.read_text(encoding="utf-8").splitlines()[0] == ",".join(CSV_FIELDS)
