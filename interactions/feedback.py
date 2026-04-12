import discord

class FeedbackView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=180)

    @discord.ui.button(label="Great", style=discord.ButtonStyle.success, emoji="👍")
    async def rate_great(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message("Thanks for the feedback: Great 👍", ephemeral=True)

    @discord.ui.button(label="Okay", style=discord.ButtonStyle.secondary, emoji="👌")
    async def rate_okay(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message("Thanks for the feedback: Okay 👌", ephemeral=True)

    @discord.ui.button(label="Needs Work", style=discord.ButtonStyle.danger, emoji="👎")
    async def rate_needs_work(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message("Thanks for the feedback: Needs Work 👎", ephemeral=True)