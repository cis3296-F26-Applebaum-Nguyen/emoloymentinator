"""Creates and configures the Discord bot."""

import discord
from discord import app_commands
from discord.ext import commands

from .commands import handle_review, handle_search


def create_bot(parse_fn, search_fn, save_fn, review_fn) -> commands.Bot:
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user}")

    @bot.tree.command(name="search", description="Search for job listings")
    @app_commands.describe(query="Describe the job you are looking for")
    async def search(interaction: discord.Interaction, query: str):
        await handle_search(
            interaction,
            query,
            parse_fn=parse_fn,
            search_fn=search_fn,
            save_fn=save_fn,
        )

    @bot.tree.command(name="review", description="Get an AI review of a job from your last search")
    @app_commands.describe(number="The job number from your last /search list")
    async def review(interaction: discord.Interaction, number: int):
        await handle_review(interaction, number, review_fn)

    async def setup_hook():
        synced = await bot.tree.sync()
        print(f"Globally synced {len(synced)} command(s)")

    bot.setup_hook = setup_hook
    return bot
