import os
import aiohttp
import discord
from components.feedback_modal import FeedbackModal

FEEDBACK_BACKEND_URL = os.getenv("FEEDBACK_BACKEND_URL", "http://localhost:8000/feedback")


class FeedbackHandler(FeedbackModal):
    async def on_submit(self, interaction: discord.Interaction) -> None:
        rating_value = self.rating.value.strip()
        if rating_value not in {"1", "2", "3", "4", "5"}:
            await interaction.response.send_message(
                "Invalid rating. Please enter a number between 1 and 5.", ephemeral=True
            )
            return

        payload = {
            "id": None,  # Let the backend generate the ID
            "user_id": str(interaction.user.id),
            "username": str(interaction.user),
            "rating": int(rating_value),
            "comments": self.comments.value or "",
        }

        await interaction.response.defer(ephemeral=True)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(FEEDBACK_BACKEND_URL, json=payload) as resp:
                    if resp.status != 200:
                        await interaction.followup.send(
                            "Failed to submit feedback. Please try again later.", ephemeral=True
                        )
                        return
        except aiohttp.ClientError:
            await interaction.followup.send(
                "Could not reach the feedback server. Please try again later.", ephemeral=True
            )
            return

        comments_text = f" with comments: {self.comments.value}" if self.comments.value else ""
        await interaction.followup.send(
            f"Thanks for your feedback! You rated this response **{rating_value}/5**{comments_text}.",
            ephemeral=True,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(
            "An unexpected error occurred while submitting feedback.", ephemeral=True
        )
