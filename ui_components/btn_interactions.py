import os
import aiohttp
import discord
from ui_components.rate_response import RateResponseButton
from ui_components.followup_modal import FollowUpButton
from logger import get_logger
from metrics import discord_commands_total, discord_command_errors_total

log = get_logger(__name__)
RAG_BACKEND_URL = os.getenv("RAG_BACKEND_URL", "http://localhost:8000/ask")


class BtnInteractions(discord.ui.ActionRow):
    def __init__(self, query: str = "", fail: bool = True, user_id: int = 0) -> None:
        super().__init__()
        self.query = query
        self.fail = fail
        self.user_id = user_id
        
        if not self.fail:
            self.add_item(FollowUpButton())
            self.add_item(RateResponseButton(user_id=self.user_id))

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
            
        # Remove buttons from the original message
        await interaction.message.edit(view=None)

        from ui_components.response_separator import ResponseView
        await interaction.followup.send(
            ephemeral=False,
            view=ResponseView(query=self.query, response=response_text, fail=False),
        )
       
