import aiohttp
import discord
from ui_components.rate_response import RateResponseButton
from ui_components.followup_modal import FollowUpButton
from logger import get_logger
from config import RAG_BACKEND_URL, RAG_FOLLOWUP_URL
from metrics import discord_commands_total, discord_command_errors_total

log = get_logger(__name__)


class BtnInteractions(discord.ui.ActionRow):
    def __init__(self, query: str = "", show_buttons: str = "all", user_id: int = 0, parent_view=None, action_type: str = "ask") -> None:
        super().__init__()
        self.query = query
        self.show_buttons = show_buttons
        self.user_id = user_id
        self.parent_view = parent_view
        self.action_type = action_type  # "ask", "followup", or "regenerate"
        
        # show_buttons options: "all", "followup_and_regenerate", "regenerate_only", "rate_only", "try_again", "no_buttons", "delete_only"
        if show_buttons == "all":
            self.add_item(FollowUpButton(parent_view=parent_view))
            self.add_item(RateResponseButton(user_id=self.user_id, parent_view=parent_view))
            self.add_item(RegenerateButton(parent_view=parent_view))
            self.add_item(DeleteButton(parent_view=parent_view))
        elif show_buttons == "followup_and_regenerate":
            self.add_item(FollowUpButton(parent_view=parent_view))
            self.add_item(RegenerateButton(parent_view=parent_view))
            self.add_item(DeleteButton(parent_view=parent_view))
        elif show_buttons == "regenerate_only":
            self.add_item(RegenerateButton(parent_view=parent_view))
            self.add_item(DeleteButton(parent_view=parent_view))
        elif show_buttons == "rate_only":
            self.add_item(RateResponseButton(user_id=self.user_id, parent_view=parent_view))
            self.add_item(DeleteButton(parent_view=parent_view))
        elif show_buttons == "try_again":
            self.add_item(TryAgainButton(parent_view=parent_view, action_type=action_type))
        elif show_buttons == "delete_only":
            self.add_item(DeleteButton(parent_view=parent_view))


class DeleteButton(discord.ui.Button):
    """Button to delete the specific ResponseView message."""
    def __init__(self, parent_view=None) -> None:
        super().__init__(
            label="Delete",
            style=discord.ButtonStyle.secondary,
            emoji="🗑️"
        )
        self.parent_view = parent_view
    
    async def callback(self, interaction: discord.Interaction) -> None:
        log.info("delete_button_clicked", user_id=interaction.user.id)
        
        try:
            await interaction.message.delete()
            log.info("message_deleted", user_id=interaction.user.id, message_id=interaction.message.id)
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to delete this message.",
                ephemeral=True
            )
        except discord.NotFound:
            # Message already deleted
            pass
        except Exception as e:
            log.error("delete_message_error", user_id=interaction.user.id, error=str(e))
            await interaction.response.send_message(
                "Failed to delete the message. Please try again.",
                ephemeral=True
            )


class RegenerateButton(discord.ui.Button):
    def __init__(self, parent_view=None) -> None:
        super().__init__(
            label="Regenerate",
            style=discord.ButtonStyle.gray,
            emoji="🔄"
        )
        self.parent_view = parent_view
    
    async def callback(self, interaction: discord.Interaction) -> None:
        log.info("regenerate_button_clicked", user_id=interaction.user.id)
        discord_commands_total.labels(command="regenerate").inc()
        await interaction.response.defer(ephemeral=True)
        
        query = self.parent_view.query
        user_id = self.parent_view.user_id
        
        response_text = "Could not reach the backend. Please try again later."
        is_success = False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    RAG_BACKEND_URL,
                    json={"user_id": user_id, "question": query},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data.get("answer", "No answer returned.")
                        is_success = True
                        log.info("regenerate_success", user_id=interaction.user.id)
                    else:
                        log.warning("regenerate_bad_status", user_id=interaction.user.id, status=resp.status)
                        discord_command_errors_total.labels(command="regenerate").inc()
                        response_text = f"Failed to get a response (Status: {resp.status}). Please try again later."
        except aiohttp.ClientError as e:
            log.error("regenerate_network_error", user_id=interaction.user.id, error=str(e))
            discord_command_errors_total.labels(command="regenerate").inc()
            response_text = "Could not reach the RAG server. Please try again later."
        
        from ui_components.response_view import ResponseView
        
        if is_success:
            # Success: original message shows only Rate and Delete buttons
            await self.parent_view.update_buttons(interaction, "rate_only")
            await interaction.followup.send(
                ephemeral=False,
                view=ResponseView(query=query, response=response_text, show_buttons="all", user_id=user_id),
            )
        else:
            # Error: original message shows Try Again button for regenerate
            await self.parent_view.update_buttons(interaction, "try_again", action_type="regenerate")
            await interaction.followup.send(
                response_text,
                ephemeral=True
            )


class TryAgainButton(discord.ui.Button):
    """Button shown when an error occurs, allowing retry of the original action."""
    def __init__(self, parent_view=None, action_type: str = "ask") -> None:
        super().__init__(
            label="Try again",
            style=discord.ButtonStyle.danger,
            emoji="🔁"
        )
        self.parent_view = parent_view
        self.action_type = action_type  # "ask", "followup", or "regenerate"
    
    async def callback(self, interaction: discord.Interaction) -> None:
        log.info("try_again_button_clicked", user_id=interaction.user.id, action_type=self.action_type)
        
        # Disable the button and show loading state
        self.disabled = True
        self.label = "Thinking..."
        self.emoji = "⏳"
        self.style = discord.ButtonStyle.secondary
        
        # Update the message to show the disabled button
        await interaction.response.edit_message(view=self.parent_view)
        
        # Determine which URL to use based on action type
        if self.action_type == "followup":
            url = RAG_FOLLOWUP_URL
        else:
            url = RAG_BACKEND_URL
        
        query = self.parent_view.query
        user_id = self.parent_view.user_id
        
        log.info("try_again_sending_request", user_id=user_id, action_type=self.action_type, url=url)
        
        response_text = "Could not reach the backend. Please try again later."
        is_success = False
        try:
            async with aiohttp.ClientSession() as session:
                log.info("try_again_posting", url=url, user_id=user_id, query_length=len(query))
                async with session.post(
                    url,
                    json={"user_id": user_id, "question": query},
                ) as resp:
                    log.info("try_again_response", status=resp.status, user_id=user_id)
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data.get("answer", "No answer returned.")
                        if response_text and response_text.strip():
                            is_success = True
                            log.info("try_again_success", user_id=interaction.user.id)
                        else:
                            log.warning("try_again_empty_answer", user_id=interaction.user.id)
                            response_text = "No answer generated. Please try again."
                    else:
                        log.warning("try_again_bad_status", user_id=interaction.user.id, status=resp.status)
                        discord_command_errors_total.labels(command=self.action_type).inc()
                        response_text = f"Failed to get a response (Status: {resp.status}). Please try again later."
        except aiohttp.ClientError as e:
            log.error("try_again_network_error", user_id=interaction.user.id, error=str(e))
            discord_command_errors_total.labels(command=self.action_type).inc()
            response_text = "Could not reach the RAG server. Please try again later."
        
        from ui_components.response_view import ResponseView
        
        if is_success:
            # Success: remove try again button, show rate and delete buttons
            await self.parent_view.update_buttons(interaction, "rate_only")
            await interaction.followup.send(
                ephemeral=False,
                view=ResponseView(query=query, response=response_text, show_buttons="all", user_id=user_id),
            )
        else:
            # Error: show try again button again (re-enable it) with same action_type
            await self.parent_view.update_buttons(interaction, "try_again", action_type=self.action_type)
            await interaction.followup.send(
                response_text,
                ephemeral=True
            )