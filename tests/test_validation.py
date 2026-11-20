import pytest
from core.validation import validate_parsed_request, parse_json_reply


def test_plain_json_is_parsed():
    assert parse_json_reply('{"a": 1}') == {"a": 1}


def test_code_fences_are_removed():
    reply = '```json\n{"a": 1}\n```'  # the way models often wrap JSON
    assert parse_json_reply(reply) == {"a": 1}


def test_none_is_rejected():
    with pytest.raises(ValueError):
        parse_json_reply(None)  # response.text can be None


def test_chatty_text_is_rejected():
    with pytest.raises(ValueError):
        parse_json_reply("Sure! Here are some jobs for you.")

def make_valid():
    """Returns a fresh valid response. Each test changes just one thing."""
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


def test_valid_response_passes():
    result = validate_parsed_request(make_valid())
    assert result["jobspy_params"]["search_term"] == "software engineer"


def test_missing_search_term_is_rejected():
    data = make_valid()
    data["jobspy_params"]["search_term"] = ""
    with pytest.raises(ValueError):  # we expect the validator to raise this error
        validate_parsed_request(data)


def test_unknown_job_type_is_rejected():
    data = make_valid()
    data["jobspy_params"]["job_type"] = "entry_level"
    with pytest.raises(ValueError):
        validate_parsed_request(data)


def test_true_is_not_accepted_as_a_number():
    data = make_valid()
    data["jobspy_params"]["distance"] = True  # Python treats True as 1, so we must block it
    with pytest.raises(ValueError):
        validate_parsed_request(data)


def test_salary_as_text_is_rejected():
    data = make_valid()
    data["post_filters"]["min_salary_annual"] = "50000"  # text, not a number
    with pytest.raises(ValueError):
        validate_parsed_request(data)


def test_extra_keys_are_dropped():
    data = make_valid()
    data["jobspy_params"]["results_wanted"] = 5000  # the model sneaking in a key
    result = validate_parsed_request(data)
    assert "results_wanted" not in result["jobspy_params"]


def test_not_a_job_search_is_passed_through():
    data = {"is_job_search": False, "error": "Not about jobs.",
            "jobspy_params": None, "post_filters": None}
    result = validate_parsed_request(data)
    assert result["is_job_search"] is False