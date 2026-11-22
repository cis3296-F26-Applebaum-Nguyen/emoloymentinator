from src.core.models import JobPosting, JobReview, SearchRequest


def test_search_request_fields():
    request = SearchRequest(search_term="software engineer", location="Florida")
    assert request.search_term == "software engineer"
    assert request.location == "Florida"


def test_job_posting_fields():
    job = JobPosting(title="Engineer", company="Acme")
    assert job.title == "Engineer"


def test_job_review_fields():
    review = JobReview(summary="Good role", skills=["Python"])
    assert review.summary == "Good role"
    assert review.skills == ["Python"]
