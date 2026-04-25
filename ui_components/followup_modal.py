import discord

from logger import get_logger

log = get_logger(__name__)

class FollowUpButton(discord.ui.Button):
    def __init__(self, parent_view=None) -> None:
        super().__init__(
            label="Follow up?",
            style=discord.ButtonStyle.secondary,
            emoji="💬"
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        log.info("followup_button_clicked", user_id=interaction.user.id)
        await interaction.response.send_message(
            "Use `/followup` to continue the conversation.",
            ephemeral=True
        )
