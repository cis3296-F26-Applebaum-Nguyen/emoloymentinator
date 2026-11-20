import json  

# Checks the AI's JSON answer and returns a clean copy, or raises ValueError.

# The job_type values our prompt allows. Check these against the JobSpy README
# and remove any that JobSpy doesn't actually accept.
ALLOWED_JOB_TYPES = {"fulltime", "parttime", "contract", "temporary",
                     "internship", "perdiem", "volunteer", "other"}


# ---------- Small helper functions, one per type of check ----------

def _optional_text(name, value):
    """Value must be text, or None (meaning 'user didn't say')."""
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{name} must be text or null")
    return value


def _optional_positive_int(name, value):
    """Value must be a whole number above 0, or None."""
    if value is None:
        return None
    # In Python, True and False count as the numbers 1 and 0,
    # so we must reject them explicitly
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive whole number or null")
    return value


def _optional_bool(name, value):
    """Value must be true/false, or None."""
    if value is not None and not isinstance(value, bool):
        raise ValueError(f"{name} must be true, false, or null")
    return value


# ---------- The main check ----------

def validate_parsed_request(data):
    """Checks the AI's answer. Returns a clean copy, or raises ValueError."""
    if not isinstance(data, dict):
        raise ValueError("Response must be a JSON object")

    if not isinstance(data.get("is_job_search"), bool):
        raise ValueError("is_job_search must be true or false")

    # If the AI says this isn't a job search, there is nothing else to check
    if data["is_job_search"] is False:
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

    # search_term is the only required field
    search_term = params.get("search_term")
    if not isinstance(search_term, str) or search_term.strip() == "":
        raise ValueError("search_term must be non-empty text")

    job_type = params.get("job_type")
    if job_type is not None and job_type not in ALLOWED_JOB_TYPES:
        raise ValueError(f"job_type '{job_type}' is not allowed")

    skills = filters.get("skills")
    if not isinstance(skills, list) or not all(isinstance(s, str) for s in skills):
        raise ValueError("skills must be a list of text values")

    # Build a NEW dictionary with only the keys we expect.
    # Anything extra the model added is left behind.
    return {
        "is_job_search": True,
        "error": None,
        "jobspy_params": {
            "search_term": search_term.strip(),
            "location": _optional_text("location", params.get("location")),
            "distance": _optional_positive_int("distance", params.get("distance")),
            "job_type": job_type,
            "is_remote": _optional_bool("is_remote", params.get("is_remote")),
            "hours_old": _optional_positive_int("hours_old", params.get("hours_old")),
            "country_indeed": _optional_text("country_indeed", params.get("country_indeed")),
        },
        "post_filters": {
            "min_salary_annual": _optional_positive_int(
                "min_salary_annual", filters.get("min_salary_annual")),
            "skills": skills,
        },
    }
    
def parse_json_reply(reply_text):
    """Turns the AI's raw text into a dictionary, or raises ValueError."""
    if reply_text is None:
        raise ValueError("The AI returned no text")

    # Remove extra spaces, then remove code fences if the model added them
    cleaned = reply_text.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    # If this isn't valid JSON it raises JSONDecodeError, which is a kind of ValueError
    return json.loads(cleaned)