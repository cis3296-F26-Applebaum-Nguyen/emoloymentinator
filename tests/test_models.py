from core.models import request_from_dict

# Settings your code controls (never the AI)
FIXED = {"site_name": ["indeed"], "results_wanted": 20}


def make_clean():
    """A dictionary shaped like the validator's output."""
    return {
        "is_job_search": True,
        "error": None,
        "jobspy_params": {
            "search_term": "software engineer", "location": "Florida",
            "distance": None, "job_type": None, "is_remote": None,
            "hours_old": None, "country_indeed": None,
        },
        "post_filters": {"min_salary_annual": 50000, "skills": ["Python"]},
    }


def test_fields_can_be_read_by_name():
    request = request_from_dict(make_clean())
    assert request.jobspy.search_term == "software engineer"
    assert request.filters.skills == ["Python"]


def test_none_values_are_left_out_of_jobspy_kwargs():
    kwargs = request_from_dict(make_clean()).jobspy.to_scrape_kwargs(FIXED)
    assert "distance" not in kwargs        # it was None, so it should be dropped
    assert kwargs["location"] == "Florida"


def test_fixed_settings_are_added():
    kwargs = request_from_dict(make_clean()).jobspy.to_scrape_kwargs(FIXED)
    assert kwargs["results_wanted"] == 20
    assert kwargs["site_name"] == ["indeed"]


def test_post_filters_are_not_sent_to_jobspy():
    kwargs = request_from_dict(make_clean()).jobspy.to_scrape_kwargs(FIXED)
    assert "skills" not in kwargs
    assert "min_salary_annual" not in kwargs   # JobSpy has no such parameter