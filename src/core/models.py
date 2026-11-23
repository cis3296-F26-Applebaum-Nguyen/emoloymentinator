"""Shared data shapes used by the bot and core."""

from dataclasses import dataclass, field


@dataclass
class SearchRequest:
    search_term: str
    location: str | None = None
    distance: int | None = None
    job_type: str | None = None
    is_remote: bool | None = None
    hours_old: int | None = None
    country_indeed: str | None = None
    min_salary_annual: int | None = None
    skills: list[str] = field(default_factory=list)


@dataclass
class JobPosting:
    title: str
    company: str
    location: str | None = None
    url: str | None = None
    description: str | None = None
    site: str | None = None          # which job board it came from
    date_posted: str | None = None   # kept as text, so no date handling needed


@dataclass
class JobReview:
    summary: str
    skills: list[str] = field(default_factory=list)
    cover_letter_required: bool | None = None
    tips: list[str] = field(default_factory=list)
    years_experience: str | None = None
    tech_stack: list[str] = field(default_factory=list)
    other_requirements: list[str] = field(default_factory=list)