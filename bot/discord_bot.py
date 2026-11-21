
import discord
import os
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
from bot.search_handler import process_search_request
from src.bot.commands import handle_review, placeholder_results
from src.bot.formatting import format_job_list
from src.core.result_store import save_results

load_dotenv(".env.local")
# Create the Discord bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="search", description="Search for job listings")
@app_commands.describe(query="Describe the job you are looking for")
async def search(interaction: discord.Interaction, query: str):
    # Temporarily store the user's search request
    search_query = query

    # Pass the request to our search handler
    response = process_search_request(search_query)

    # Blank queries keep the handler's "please provide a query" reply
    if search_query.strip():
        # TODO(#14): replace placeholders with the real search results
        jobs = placeholder_results(search_query.strip())
        save_results(interaction.user.id, jobs)
        response = format_job_list(search_query.strip(), jobs)

    # Send the response back to Discord
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
