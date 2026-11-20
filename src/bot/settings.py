"""Local configuration for the Discord bot."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_env() -> None:
    """Load .env.local from the project root without overwriting real env vars."""
    load_dotenv(PROJECT_ROOT / ".env.local", override=False)


def discord_token() -> str:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is missing from .env.local")
    return token


def test_guild_id() -> int | None:
    """Optional guild ID for fast command syncing during development."""
    raw = os.getenv("DISCORD_GUILD_ID")
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError("DISCORD_GUILD_ID must be an integer") from exc
