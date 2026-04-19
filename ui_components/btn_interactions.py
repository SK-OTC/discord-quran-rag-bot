import os
import aiohttp
import discord
from bot_commands.feedback import FeedbackHandler

RAG_BACKEND_URL = os.getenv("RAG_BACKEND_URL", "http://localhost:8000/ask")


class BtnInteractions(discord.ui.ActionRow):
    def __init__(self, query: str = "") -> None:
        super().__init__()
        self.query = query

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
        await interaction.response.defer(ephemeral=False)

        response_text = "Could not reach the backend. Please try again later."
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    RAG_BACKEND_URL,
                    json={"question": self.query},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data.get("answer", "No answer returned.")
                    else:
                        response_text = "Failed to get a response. Please try again later."
        except aiohttp.ClientError:
            response_text = "Could not reach the RAG server. Please try again later."

        from ui_components.response_separator import ResponseView
        await interaction.followup.send(
            ephemeral=False,
            view=ResponseView(query=self.query, response=response_text),
        )

    @discord.ui.button(label="Rate AI response", style=discord.ButtonStyle.gray, emoji="⭐")
    async def rate_ai_response(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(FeedbackHandler())

