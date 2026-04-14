import discord
from components.ai_response import AIResponseView



async def ask(self, interaction: discord.Interaction, question: str) -> None:
        # Placeholder response until RAG pipeline is connected.
        await interaction.response.send_message(
            ephemeral=False,
            view=AIResponseView(query=question, response="RAG is not connected yet."),
        )