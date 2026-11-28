"""Matches job locations against the place the user searched for."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

import us

from .models import JobPosting, SearchRequest

AREA_PROMPT = (Path(__file__).parent / "prompts" / "area_resolver_prompt.txt").read_text(encoding="utf-8")
COUNTRY_WORDS = {"usa", "us", "u.s.", "u.s.a.", "united states"}

EXACT = 4
REMOTE = 3
SAME_STATE = 2
UNKNOWN = 1
OTHER = 0


@dataclass(frozen=True)
class Place:
    city: str | None = None
    state: str | None = None


def state_abbr(text: str) -> str | None:
    text = text.strip().rstrip(".")
    if not text.replace(" ", "").isalpha():
        return None
    state = us.states.lookup(text)
    return state.abbr if state else None


def parse_place(text: str | None) -> Place | None:
    if text is None or str(text).strip().lower() in {"", "nan", "none"}:
        return None

    parts = [part.strip() for part in str(text).split(",") if part.strip()]
    while parts and parts[-1].lower() in COUNTRY_WORDS:
        parts.pop()
    if not parts:
        return None

    if len(parts) > 1:
        state = state_abbr(parts[-1])
        return Place(parts[-2], state) if state else Place(parts[0])

    if state := state_abbr(parts[0]):
        return Place(state=state)

    *city, last = parts[0].split()
    if city and last.isupper() and state_abbr(last):
        return Place(" ".join(city), state_abbr(last))
    return Place(parts[0])


def classify_request_location(location: str | None) -> str:
    place = parse_place(location)
    if place is None:
        return "none"
    if place.state:
        return "city_state" if place.city else "state"
    return "area"


def location_filter_applies(request: SearchRequest) -> bool:
    country = (request.country_indeed or "usa").strip().lower()
    return classify_request_location(request.location) != "none" and country in COUNTRY_WORDS


def search_targets(request: SearchRequest) -> list[Place]:
    if classify_request_location(request.location) == "area":
        places = map(parse_place, request.area_places)
    else:
        places = [parse_place(request.location)]
    return [place for place in places if place]


def same_city(a: str | None, b: str | None) -> bool:
    def normalize(text):
        return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()

    return bool(a and b) and normalize(a) == normalize(b)


def score_job(job: JobPosting, request: SearchRequest) -> int:
    if job.is_remote or "remote" in (job.location or "").lower():
        return REMOTE

    have = parse_place(job.location)
    if have is None or have.state is None:
        return UNKNOWN

    score = OTHER
    for want in search_targets(request):
        if want.state == have.state:
            if want.city is None or same_city(want.city, have.city):
                return EXACT
            score = SAME_STATE
    return score


def found_place(request: SearchRequest, jobs: list[JobPosting]) -> bool:
    return any(score_job(job, request) == EXACT for job in jobs)


def refine_jobs(jobs: list[JobPosting], request: SearchRequest, limit: int = 20) -> list[JobPosting]:
    if not location_filter_applies(request):
        return jobs[:limit]

    ranked = sorted(jobs, key=lambda job: score_job(job, request), reverse=True)
    if found_place(request, ranked):
        ranked = [job for job in ranked if score_job(job, request) >= REMOTE]
    return ranked[:limit]


def location_notice(request: SearchRequest, jobs: list[JobPosting]) -> str | None:
    if not jobs or not location_filter_applies(request) or found_place(request, jobs):
        return None
    return f"I couldn't find jobs in {request.location}, but here are some other results you may like."


def resolve_area(text: str, ai_fn) -> list[str]:
    for _ in range(2):
        try:
            reply = ai_fn(f"{AREA_PROMPT}\n\n<area>\n{text}\n</area>")
            places = json.loads(reply.replace("```json", "").replace("```", ""))["places"]
            if not isinstance(places, list):
                continue
        except Exception:
            continue

        found = [parse_place(item) for item in places if isinstance(item, str)]
        return [f"{p.city}, {p.state}" for p in found if p and p.city and p.state][:15]
    return []
