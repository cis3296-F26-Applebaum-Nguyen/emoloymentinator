"""Entry point for the Employmentinator Discord bot."""
from __future__ import annotations

import logging

import discord

from bot.formatting import format_search_results
from bot.search_command import make_handler, register_search_command
from bot.settings import discord_token, load_env, test_guild_id
from core.job_search import search_jobs
from core.query_parser import parse_search_request

LOGGER = logging.getLogger(__name__)


def create_bot() -> discord.Client:
    """Build the client and register slash commands. No network calls here."""
    intents = discord.Intents.default()
    bot = discord.Client(
        intents=intents,
        allowed_mentions=discord.AllowedMentions.none(),
    )
    tree = discord.app_commands.CommandTree(bot)

    handler = make_handler(
        parse=parse_search_request,
        search=search_jobs,
        formatter=format_search_results,
    )
    register_search_command(tree, handler=handler)

    @tree.command(name="ping", description="Check that Employmentinator is online")
    async def ping(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Pong!")

    @bot.event
    async def on_ready() -> None:
        names = [command.name for command in tree.get_commands()]
        # Syncing to one test guild is much faster than global sync while developing.
        guild_id = test_guild_id()
        try:
            if guild_id is None:
                await tree.sync()
                scope = "globally (Discord may take up to 1 hour to show them)"
            else:
                await tree.sync(guild=discord.Object(id=guild_id))
                scope = f"to guild {guild_id} (usually instant)"
        except Exception:
            LOGGER.exception("Slash command sync failed")
            print("Slash command sync FAILED - check the log above.")
        else:
            print(f"Logged in as {bot.user}; synced {names} {scope}.")

    return bot


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    load_env()
    if test_guild_id() is None:
        print("Tip: add DISCORD_GUILD_ID=<your server ID> to .env.local for instant slash-command syncing.")
    bot = create_bot()
    bot.run(discord_token())


if __name__ == "__main__":
    main()
