import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.bot.bot import create_bot
from src.core.models import JobPosting, SearchRequest


def test_search_command():
    interaction = MagicMock()
    interaction.user.id = 1
    interaction.response.send_message = AsyncMock()
    interaction.followup.send = AsyncMock()

    async def fake_search(request):
        return [JobPosting(title=f"{i} {request.search_term}", company="Acme") for i in range(1, 6)]

    bot = create_bot(
        lambda text: SearchRequest(search_term=text),
        fake_search,
        lambda user_id, jobs: None,
        lambda job: "review",
    )
    search = bot.tree.get_command("search")

    asyncio.run(search.callback(interaction, "Python developer"))

    interaction.response.send_message.assert_awaited_once_with("Working on it...")
    kwargs = interaction.followup.send.await_args_list[-1].kwargs
    embed = kwargs["embed"]
    assert embed.title == "Job 1"
    title_field = next(field for field in embed.fields if field.name == "Title")
    assert "Python developer" in title_field.value


def test_search_blank_query_asks_for_input():
    interaction = MagicMock()
    interaction.response.send_message = AsyncMock()
    bot = create_bot(
        lambda text: SearchRequest(search_term=text),
        None,
        lambda user_id, jobs: None,
        lambda job: "review",
    )
    search = bot.tree.get_command("search")

    asyncio.run(search.callback(interaction, "   "))

    interaction.response.send_message.assert_awaited_once_with(
        "Please provide a job search query."
    )
