from unittest.mock import patch

from src.core.job_search import search_jobs
from src.core.models import SearchRequest


def test_search_without_salary_returns_results():
    frame = [
        {
            "title": "Software Engineer",
            "company": "Acme",
            "location": "Philadelphia",
            "job_url": "https://example.com/job",
            "description": "Build software.",
            "site": "indeed",
            "date_posted": "2026-11-22",
        }
    ]

    import pandas as pd

    with patch("src.core.job_search.scrape_jobs", return_value=pd.DataFrame(frame)):
        jobs = search_jobs(SearchRequest(search_term="software engineer"))

    assert len(jobs) == 1
    assert jobs[0].title == "Software Engineer"
