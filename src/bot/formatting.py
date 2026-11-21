"""
Formats job search results and AI reviews into Discord messages.
Create a bot that can post embedded messages with multiple pages and buttons to flip through them.
"""
import os
import asyncio
import discord
import pandas as pd
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


def clean(value, fallback="Not listed") -> str:
    if value is None or pd.isna(value):
        return fallback
    return str(value)


def build_pages(jobs: pd.DataFrame) -> list[discord.Embed]:
    pages = []
    total = len(jobs)
    for i, (_, job) in enumerate(jobs.iterrows(), start=1):
        page = discord.Embed(
            title=f"Job {i}",
            color=discord.Color.blue(),
        )
        page.add_field(name="Title", value=clean(job.get("title")), inline=True)
        page.add_field(name="Company", value=clean(job.get("company")), inline=True)
        page.add_field(name="Site", value=clean(job.get("site")), inline=True)
        page.add_field(name="Posted", value=clean(job.get("date_posted")), inline=True)
        page.add_field(name="Location", value=clean(job.get("location")), inline=False)
        page.add_field(name="Link", value=f"[Open job]({clean(job.get('job_url'), 'https://example.com')})", inline=False)
        page.set_footer(text=f"Job {i}/{total}")
        pages.append(page)
    return pages


class Pages(discord.ui.View):
    def __init__(self, author_id: int, pages: list[discord.Embed]):
        super().__init__(timeout=300)
        self.author_id = author_id
        self.pages = pages
        self.index = 0
        self.message: discord.Message | None = None
        self.update_buttons()
    def update_buttons(self):
        self.prev_button.disabled = self.index == 0
        self.next_button.disabled = self.index == len(self.pages) - 1
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Only the person who ran the command can use these buttons.",
                ephemeral=True,
            )
            return False
        return True
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)
    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)

def test_search(search_term: str) -> pd.DataFrame:
    """
    Test function to simulate job search results.
    Returns a DataFrame with dummy job data.
    """
    data = {
        "title": [f"Job Title {i}" for i in range(1, 21)],
        "company": [f"Company {i}" for i in range(1, 21)],
        "site": [f"Site {i}" for i in range(1, 21)],
        "date_posted": [f"2024-06-{i:02d}" for i in range(1, 21)],
        "location": [f"Location {i}" for i in range(1, 21)],
        "job_url": [f"https://example.com/job{i}" for i in range(1, 21)],
    }
    return pd.DataFrame(data)



@bot.tree.command(name="search", description="Search for jobs")
async def jobs_cmd(interaction: discord.Interaction, search_term: str):
    await interaction.response.defer()
    jobs = await asyncio.to_thread(test_search, search_term)
    if jobs is None or len(jobs) == 0:
        await interaction.followup.send("No jobs found. Try a different search or location.")
        return
    pages = build_pages(jobs)
    view = Pages(interaction.user.id, pages)
    view.message = await interaction.followup.send(embed=pages[0], view=view)
bot.run(os.environ["DISCORD_TOKEN"])