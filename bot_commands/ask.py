import os
import aiohttp
import discord
from ui_components.response_view import ResponseView
from logger import get_logger
from metrics import discord_commands_total, discord_command_errors_total

log = get_logger(__name__)
RAG_BACKEND_URL = os.getenv("RAG_BACKEND_URL", "http://localhost:8000/ask")


async def ask(self, interaction: discord.Interaction, question: str) -> None:
    await interaction.response.defer()
    user_id = interaction.user.id
    discord_commands_total.labels(command="ask").inc()
    log.info("ask_command_invoked", user_id=user_id, question=question)

    response_text = "Could not reach the backend. Please try again later."
    show_buttons = "regenerate_only"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                RAG_BACKEND_URL,
                json={"user_id": user_id, "question": question},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    response_text = data.get("answer", "No answer returned.")
                    show_buttons = "all"
                    log.info("ask_command_success", user_id=user_id)
                else:
                    log.warning("ask_command_bad_status", user_id=user_id, status=resp.status)
                    discord_command_errors_total.labels(command="ask").inc()
                    response_text = "Failed to get a response. Please try again later."
    except aiohttp.ClientError as e:
        log.error("ask_command_network_error", user_id=user_id, error=str(e))
        discord_command_errors_total.labels(command="ask").inc()
        response_text = "Could not reach the RAG server. Please try again later."
    
    await interaction.followup.send(
        content="",
        ephemeral=False,
        view=ResponseView(query=question, response=response_text, show_buttons=show_buttons, user_id=user_id),
    )


