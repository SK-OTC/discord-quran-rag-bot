import aiohttp
import discord
from config import RAG_BACKEND_URL, RAG_FOLLOWUP_URL
from logger import get_logger   
from metrics import discord_command_errors_total

log = get_logger(__name__)

class TryAgainButton(discord.ui.Button):
    """Button shown when an error occurs, allowing retry of the original action."""
    def __init__(self, parent_view=None, action_type: str = "ask", disabled: bool = False) -> None:
        super().__init__(
            label="Try again",
            style=discord.ButtonStyle.danger,
            emoji="🔁",
            disabled=disabled
        )
        self.parent_view = parent_view
        self.action_type = action_type  # "ask", "followup", or "regenerate"
    
    async def callback(self, interaction: discord.Interaction) -> None:
        log.info("try_again_button_clicked", user_id=interaction.user.id, action_type=self.action_type)
        
        # Disable the button and show loading state
        self.disabled = True
        self.label = "Thinking..."
        self.emoji = "⏳"
        self.style = discord.ButtonStyle.secondary
        
        # Update the message to show the disabled button
        await interaction.response.edit_message(view=self.parent_view)
        
        # Determine which URL to use based on action type
        if self.action_type == "followup":
            url = RAG_FOLLOWUP_URL
        else:
            url = RAG_BACKEND_URL
        
        query = self.parent_view.query
        user_id = self.parent_view.user_id
        
        log.info("try_again_sending_request", user_id=user_id, action_type=self.action_type, url=url)
        
        response_text = "Could not reach the backend. Please try again later."
        is_success = False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json={"user_id": user_id, "question": query},
                ) as resp:
                    log.info("try_again_response", status=resp.status, user_id=user_id)
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data.get("answer", "No answer returned.")
                        if response_text and response_text.strip():
                            is_success = True
                            log.info("try_again_success", user_id=interaction.user.id)
                        else:
                            log.warning("try_again_empty_answer", user_id=interaction.user.id)
                            response_text = "No answer generated. Please try again."
                    else:
                        log.warning("try_again_bad_status", user_id=interaction.user.id, status=resp.status)
                        discord_command_errors_total.labels(command=self.action_type).inc()
                        response_text = f"Failed to get a response (Status: {resp.status}). Please try again later."
        except aiohttp.ClientError as e:
            log.error("try_again_network_error", user_id=interaction.user.id, error=str(e))
            discord_command_errors_total.labels(command=self.action_type).inc()
            response_text = "Could not reach the RAG server. Please try again later."
        
        if is_success:
            # Success: original error message only needs Delete button (nothing to rate)
            await self.parent_view.update_buttons(interaction, "delete_only")
            # Send new response with all buttons
            await self.parent_view.send_new_response(interaction, query, response_text, "all", user_id)
        else:
            # Error: show try again button again with same action_type
            await self.parent_view.update_buttons(interaction, "try_again", action_type=self.action_type)
            await interaction.followup.send(
                response_text,
                ephemeral=True
            )