"""
Runs a JobSpy scrape from a validated SearchRequest.

This module is the boundary between our validated search parameters and
JobSpy. It knows about JobSpy's DataFrame-ish results, but it does not know
anything about Discord.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from core.models import JobPosting, SearchRequest

# Developer-controlled settings. The AI never supplies these, because the
# validated params are merged first and these fixed values are merged last.
DEFAULT_FIXED_SETTINGS: dict[str, Any] = {
    "site_name": ["linkedin", "indeed", "glassdoor", "ziprecruiter", "monster"],
    "results_wanted": 20,
    "enforce_annual_salary": True,
    "verbose": 0,
}

Scraper = Callable[..., Any]


class JobSearchError(Exception):
    """The scrape failed. The message is safe to show the user."""


def _default_scraper(**kwargs: Any) -> Any:
    """Import JobSpy only when we actually need it, so tests don't require it."""
    try:
        from jobspy import scrape_jobs
    except ImportError as exc:  # pragma: no cover - depends on local install
        raise JobSearchError(
            "JobSpy is not installed. Add python-jobspy to requirements.txt."
        ) from exc
    return scrape_jobs(**kwargs)


def _as_number(value: Any) -> float | None:
    """Return a usable number, or None for missing/invalid values."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text(row: Mapping[str, Any], key: str, default: str = "") -> str:
    """Pull a display-safe string out of a JobSpy row."""
    value = row.get(key)
    if value is None:
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


def _min_salary_ok(row: Mapping[str, Any], minimum: int | None) -> bool:
    """A posting passes when its known salary range reaches the minimum."""
    if minimum is None:
        return True
    amounts = [amount for amount in
               (_as_number(row.get("min_amount")), _as_number(row.get("max_amount")))
               if amount is not None]
    return bool(amounts) and max(amounts) >= minimum


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


def search_jobs(
    request: SearchRequest,
    *,
    scraper: Scraper | None = None,
    fixed_settings: Mapping[str, Any] | None = None,
) -> list[JobPosting]:
    """Search JobSpy with the AI-produced parameters and apply our filters."""
    scrape = scraper or _default_scraper
    settings = DEFAULT_FIXED_SETTINGS if fixed_settings is None else fixed_settings
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
    return [_to_posting(row) for row in kept]
