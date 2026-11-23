"""JobSpy integration for searching jobs."""

from asyncio import to_thread
import math

from .models import JobPosting, SearchRequest

try:
    from jobspy import scrape_jobs
except ImportError:
    scrape_jobs = None


class JobSearchError(Exception):
    """The scraper could not complete a search."""


def search_jobs(request: SearchRequest) -> list[JobPosting]:
    if scrape_jobs is None:
        raise JobSearchError("JobSpy is not installed.")

    kwargs = {
        "site_name": ["indeed", "linkedin", "zip_recruiter", "google", "glassdoor"],
        "search_term": request.search_term,
        "location": request.location,
        "distance": request.distance,
        "is_remote": request.is_remote,
        "job_type": request.job_type,
        "hours_old": request.hours_old,
        "results_wanted": 20,
        "country_indeed": request.country_indeed or "USA",
    }
    kwargs = {key: value for key, value in kwargs.items() if value is not None}

    frame = scrape_jobs(**kwargs)
    if frame is None or getattr(frame, "empty", False):
        return []

    def text_value(value) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text or text.lower() in {"nan", "<na>", "none"}:
            return None
        return text

    jobs = []
    for _, row in frame.iterrows():
        title = text_value(row.get("title"))
        if not title:
            continue

        if request.min_salary_annual is not None:
            amount = row.get("max_amount")
            if amount is None:
                amount = row.get("min_amount")
            if amount is None:
                continue
            try:
                amount = float(amount)
                if math.isnan(amount):
                    continue
                interval = str(row.get("interval") or "").lower()
                if interval == "hourly":
                    amount *= 2080
                elif interval == "monthly":
                    amount *= 12
            except (TypeError, ValueError):
                continue
            if amount < request.min_salary_annual:
                continue

        jobs.append(JobPosting(
            title=title,
            company=text_value(row.get("company")) or "",
            location=text_value(row.get("location")),
            url=text_value(row.get("job_url")),
            description=text_value(row.get("description")),
            site=text_value(row.get("site")),
            date_posted=text_value(row.get("date_posted")),
        ))

    return jobs


async def search_jobs_async(request: SearchRequest) -> list[JobPosting]:
    return await to_thread(search_jobs, request)
