"""Compatibility entry point for the Discord bot."""

from .discord_bot import bot, main

__all__ = ["bot", "main"]


if __name__ == "__main__":
    main()