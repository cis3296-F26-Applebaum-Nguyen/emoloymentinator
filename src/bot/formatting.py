"""Formats bot output for Discord."""

from collections.abc import Sequence
from ..core.models import JobPosting, JobReview
import discord

DISCORD_MESSAGE_LIMIT = 2000


def shorten(text: str, limit: int = 1000) -> str:
    # Discord rejects embed fields over 1024 characters, so trim long values
    return text if len(text) <= limit else text[: limit - 3] + "..."


def build_job_embed(job: JobPosting, number: int, total: int) -> discord.Embed:
    embed = discord.Embed(title=f"Job {number}")

    # inline=True puts fields side by side (Title / Company / Site in your mockup)
    embed.add_field(name="Title", value=shorten(job.title), inline=True)
    embed.add_field(name="Company", value=shorten(job.company) or "Not listed", inline=True)
    embed.add_field(name="Site", value=job.site or "Unknown", inline=True)

    # inline=False gives each of these its own row
    embed.add_field(name="Posted", value=job.date_posted or "Not listed", inline=False)
    embed.add_field(name="Location", value=shorten(job.location or "Not listed"), inline=False)

    # [text](url) is Discord's markdown for a clickable link
    link = f"[Open job]({job.url})" if job.url else "Not available"
    embed.add_field(name="Link", value=link, inline=False)

    embed.set_footer(text=f"Job {number}/{total} • /review {number} for an AI review")
    return embed


def split_message(text: str, limit: int = DISCORD_MESSAGE_LIMIT) -> list[str]:
    if len(text) <= limit:
        return [text]

    pieces = []
    start = 0
    while start < len(text):
        end = min(start + limit, len(text))
        if end < len(text):
            newline = text.rfind("\n", start, end)
            if newline > start:
                end = newline + 1
        pieces.append(text[start:end])
        start = end
    return pieces


def format_job_review(review: JobReview) -> str:
    lines = [review.summary]

    # Each section is only added when it has content
    if review.years_experience:
        lines += ["", f"**Experience:** {review.years_experience}"]
    if review.tech_stack:
        lines += ["", "**Tech stack:** " + ", ".join(review.tech_stack)]
    if review.skills:
        lines += ["", "**Skills:** " + ", ".join(review.skills)]
    if review.other_requirements:
        lines += ["", "**Other requirements:**"]
        lines += [f"- {item}" for item in review.other_requirements]
    if review.cover_letter_required is not None:
        lines += ["", "**Cover letter:** " + (
            "required" if review.cover_letter_required else "not required"
        )]
    if review.tips:
        lines += ["", "**Tips:**"]
        lines += [f"- {tip}" for tip in review.tips]
    return "\n".join(lines)
