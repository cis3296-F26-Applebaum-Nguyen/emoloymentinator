"""
Runs a JobSpy scrape from a validated SearchRequest.

This module is the boundary between our validated search parameters and
JobSpy. It knows about JobSpy's DataFrame-ish results, but it does not know
anything about Discord.
"""
from __future__ import annotations

import csv
import math
import os
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from core.models import JobPosting, SearchRequest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_CSV_PATH = PROJECT_ROOT / "data" / "jobs.csv"

# Exact names accepted by python-jobspy 1.4.1.
ALLOWED_SITES = (
    "linkedin", "indeed", "zip_recruiter", "glassdoor",
    "google", "bayt", "naukri", "bdjobs", "hellowork",
)
SITE_ALIASES = {"ziprecruiter": "zip_recruiter"}

# More than one board, but no invalid names. Leave LinkedIn out by setting
# JOBSPY_SITES=indeed,glassdoor,zip_recruiter in .env.local if you prefer.
DEFAULT_SITES = ["linkedin", "indeed", "glassdoor", "zip_recruiter"]

# Developer-controlled settings. The AI never supplies these, because the
# validated params are merged first and these fixed values are merged last.
DEFAULT_FIXED_SETTINGS: dict[str, Any] = {
    "site_name": DEFAULT_SITES,
    "results_wanted": 20,
    "enforce_annual_salary": True,
    "verbose": 0,
}

CSV_FIELDS = ["title", "company", "location", "job_url", "site", "salary", "description"]

Scraper = Callable[..., Any]


class JobSearchError(Exception):
    """The scrape failed. The message is safe to show the user."""


def normalize_sites(values: Iterable[str]) -> list[str]:
    """Clean up site names and reject values JobSpy cannot understand."""
    normalized: list[str] = []
    for value in values:
        site = str(value).strip().lower().replace("-", "_")
        site = SITE_ALIASES.get(site, site)
        if site not in ALLOWED_SITES:
            raise JobSearchError(
                f"Unsupported job board '{value}'. "
                f"Allowed boards: {', '.join(ALLOWED_SITES)}."
            )
        if site not in normalized:
            normalized.append(site)
    return normalized


def _fixed_settings() -> dict[str, Any]:
    """Build fixed settings, allowing an env override for the board list."""
    settings = dict(DEFAULT_FIXED_SETTINGS)
    raw_sites = os.getenv("JOBSPY_SITES")
    if raw_sites:
        settings["site_name"] = normalize_sites(raw_sites.split(","))
    else:
        settings["site_name"] = list(DEFAULT_SITES)
    return settings


def _default_scraper(**kwargs: Any) -> Any:
    """Import JobSpy only when we actually need it, so tests don't require it."""
    try:
        from jobspy import scrape_jobs
    except ImportError as exc:  # pragma: no cover - depends on local install
        raise JobSearchError(
            "JobSpy is not installed. Add python-jobspy to requirements.txt."
        ) from exc
    return scrape_jobs(**kwargs)


def _is_missing(value: Any) -> bool:
    """JobSpy uses NaN for empty cells; treat those like None."""
    if value is None:
        return True
    if isinstance(value, bool):
        return False
    if isinstance(value, float) and math.isnan(value):
        return True
    return str(value).strip().lower() in {"", "nan", "none", "nat"}


def _as_number(value: Any) -> float | None:
    """Return a usable number, or None for missing/invalid values."""
    if _is_missing(value) or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) else number


def _text(row: Mapping[str, Any], key: str, default: str = "") -> str:
    """Pull a display-safe string out of a JobSpy row."""
    value = row.get(key)
    if _is_missing(value):
        return default
    if isinstance(value, (list, tuple, set)):
        text = " ".join(str(item) for item in value).strip()
    else:
        text = str(value).strip()
    return text or default


def _salary(row: Mapping[str, Any]) -> str | None:
    """Build a short salary label from JobSpy's amount columns."""
    low = _as_number(row.get("min_amount"))
    high = _as_number(row.get("max_amount"))
    if low is None and high is None:
        return None

    currency = _text(row, "currency", "USD")

    def money(amount: float) -> str:
        return f"{amount:,.0f}"

    if low is not None and high is not None and low != high:
        return f"{currency} {money(low)}–{money(high)}"
    amount = low if low is not None else high
    return f"{currency} {money(amount)}"


def _records(raw: Any) -> list[dict[str, Any]]:
    """Accept a pandas DataFrame, a mapping, or a list of mappings."""
    if raw is None:
        return []
    if hasattr(raw, "to_dict"):
        rows = raw.to_dict("records")
    elif isinstance(raw, Mapping):
        rows = [raw]
    else:
        rows = list(raw)
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _salary_lower_bound(row: Mapping[str, Any]) -> float | None:
    """Use the stated minimum; when only one amount exists, use that amount."""
    low = _as_number(row.get("min_amount"))
    if low is not None:
        return low
    return _as_number(row.get("max_amount"))


def _min_salary_ok(row: Mapping[str, Any], minimum: int | None) -> bool:
    """A posting passes when its lower bound reaches the requested minimum."""
    if minimum is None:
        return True
    lower_bound = _salary_lower_bound(row)
    return lower_bound is not None and lower_bound >= minimum


def _skills_ok(row: Mapping[str, Any], skills: list[str]) -> bool:
    """Keep postings that mention at least one requested skill.

    JobSpy sometimes fills a `skills` column; otherwise we search the
    description and title. Matching is case-insensitive.
    """
    if not skills:
        return True
    haystack = " ".join([
        _text(row, "description"),
        _text(row, "skills"),
        _text(row, "title"),
    ]).lower()
    return any(skill.lower() in haystack for skill in skills)


def _to_posting(row: Mapping[str, Any]) -> JobPosting:
    return JobPosting(
        title=_text(row, "title", "Untitled role"),
        company=_text(row, "company", "Unknown company"),
        location=_text(row, "location", "Location not listed"),
        job_url=_text(row, "job_url") or _text(row, "job_url_direct"),
        site=_text(row, "site"),
        salary=_salary(row),
        description=_text(row, "description"),
    )


def save_results(
    postings: Iterable[JobPosting],
    path: Path | str = RESULTS_CSV_PATH,
) -> Path:
    """Overwrite the CSV with the results from the latest search."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for posting in postings:
            writer.writerow({field: getattr(posting, field) for field in CSV_FIELDS})
    return target


def load_results(path: Path | str = RESULTS_CSV_PATH) -> list[JobPosting]:
    """Read the last saved search back into JobPosting objects."""
    target = Path(path)
    if not target.exists():
        return []
    with target.open(newline="", encoding="utf-8") as handle:
        return [JobPosting(**row) for row in csv.DictReader(handle)]


def search_jobs(
    request: SearchRequest,
    *,
    scraper: Scraper | None = None,
    fixed_settings: Mapping[str, Any] | None = None,
    csv_path: Path | str = RESULTS_CSV_PATH,
) -> list[JobPosting]:
    """Search JobSpy, apply our filters, save the results, and return them."""
    scrape = scraper or _default_scraper
    settings = dict(fixed_settings) if fixed_settings is not None else _fixed_settings()
    if "site_name" in settings:
        settings["site_name"] = normalize_sites(settings["site_name"])
    kwargs = request.jobspy.to_scrape_kwargs(settings)

    try:
        raw = scrape(**kwargs)
    except JobSearchError:
        raise
    except Exception as exc:
        raise JobSearchError("The job search failed. Please try again.") from exc

    rows = _records(raw)
    kept = [
        row for row in rows
        if _min_salary_ok(row, request.filters.min_salary_annual)
        and _skills_ok(row, request.filters.skills)
    ]
    postings = [_to_posting(row) for row in kept]

    try:
        save_results(postings, csv_path)
    except OSError as exc:
        raise JobSearchError("Could not save the job results to CSV.") from exc

    return postings
