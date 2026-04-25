import discord

from logger import get_logger

log = get_logger(__name__)

class FollowUpButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Follow up?",
            style=discord.ButtonStyle.secondary,
            emoji="💬"
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        log.info("followup_button_clicked", user_id=interaction.user.id)
        await interaction.response.send_message(
            "Use `/followup` to continue the conversation.",
            ephemeral=True
        )
# class FollowUp(discord.ui.Button, title="Follow-up Question"):
#     @discord.ui.button(label="Follow up?", style=discord.ButtonStyle.secondary, emoji="💬")
#     async def follow_up_button(
#         self,
#         interaction: discord.Interaction,
#         button: discord.ui.Button,
#     ) -> None:
#         # log.info("followup_button_clicked", user_id=interaction.user.id)
#         await interaction.response.send_message(f"Use `/followup` to continue the conversation.", ephemeral=True)
# async def follow_up_modal(self, interaction: discord.Interaction) -> None:
#     await interaction.response.send_message(f"Use `/followup` to continue the conversation.", ephemeral=True)