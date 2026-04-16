import discord

async def ping(self, interaction: discord.Interaction) -> None:
    latency_ms = round(self.bot.latency * 1000)
    await interaction.response.send_message(f"Pong! `{latency_ms}ms`", ephemeral=True)