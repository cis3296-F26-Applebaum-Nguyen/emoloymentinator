"""Loads application settings from environment files."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Settings:
    discord_token: str | None
    ai_key: str | None
    ai_model: str


def load_config(env_file: str = ".env") -> Settings:
    load_dotenv(".env.local")
    load_dotenv(env_file)
    return Settings(
        discord_token=os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN"),
        ai_key=os.getenv("GEMINI_API_KEY"),
        ai_model=os.getenv("AI_MODEL", "gemma-4-26b-a4b-it"),
    )
