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
    job_type: Optional[Literal["fulltime", "parttime", "internship", "contract"]] = None
    hours_old: Optional[int] = None
    results_wanted: int = 10

# uses the jobspy library to scrape job postings, the schema is used here
# to fill in the function's parameters
def search_jobs(q: JobQuery) -> pd.DataFrame:
    df = scrape_jobs (
        site_name=["indeed", "linkedin", "zip_recruiter", "google"],
        search_term=q.search_term,
        location=q.location,
        is_remote=q.is_remote,
        job_type=q.job_type,
        results_wanted=q.results_wanted,
        hours_old=q.hours_old,
        country_indeed="USA",
    )

    return df

def export_csv(df, path="jobposting.csv"):
    cols = ["title", "company", "location", "is_remote", "min_amount", "max_amount",
            "interval", "site", "date_posted", "job_url"]
    df[[c for c in cols if c in df.columns]].to_csv(path, index=False)
    return path


'''
testing area
testing if the functions work by hardcoding the schema
and then running search jobs
'''

#stand in for gemini's parsed prompt. this is hardcoded prompt for testing
def parse_prompt(prompt: str) -> JobQuery:
    return JobQuery(
        search_term="software engineer",
        location="pennsylvania",
        is_remote="True",
        job_type="fulltime",
        hours_old="72",
        results_wanted="10",
    )

def run_search(prompt: str) -> str:
    q = parse_prompt(prompt)
    df = search_jobs(q)
    print(f"Found {len(df)} jobs")
    return export_csv(df)

if __name__ == "__main__":
    path = run_search("find me a remote job in Florida")
    print("Saved to", path)