import aiohttp
import discord
from config import RAG_BACKEND_URL
from logger import get_logger
from metrics import discord_commands_total, discord_command_errors_total

log = get_logger(__name__)

class RegenerateButton(discord.ui.Button):
    def __init__(self, parent_view=None, disabled: bool = False, thinking: bool = False) -> None:
        if thinking:
            super().__init__(
                label="Thinking...",
                style=discord.ButtonStyle.secondary,
                emoji="⏳",
                disabled=True
            )
        else:
            super().__init__(
                label="Regenerate",
                style=discord.ButtonStyle.gray,
                emoji="🔄",
                disabled=disabled
            )
        self.parent_view = parent_view
    
    async def callback(self, interaction: discord.Interaction) -> None:
        log.info("regenerate_button_clicked", user_id=interaction.user.id)
        discord_commands_total.labels(command="regenerate").inc()
        await interaction.response.defer(ephemeral=True)
        
        query = self.parent_view.query
        user_id = self.parent_view.user_id
        
        # Show thinking state - update original message to show thinking regenerate button
        await self.parent_view.update_buttons(interaction, "thinking")
        
        response_text = "Could not reach the backend. Please try again later."
        is_success = False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    RAG_BACKEND_URL,
                    json={"user_id": user_id, "question": query},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data.get("answer", "No answer returned.")
                        is_success = True
                        log.info("regenerate_success", user_id=interaction.user.id)
                    else:
                        log.warning("regenerate_bad_status", user_id=interaction.user.id, status=resp.status)
                        discord_command_errors_total.labels(command="regenerate").inc()
                        response_text = f"Failed to get a response (Status: {resp.status}). Please try again later."
        except aiohttp.ClientError as e:
            log.error("regenerate_network_error", user_id=interaction.user.id, error=str(e))
            discord_command_errors_total.labels(command="regenerate").inc()
            response_text = "Could not reach the RAG server. Please try again later."
        
        if is_success:
            # Success: original message shows only Rate and Delete buttons
            await self.parent_view.update_buttons(interaction, "rate_only")
            # Use parent_view to create new response
            await self.parent_view.send_new_response(interaction, query, response_text, "all", user_id)
        else:
            # Error: original message shows Try Again button for regenerate
            await self.parent_view.update_buttons(interaction, "try_again", action_type="regenerate")
            await interaction.followup.send(
                response_text,
                ephemeral=True
            )