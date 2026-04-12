import discord
from interactions.feedback import FeedbackView


async def ask(self, interaction: discord.Interaction, question: str) -> None:
        # Placeholder response until RAG pipeline is connected.
        await interaction.response.send_message(
            f"I received your question: \"{question}\"\n\nRAG is not connected yet.\n\nRate the AI's feedback:",
            ephemeral=False,
            view=FeedbackView(),
        )