import os
import aiohttp
import discord
from bot_commands.feedback import FeedbackHandler
from ui_components.followup_modal import follow_up_modal
from logger import get_logger
from metrics import discord_commands_total, discord_command_errors_total

log = get_logger(__name__)
RAG_BACKEND_URL = os.getenv("RAG_BACKEND_URL", "http://localhost:8000/ask")


class BtnInteractions(discord.ui.ActionRow):
    def __init__(self, query: str = "", user_id: int = 0) -> None:
        super().__init__()
        self.query = query
        self.user_id = user_id

    @discord.ui.button(label="Follow up?", style=discord.ButtonStyle.secondary, emoji="💬")
    async def follow_up(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        log.info("followup_button_clicked", user_id=interaction.user.id)
        await follow_up_modal(self, interaction)

    @discord.ui.button(label="Regenerate", style=discord.ButtonStyle.gray, emoji="🔄")
    async def regenerate(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        log.info("regenerate_button_clicked", user_id=interaction.user.id, query=self.query)
        discord_commands_total.labels(command="regenerate").inc()
        await interaction.response.defer(ephemeral=True)

        response_text = "Could not reach the backend. Please try again later."
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    RAG_BACKEND_URL,
                    json={"user_id": self.user_id, "question": self.query},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data.get("answer", "No answer returned.")
                        log.info("regenerate_success", user_id=interaction.user.id)
                    else:
                        log.warning("regenerate_bad_status", user_id=interaction.user.id, status=resp.status)
                        discord_command_errors_total.labels(command="regenerate").inc()
                        response_text = "Failed to get a response. Please try again later."
        except aiohttp.ClientError as e:
            log.error("regenerate_network_error", user_id=interaction.user.id, error=str(e))
            discord_command_errors_total.labels(command="regenerate").inc()
            response_text = "Could not reach the RAG server. Please try again later."

        from ui_components.response_separator import ResponseView
        await interaction.followup.send(
            ephemeral=False,
            view=ResponseView(query=self.query, response=response_text),
        )

    @discord.ui.button(label="Rate AI response", style=discord.ButtonStyle.gray, emoji="⭐")
    async def rate_ai_response(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        log.info("rate_button_clicked", user_id=interaction.user.id)
        await interaction.response.send_modal(FeedbackHandler())

