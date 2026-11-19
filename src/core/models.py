# Dataclasses that hold the validated search request in a usable form.
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class JobSpyParams:
    """The values that go straight into JobSpy's scrape_jobs()."""
    search_term: str                         # required: no default value
    location: Optional[str] = None           # Optional[...] = None means "may be missing"
    distance: Optional[int] = None
    job_type: Optional[str] = None
    is_remote: Optional[bool] = None
    hours_old: Optional[int] = None
    country_indeed: Optional[str] = None

    def to_scrape_kwargs(self, fixed_settings):
        """Builds the dictionary of keyword arguments for scrape_jobs()."""
        as_dict = asdict(self)  # turns this object into a plain dictionary
        # Keep only the values the user actually specified
        kwargs = {key: value for key, value in as_dict.items() if value is not None}
        # Fixed settings go last, so they always win
        return {**kwargs, **fixed_settings}


@dataclass
class PostFilters:
    """Values our own code applies AFTER JobSpy returns results."""
    min_salary_annual: Optional[int] = None
    # default_factory gives every object its own new list.
    # (Writing "= []" would share one list between all objects.)
    skills: list = field(default_factory=list)


@dataclass
class SearchRequest:
    """Holds both parts together."""
    jobspy: JobSpyParams
    filters: PostFilters


def request_from_dict(clean):
    """Converts the validator's output into a SearchRequest."""
    return SearchRequest(
        # ** unpacks a dictionary into keyword arguments, so this line is the
        # same as JobSpyParams(search_term=..., location=..., and so on)
        jobspy=JobSpyParams(**clean["jobspy_params"]),
        filters=PostFilters(**clean["post_filters"]),
    )