import json
from pathlib import Path

import pytest

from src.core.location import (
    Place,
    classify_request_location,
    location_notice,
    parse_place,
    refine_jobs,
    resolve_area,
    score_job,
)
from src.core.models import JobPosting, SearchRequest

PROBE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "probe_output"


def job(location, remote=None, title="Engineer"):
    return JobPosting(title=title, company="Acme", location=location, is_remote=remote)


def request(location, **kwargs):
    return SearchRequest(search_term="engineer", location=location, **kwargs)


# --- parsing -------------------------------------------------------------


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Wayne, PA", Place("Wayne", "PA")),
        ("Wayne, PA, USA", Place("Wayne", "PA")),
        ("Wayne, Pennsylvania", Place("Wayne", "PA")),
        ("Wayne PA", Place("Wayne", "PA")),
        ("Florida", Place(state="FL")),
        ("pa", Place(state="PA")),
        ("USA", None),
        ("", None),
        (None, None),
        ("nan", None),
    ],
)
def test_parse_place(text, expected):
    assert parse_place(text) == expected


@pytest.mark.parametrize(
    "text, kind",
    [
        ("Wayne, PA", "city_state"),
        ("Florida", "state"),
        ("the Main Line", "area"),
        ("Philadelphia", "area"),
        (None, "none"),
    ],
)
def test_classify_request_location(text, kind):
    assert classify_request_location(text) == kind


# --- city + state: match on both ----------------------------------------


def test_city_state_keeps_only_exact_city_and_state():
    jobs = [
        job("Wayne, NJ, USA"),  # right city name, wrong state
        job("Wayne, PA, USA"),
        job("Philadelphia, PA"),  # right state, wrong city
    ]
    result = refine_jobs(jobs, request("Wayne, PA"))
    assert [j.location for j in result] == ["Wayne, PA, USA"]


def test_city_match_ignores_case_and_punctuation():
    assert score_job(job("WAYNE, pa"), request("Wayne, PA")) == 4
    assert score_job(job("St. Louis, MO"), request("St Louis, MO")) == 4


# --- state only: match on state -----------------------------------------


def test_state_search_keeps_any_city_in_that_state():
    jobs = [job("Tampa, FL"), job("Austin, TX"), job("Miami, FL, USA")]
    result = refine_jobs(jobs, request("Florida"))
    assert [j.location for j in result] == ["Tampa, FL", "Miami, FL, USA"]


# --- remote and unverifiable jobs ---------------------------------------


def test_remote_jobs_count_as_matches_but_rank_below_exact():
    jobs = [job("Remote", remote=True), job("Wayne, PA"), job("Austin, TX")]
    result = refine_jobs(jobs, request("Wayne, PA"))
    assert [j.location for j in result] == ["Wayne, PA", "Remote"]


def test_remote_job_alone_does_not_hide_the_fallback():
    # Found live: one remote job used to count as a match and discard the rest.
    jobs = [job("Harrisburg, PA", remote=True), job("Radnor, PA"), job("Newark, DE")]
    req = request("Wayne, PA")
    result = refine_jobs(jobs, req)
    assert len(result) == 3
    assert result[0].location == "Harrisburg, PA"  # remote ranks first
    assert location_notice(req, result) is not None


def test_remote_detected_from_location_text():
    assert score_job(job("Remote, US"), request("Wayne, PA")) == 3


def test_unverifiable_jobs_score_low_and_are_dropped_when_matches_exist():
    jobs = [job("USA"), job(None), job("Wayne, PA")]
    assert [j.location for j in refine_jobs(jobs, request("Wayne, PA"))] == ["Wayne, PA"]
    assert score_job(job("USA"), request("Wayne, PA")) == 1


# --- nothing matches: fallback + message --------------------------------


def test_no_match_falls_back_to_ranked_results_with_notice():
    jobs = [job("USA"), job("Newark, DE"), job("Radnor, PA"), job("Ashburn, VA")]
    req = request("Wayne, PA")
    result = refine_jobs(jobs, req)

    assert len(result) == 4
    assert result[0].location == "Radnor, PA"  # same state ranks first
    assert result[1].location == "USA"  # unverified next
    notice = location_notice(req, result)
    assert "couldn't find jobs in Wayne, PA" in notice
    assert "other results" in notice


def test_no_notice_when_something_matches():
    req = request("Wayne, PA")
    assert location_notice(req, [job("Wayne, PA")]) is None


def test_no_notice_without_location_or_results():
    assert location_notice(request(None), [job("Anywhere, TX")]) is None
    assert location_notice(request("Wayne, PA"), []) is None


def test_no_location_or_non_us_country_does_not_filter():
    jobs = [job("Austin, TX"), job("Toronto, ON")]
    assert refine_jobs(jobs, request(None)) == jobs
    assert refine_jobs(jobs, request("Toronto, ON", country_indeed="Canada")) == jobs


def test_limit_is_applied():
    jobs = [job(f"Wayne, PA", title=str(i)) for i in range(30)]
    assert len(refine_jobs(jobs, request("Wayne, PA"), limit=20)) == 20


# --- areas: AI resolves, then we match on the resolved places -----------


def test_area_matches_resolved_places():
    req = request("the Main Line", area_places=["Wayne, PA", "Bryn Mawr, PA"])
    jobs = [job("Austin, TX"), job("Bryn Mawr, PA"), job("Wayne, PA")]
    assert [j.location for j in refine_jobs(jobs, req)] == ["Bryn Mawr, PA", "Wayne, PA"]


def test_unresolved_area_falls_back_with_notice():
    req = request("somewhere warm")
    jobs = [job("Austin, TX"), job("Tampa, FL")]
    result = refine_jobs(jobs, req)
    assert len(result) == 2
    assert "couldn't find jobs in somewhere warm" in location_notice(req, result)


def test_resolve_area_parses_ai_reply():
    reply = '```json\n{"places": ["Wayne, PA", "Bryn Mawr, Pennsylvania", "nonsense"]}\n```'
    assert resolve_area("the Main Line", lambda prompt: reply) == ["Wayne, PA", "Bryn Mawr, PA"]


@pytest.mark.parametrize("reply", ["not json", '{"places": "x"}', "[]", None])
def test_resolve_area_bad_reply_gives_empty_list(reply):
    assert resolve_area("the Main Line", lambda prompt: reply) == []


def test_resolve_area_retries_once_after_a_failure():
    replies = iter([RuntimeError("rate limited"), '{"places": ["Wayne, PA"]}'])

    def flaky(prompt):
        reply = next(replies)
        if isinstance(reply, Exception):
            raise reply
        return reply

    assert resolve_area("the Main Line", flaky) == ["Wayne, PA"]


def test_resolve_area_does_not_retry_a_valid_empty_answer():
    calls = []

    def unknown(prompt):
        calls.append(prompt)
        return '{"places": []}'

    assert resolve_area("somewhere warm", unknown) == []
    assert len(calls) == 1


def test_resolve_area_ai_error_gives_empty_list():
    def boom(prompt):
        raise RuntimeError("rate limited")

    assert resolve_area("the Main Line", boom) == []


# --- real data captured from JobSpy (scripts/probe_location.py) ---------


def load_probe(control_id, site):
    path = PROBE_DIR / f"control_{control_id}.json"
    if not path.exists():
        pytest.skip("probe fixtures not generated")
    data = json.loads(path.read_text())
    rows = next(s["rows"] for s in data["sites"] if s["site"] == site)
    return [job(row["location"], title=row["title"]) for row in rows]


def test_real_wayne_pa_results_fall_back_with_notice():
    jobs = load_probe(1, "indeed")  # 0 exact Wayne, PA rows in the capture
    req = request("Wayne, PA")
    result = refine_jobs(jobs, req)
    assert len(result) == len(jobs)
    assert result[0].location.endswith("PA, USA")  # same-state results first
    assert location_notice(req, result) is not None


def test_real_springfield_il_results_filter_to_exact_city():
    jobs = load_probe(3, "indeed")
    result = refine_jobs(jobs, request("Springfield, IL"))
    assert result
    assert all(j.location.startswith("Springfield, IL") for j in result)
    assert len(result) < len(jobs)  # the 4 other-IL-city rows are dropped


def test_real_glassdoor_vague_usa_rows_do_not_beat_exact_matches():
    jobs = load_probe(2, "glassdoor")  # includes bare "USA" rows + 1 Wayne, NJ
    result = refine_jobs(jobs, request("Wayne, NJ"))
    assert all(j.location.startswith("Wayne, NJ") for j in result)
