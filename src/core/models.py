"""
Defines shared data structures for job searches,
job postings, and AI reviews.
"""

from dataclasses import dataclass


@dataclass
class JobPosting:
    """A single job posting from a search result."""
    title: str
    company: str
    location: str | None = None
    url: str | None = None
    description: str | None = None
