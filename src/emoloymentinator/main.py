"""Starts Employmentinator and connects bot and core components."""

from functools import partial
from pathlib import Path
import sys

# Running this file directly does not automatically put the repository root
# on Python's import path.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from src.core.ai_client import ask_ai
from src.core.config import load_config
from src.core.job_review import review_posting
from src.core.job_search import search_jobs_async
from src.core.query_parser import parse_search_request
from src.core.result_store import save_results
from src.bot.bot import create_bot


def main() -> None:
    settings = load_config()
    if not settings.discord_token:
        raise RuntimeError(
            "DISCORD_BOT_TOKEN is not set. "
            "Please configure your Discord bot token."
        )
    if not settings.ai_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    ai = partial(
        ask_ai,
        api_key=settings.ai_key,
        model=settings.ai_model,
    )
    parser = partial(parse_search_request, ai_fn=ai)
    reviewer = partial(review_posting, ask_ai=ai)

    bot = create_bot(parser, search_jobs_async, save_results, reviewer)
    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
