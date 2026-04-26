import aiohttp
import discord
from ui_components.rate_response import RateResponseButton
from ui_components.followup_modal import FollowUpButton
from logger import get_logger
from config import RAG_BACKEND_URL
from metrics import discord_commands_total, discord_command_errors_total

log = get_logger(__name__)


class BtnInteractions(discord.ui.ActionRow):
    def __init__(self, query: str = "", show_buttons: str = "all", user_id: int = 0, parent_view=None) -> None:
        super().__init__()
        self.query = query
        self.show_buttons = show_buttons
        self.user_id = user_id
        self.parent_view = parent_view
        
        # show_buttons options: "all", "followup_and_regenerate", "regenerate_only"
        if show_buttons == "all":
            self.add_item(FollowUpButton(parent_view=parent_view))
            self.add_item(RateResponseButton(user_id=self.user_id, parent_view=parent_view))
        elif show_buttons == "followup_and_regenerate":
            self.add_item(FollowUpButton(parent_view=parent_view))

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
        is_success = False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    RAG_BACKEND_URL,
                    json={"user_id": self.user_id, "question": self.query},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data.get("answer", "No answer returned.")
                        is_success = True
                        log.info("regenerate_success", user_id=interaction.user.id)
                    else:
                        log.warning("regenerate_bad_status", user_id=interaction.user.id, status=resp.status)
                        discord_command_errors_total.labels(command="regenerate").inc()
                        response_text = "Failed to get a response. Please try again later."
        except aiohttp.ClientError as e:
            log.error("regenerate_network_error", user_id=interaction.user.id, error=str(e))
            discord_command_errors_total.labels(command="regenerate").inc()
            response_text = "Could not reach the RAG server. Please try again later."
        
        # Update original message buttons based on success/error
        if is_success:
            # Success: hide all buttons on original message
            await self.parent_view.update_buttons(interaction, "no_buttons")
        else:
            # Error: show only regenerate button on original message
            await self.parent_view.update_buttons(interaction, "regenerate_only")

        from ui_components.response_view import ResponseView
        await interaction.followup.send(
            content=response_text,
            ephemeral=False,
            view=ResponseView(query=self.query, response=response_text, show_buttons="all", user_id=self.user_id),
        )
       
