import discord
from ui_components.btn_interactions import BtnInteractions

class ResponseView(discord.ui.LayoutView):

    _TOTAL_LIMIT = 4000

    def __init__(self, query: str, response: str, show_buttons: str = "all", user_id: int = 0, action_type: str = "ask") -> None:
        """Create a response view with configurable buttons.
        
        Args:
            query: The user's query
            response: The AI response
            show_buttons: "all", "followup_and_regenerate", "regenerate_only", "rate_only", "try_again", "no_buttons", "delete_only"
            user_id: The user ID
            action_type: "ask", "followup", or "regenerate" - used for Try again button
        """
        super().__init__(timeout=None)
        self.query = query
        self.response = response
        self.show_buttons = show_buttons
        self.user_id = user_id
        self.action_type = action_type
        
        query_display = f"**Query:** {query}"
        available = self._TOTAL_LIMIT - len(query_display)
        if not response or not response.strip():
            response = "*(No response)*"
        elif len(response) > available:
            response = response[: available - 3] + "..."
        self.add_item(discord.ui.TextDisplay(query_display))
        self.add_item(discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))
        self.add_item(discord.ui.TextDisplay(response))
        
        if show_buttons != "no_buttons":
            self.add_item(BtnInteractions(
                query=query, 
                show_buttons=show_buttons, 
                user_id=user_id, 
                parent_view=self,
                action_type=action_type
            ))
    
    async def update_buttons(self, interaction: discord.Interaction, show_buttons: str, action_type: str = None) -> None:
        """Update which buttons are shown in this view."""
        if action_type is None:
            action_type = self.action_type
        
        self.show_buttons = show_buttons
        self.action_type = action_type
        
        # Create new view with same content but different buttons
        new_view = ResponseView(
            query=self.query,  # Preserve original query
            response=self.response,  # Preserve original response
            show_buttons=show_buttons, 
            user_id=self.user_id,
            action_type=action_type
        )
        
        try:
            await interaction.message.edit(view=new_view)
        except discord.NotFound:
            # Message was deleted
            pass
        except Exception as e:
            from logger import get_logger
            log = get_logger(__name__)
            log.error("update_buttons_failed", error=str(e))