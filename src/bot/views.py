import discord

from ..core.models import JobPosting
from .formatting import build_job_embed


class JobListView(discord.ui.View):
    def __init__(self, jobs: list[JobPosting], owner_id: int):
        super().__init__(timeout=600)  # buttons stop working after 10 minutes
        self.jobs = jobs
        self.owner_id = owner_id
        self.index = 0        # which job is currently showing (0-based)
        self.message: discord.Message | None = None  # set after sending, so on_timeout can edit it
        self.update_buttons()

    def build_embed(self) -> discord.Embed:
        return build_job_embed(self.jobs[self.index], self.index + 1, len(self.jobs))

    def update_buttons(self):
        # Grey out Previous on the first job and Next on the last
        self.previous_button.disabled = self.index == 0
        self.next_button.disabled = self.index == len(self.jobs) - 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Runs before every click. Only the person who ran /search can flip pages,
        # because /review reads THEIR saved list.
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This list belongs to someone else. Run /search to get your own.",
                ephemeral=True,  # only the clicker sees this message
            )
            return False
        return True

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1
        self.update_buttons()
        # Edit the existing message instead of posting a new one
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def on_timeout(self):
        # Grey out both buttons so they don't show a confusing "interaction failed"
        for button in self.children:
            if isinstance(button, discord.ui.Button):
                button.disabled = True
        if self.message is not None:
            await self.message.edit(view=self)