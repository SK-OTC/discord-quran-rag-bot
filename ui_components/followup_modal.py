import discord


async def follow_up_modal(self, interaction: discord.Interaction) -> None:
    await interaction.response.send_message(f"Use `/followup` to continue the conversation.", ephemeral=True)