
import asyncio
from unittest.mock import AsyncMock, MagicMock

from bot.discord_bot import search


def test_search_command():
    # Simulate a Discord interaction
    interaction = MagicMock()
    interaction.response.send_message = AsyncMock()

    # Run the /search command callback
    asyncio.run(
        search.callback(interaction, "Python developer")
    )

    # Verify the bot responds with a numbered list of jobs
    interaction.response.send_message.assert_awaited_once()
    message = interaction.response.send_message.await_args.args[0]
    assert "Python developer" in message
    assert "**1.**" in message and "**5.**" in message
    assert "/review" in message


def test_search_blank_query_asks_for_input():
    interaction = MagicMock()
    interaction.response.send_message = AsyncMock()

    asyncio.run(search.callback(interaction, "   "))

    interaction.response.send_message.assert_awaited_once_with(
        "Please provide a job search query."
    )
