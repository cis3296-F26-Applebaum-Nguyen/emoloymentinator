"""
Searches job boards using JobSpy.
Returns matching job postings based on search parameters.
"""

from pydantic import BaseModel
from typing import Optional, Literal
from google import genai
from jobspy import scrape_jobs
import pandas as pd

# JobQuery is our schema for the job_search function to fill 
class JobQuery(BaseModel):
    search_term: str           # Job title
    location: Optional[str] = None  # Philadlephia, New YOrk, etc.
    is_remote: bool = False
    job_type: Optional[Literal["fulltime", "parttime", "internship", "contract"]] 
    hours_old: Optional[int] = None
    results_wanted: int = 10

def search_jobs(q: JobQuery) -> pd.DataFrame:
    df = scrape_jobs (
        site_name=["indeed", "linkedin", "zip_recruiter", "google"],
        search_term=q.search_term,
        location=q.location
        is_remote=q.is_remote,
        job_type=q.job_type,
        results_wanted=q.results_wanted,
        hours=q.hours_old,
        country_indeed="USA",
    )

    return df