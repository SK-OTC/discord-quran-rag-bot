import discord
from logger import get_logger

log = get_logger(__name__)

class DeleteButton(discord.ui.Button):
    """Button to delete the specific ResponseView message."""
    def __init__(self, parent_view=None, disabled: bool = False) -> None:
        super().__init__(
            label="Delete",
            style=discord.ButtonStyle.secondary,
            emoji="🗑️",
            disabled=disabled
        )
        self.parent_view = parent_view
    
    async def callback(self, interaction: discord.Interaction) -> None:
        log.info("delete_button_clicked", user_id=interaction.user.id)
        
        try:
            await interaction.message.delete()
            log.info("message_deleted", user_id=interaction.user.id, message_id=interaction.message.id)
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to delete this message.",
                ephemeral=True
            )
        except discord.NotFound:
            pass
        except Exception as e:
            log.error("delete_message_error", user_id=interaction.user.id, error=str(e))
            await interaction.response.send_message(
                "Failed to delete the message. Please try again.",
                ephemeral=True
            )