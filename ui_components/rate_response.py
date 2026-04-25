import discord

from bot_commands.feedback import FeedbackHandler

from logger import get_logger

log = get_logger(__name__)
class RateResponseButton(discord.ui.Button):
    def __init__(self, user_id: int = 0) -> None:
        super().__init__(
            label="Rate AI response",
            style=discord.ButtonStyle.gray,
            emoji="⭐"
        )
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction) -> None:
        log.info("rate_button_clicked", user_id=interaction.user.id)
        await interaction.response.send_modal(FeedbackHandler())