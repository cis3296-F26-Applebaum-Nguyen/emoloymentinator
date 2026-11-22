import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from .commands import handle_review, placeholder_results
from .formatting import format_job_list
from .search_handler import process_search_request
from ..core.result_store import save_results

load_dotenv(".env.local")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.tree.command(name="search", description="Search for job listings")
@app_commands.describe(query="Describe the job you are looking for")
async def search(interaction: discord.Interaction, query: str):
    response = process_search_request(query)

    if query.strip():
        jobs = placeholder_results(query.strip())
        save_results(interaction.user.id, jobs)
        response = format_job_list(query.strip(), jobs)

    await interaction.response.send_message(response)


@bot.tree.command(name="review", description="Get an AI review of a job from your last search")
@app_commands.describe(number="The job number from your last /search list")
async def review(interaction: discord.Interaction, number: int):
    await handle_review(interaction, number)


async def setup_hook():
    synced = await bot.tree.sync()
    print(f"Globally synced {len(synced)} command(s)")


bot.setup_hook = setup_hook


def main():
    token = os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        raise RuntimeError(
            "DISCORD_BOT_TOKEN is not set. "
            "Please configure your Discord bot token."
        )

    bot.run(token)


if __name__ == "__main__":
    main()
