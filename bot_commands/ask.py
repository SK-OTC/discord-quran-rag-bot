import aiohttp
import discord
from ui_components.response_view import ResponseView
from logger import get_logger
from config import RAG_BACKEND_URL
from metrics import discord_commands_total, discord_command_errors_total

log = get_logger(__name__)


async def ask(self, interaction: discord.Interaction, question: str) -> None:
    try:
        await interaction.response.defer()
    except discord.NotFound:
        log.warning("ask_interaction_expired_before_defer", user_id=getattr(interaction.user, "id", None))
        return
    user_id = interaction.user.id
    discord_commands_total.labels(command="ask").inc()
    log.info("ask_command_invoked", user_id=user_id, question=question)

    response_text = "Could not reach the backend. Please try again later."
    show_buttons = "try_again"
    action_type = "ask"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                RAG_BACKEND_URL,
                json={"user_id": user_id, "question": question},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    response_text = data.get("answer", "No answer returned.")
                    if response_text and response_text.strip():
                        show_buttons = "all"
                        log.info("ask_command_success", user_id=user_id)
                    else:
                        log.warning("ask_empty_answer", user_id=user_id, question=question[:100])
                        response_text = "No answer generated. Please try again."
                else:
                    log.warning("ask_command_bad_status", user_id=user_id, status=resp.status)
                    discord_command_errors_total.labels(command="ask").inc()
                    response_text = f"Failed to get a response (Status: {resp.status}). Please try again later."
    except aiohttp.ClientError as e:
        log.error("ask_command_network_error", user_id=user_id, error=str(e))
        discord_command_errors_total.labels(command="ask").inc()
        response_text = "Could not reach the RAG server. Please try again later."
    
    await interaction.followup.send(
        ephemeral=False,
        view=ResponseView(
            query=question, 
            response=response_text, 
            show_buttons=show_buttons, 
            user_id=user_id,
            action_type=action_type
        ),
    )