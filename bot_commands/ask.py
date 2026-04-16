import os
import aiohttp
import discord
from ui_components.response_separator import ResponseView


RAG_BACKEND_URL = os.getenv("RAG_BACKEND_URL", "http://localhost:8000/ask")


async def ask(self, interaction: discord.Interaction, question: str) -> None:
    await interaction.response.defer()

    response_text = "Could not reach the backend. Please try again later."
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                RAG_BACKEND_URL,
                json={"question": question},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    response_text = data.get("answer", "No answer returned.")
                else:
                    response_text = "Failed to get a response. Please try again later."
    except aiohttp.ClientError:
        response_text = "Could not reach the RAG server. Please try again later."

    await interaction.followup.send(
        ephemeral=False,
        view=ResponseView(query=question, response=response_text),
    )