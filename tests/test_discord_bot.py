
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

    # Verify the bot responds with the handler's result
    interaction.response.send_message.assert_awaited_once_with(
        "Received your search request: Python developer"
    )
