import discord
from components.feedback import FeedbackModal


class FeedbackView(discord.ui.ActionRow):
    def __init__(self) -> None:
        super().__init__()


    @discord.ui.button(label="Follow up?", style=discord.ButtonStyle.secondary, emoji="💬")
    async def follow_up(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message("Ask a follow-up question:", ephemeral=True)

    @discord.ui.button(label="Regenerate", style=discord.ButtonStyle.gray, emoji="🔄")
    async def regenerate(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message("Regenerating response...", ephemeral=True)

    @discord.ui.button(label="Rate AI response", style=discord.ButtonStyle.gray, emoji="⭐")
    async def rate_ai_response(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(FeedbackModal())
    
