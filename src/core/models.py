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


@dataclass
class JobReview:
    summary: str
    skills: list[str] = field(default_factory=list)
    cover_letter_required: bool | None = None
    tips: list[str] = field(default_factory=list)
