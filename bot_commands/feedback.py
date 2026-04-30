import aiohttp
import discord
from ui_components.feedback_modal import FeedbackModal
from config import FEEDBACK_BACKEND_URL
from metrics import discord_commands_total, discord_command_errors_total
from logger import get_logger

log = get_logger(__name__)


class FeedbackHandler(FeedbackModal):
    def __init__(self, parent_view=None, interaction_message=None):
        super().__init__()
        self.parent_view = parent_view
        self.interaction_message = interaction_message
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        discord_commands_total.labels(command="feedback").inc()
        rating_value = self.rating.value.strip()
        if rating_value not in {"1", "2", "3", "4", "5"}:
            await interaction.response.send_message(
                "Invalid rating. Please enter a number between 1 and 5.", ephemeral=True
            )
            return

        payload = {
            "id": None,
            "user_id": str(interaction.user.id),
            "username": str(interaction.user),
            "rating": int(rating_value),
            "comments": self.comments.value or "",
        }

        await interaction.response.defer(ephemeral=True)

        is_success = False
        error_message = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(FEEDBACK_BACKEND_URL, json=payload) as resp:
                    if resp.status == 200:
                        is_success = True
                    else:
                        discord_command_errors_total.labels(command="feedback").inc()
                        error_message = "Failed to submit feedback. Please try again later."
        except aiohttp.ClientError:
            discord_command_errors_total.labels(command="feedback").inc()
            error_message = "Could not reach the feedback server. Please try again later."

        if is_success:
            comments_text = f" with comments: {self.comments.value}" if self.comments.value else ""
            await interaction.followup.send(
                f"Thanks for your feedback! You rated this response **{rating_value}/5**{comments_text}.",
                ephemeral=True,
            )
            
            # On success: show only delete button
            if self.interaction_message:
                try:
                    from ui_components.response_view import ResponseView
                    
                    # Get current view info
                    new_view = ResponseView(
                        query=self.parent_view.query if self.parent_view else "", 
                        response=self.parent_view.response if self.parent_view else "",
                        show_buttons="delete_only",
                        user_id=self.parent_view.user_id if self.parent_view else 0
                    )
                    
                    # Edit the original message to show only delete button
                    await self.interaction_message.edit(view=new_view)
                    log.info("feedback_success_buttons_updated_to_delete_only")
                    
                except discord.NotFound:
                    log.warning("feedback_message_not_found_for_edit")
                except discord.Forbidden:
                    log.error("feedback_no_permission_to_edit_message")
                except Exception as e:
                    log.error("failed_to_update_buttons_after_rating", error=str(e))
        else:
            # On failure: keep A and D, show error
            if error_message:
                await interaction.followup.send(
                    error_message,
                    ephemeral=True
                )
            # Don't update the view - keeps A and D visible

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        log.error("feedback_modal_error", error=str(error))
        # Try to respond if not already responded
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An unexpected error occurred while submitting feedback.", 
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "An unexpected error occurred while submitting feedback.", 
                    ephemeral=True
                )
        except:
            pass