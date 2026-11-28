"""Turns natural-language searches into SearchRequest objects."""

import json
from pathlib import Path

from .ai_client import ask_ai
from .location import classify_request_location, resolve_area
from .models import SearchRequest


SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "query_parser_prompt.txt").read_text(
    encoding="utf-8"
)


class SearchParseError(Exception):
    """A plain-language search could not be parsed."""


def parse_json_reply(reply_text: str | None) -> dict:
    if reply_text is None:
        raise ValueError("The AI returned no text")
    cleaned = reply_text.strip().replace("```json", "").replace("```", "").strip()
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("Response must be a JSON object")
    return data


def validate_parsed_request(data: dict) -> dict:
    if not isinstance(data.get("is_job_search"), bool):
        raise ValueError("is_job_search must be true or false")

    if not data["is_job_search"]:
        return {
            "is_job_search": False,
            "error": data.get("error") or "The request is not about searching for jobs.",
            "jobspy_params": None,
            "post_filters": None,
        }

    params = data.get("jobspy_params")
    filters = data.get("post_filters")
    if not isinstance(params, dict) or not isinstance(filters, dict):
        raise ValueError("jobspy_params and post_filters must be objects")

    search_term = params.get("search_term")
    if not isinstance(search_term, str) or not search_term.strip():
        raise ValueError("search_term must be non-empty text")

    allowed_types = {
        "fulltime", "parttime", "contract", "temporary", "internship",
        "perdiem", "volunteer", "other",
    }
    job_type = params.get("job_type")
    if job_type is not None and job_type not in allowed_types:
        raise ValueError("Unknown job_type")

    def optional_text(name: str, value):
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{name} must be text or null")
        return value

    def optional_positive_int(name: str, value):
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer or null")
        return value

    is_remote = params.get("is_remote")
    if is_remote is not None and not isinstance(is_remote, bool):
        raise ValueError("is_remote must be true, false, or null")

    skills = filters.get("skills")
    if not isinstance(skills, list) or not all(isinstance(skill, str) for skill in skills):
        raise ValueError("skills must be a list of text values")

    return {
        "is_job_search": True,
        "error": None,
        "jobspy_params": {
            "search_term": search_term.strip(),
            "location": optional_text("location", params.get("location")),
            "distance": optional_positive_int("distance", params.get("distance")),
            "job_type": job_type,
            "is_remote": is_remote,
            "hours_old": optional_positive_int("hours_old", params.get("hours_old")),
            "country_indeed": optional_text("country_indeed", params.get("country_indeed")),
        },
        "post_filters": {
            "min_salary_annual": optional_positive_int(
                "min_salary_annual", filters.get("min_salary_annual")
            ),
            "skills": skills,
        },
    }


def translate_request(user_text: str, ai_fn=ask_ai) -> dict:
    prompt = f"{SYSTEM_PROMPT}\n\n<user_request>\n{user_text}\n</user_request>"
    return parse_json_reply(ai_fn(prompt))


def parse_search_request(user_text: str, ai_fn=ask_ai) -> SearchRequest:
    for attempt in range(2):
        try:
            raw = translate_request(user_text, ai_fn)
            clean = validate_parsed_request(raw)
            if not clean["is_job_search"]:
                raise SearchParseError(clean["error"])

            params = clean["jobspy_params"]
            filters = clean["post_filters"]
            request = SearchRequest(
                search_term=params["search_term"],
                location=params["location"],
                distance=params["distance"],
                job_type=params["job_type"],
                is_remote=params["is_remote"],
                hours_old=params["hours_old"],
                country_indeed=params["country_indeed"],
                min_salary_annual=filters["min_salary_annual"],
                skills=filters["skills"],
            )
            if request.location is not None and classify_request_location(request.location) == "area":
                request.area_places = resolve_area(request.location, ai_fn)
            return request
        except SearchParseError:
            raise
        except (ValueError, json.JSONDecodeError):
            if attempt == 1:
                raise SearchParseError(
                    "I couldn't understand that search. Try including a job title."
                )
