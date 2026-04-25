import os
import aiohttp
import discord
from ui_components.response_separator import ResponseView
from logger import get_logger
from metrics import discord_commands_total, discord_command_errors_total

log = get_logger(__name__)
RAG_FOLLOWUP_URL = os.getenv("RAG_FOLLOWUP_URL", "http://localhost:8000/followup")
RAG_ASK_URL = os.getenv("RAG_BACKEND_URL", "http://localhost:8000/ask")


async def followup(self, interaction: discord.Interaction, question: str) -> None:
    await interaction.response.defer()

    user_id = interaction.user.id
    discord_commands_total.labels(command="followup").inc()
    log.info("followup_command_invoked", user_id=user_id, question=question)
    response_text = "Could not reach the backend. Please try again later."
    is_success = False

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                RAG_FOLLOWUP_URL,
                json={"user_id": user_id, "question": question},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    response_text = data.get("answer", "No answer returned.")
                    is_success = True
                    log.info("followup_command_success", user_id=user_id)
                elif resp.status == 404:
                    # No cached context — fall back to /ask
                    log.warning("followup_no_history_fallback_to_ask", user_id=user_id)
                    async with session.post(
                        RAG_ASK_URL,
                        json={"user_id": user_id, "question": question},
                    ) as ask_resp:
                        if ask_resp.status == 200:
                            data = await ask_resp.json()
                            answer = data.get("answer", "No answer returned.")
                            response_text = f"{answer}\n\n*No previous context provided.*"
                            is_success = True
                            log.info("followup_fallback_ask_success", user_id=user_id)
                        else:
                            log.warning("followup_fallback_ask_bad_status", user_id=user_id, status=ask_resp.status)
                            response_text = "Failed to get a response. Please try again later."
                else:
                    log.warning("followup_command_bad_status", user_id=user_id, status=resp.status)
                    discord_command_errors_total.labels(command="followup").inc()
                    response_text = "Failed to get a response. Please try again later."
    except aiohttp.ClientError as e:
        log.error("followup_command_network_error", user_id=user_id, error=str(e))
        discord_command_errors_total.labels(command="followup").inc()
        response_text = "Could not reach the RAG server. Please try again later."

    # Success: no buttons on new followup message
    # Error: show only regenerate button
    show_buttons = "no_buttons" if is_success else "regenerate_only"
    
    await interaction.followup.send(
        content="",
        ephemeral=False,
        view=ResponseView(query=question, response=response_text, show_buttons=show_buttons, user_id=user_id),
    )
