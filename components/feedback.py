import os
import aiohttp
import discord

FEEDBACK_BACKEND_URL = os.getenv("FEEDBACK_BACKEND_URL", "")


class FeedbackModal(discord.ui.Modal, title="Rate AI Response"):
    rating = discord.ui.TextInput(
        label="Rating (1–5)",
        placeholder="Enter a number from 1 to 5",
        min_length=1,
        max_length=1,
        required=True,
    )
    comments = discord.ui.TextInput(
        label="Comments (optional)",
        style=discord.TextStyle.paragraph,
        placeholder="Any additional feedback?",
        required=False,
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        rating_value = self.rating.value.strip()
        if rating_value not in {"1", "2", "3", "4", "5"}:
            await interaction.response.send_message(
                "Invalid rating. Please enter a number between 1 and 5.", ephemeral=True
            )
            return

        payload = {
            "user_id": str(interaction.user.id),
            "username": str(interaction.user),
            "rating": int(rating_value),
            "comments": self.comments.value or "",
        }

        if FEEDBACK_BACKEND_URL:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(FEEDBACK_BACKEND_URL, json=payload) as resp:
                        if resp.status not in (200, 201, 204):
                            await interaction.response.send_message(
                                "Failed to submit feedback. Please try again later.", ephemeral=True
                            )
                            return
            except aiohttp.ClientError:
                await interaction.response.send_message(
                    "Could not reach the feedback server. Please try again later.", ephemeral=True
                )
                return

        await interaction.response.send_message(
            f"Thanks for your feedback! You rated this response **{rating_value}/5**.",
            ephemeral=True,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(
            "An unexpected error occurred while submitting feedback.", ephemeral=True
        )
