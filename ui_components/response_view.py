import discord
from ui_components.btn_interactions import BtnInteractions

class ResponseView(discord.ui.LayoutView):

    _TOTAL_LIMIT = 4000

    def __init__(self, query: str, response: str, show_buttons: str = "all", user_id: int = 0) -> None:
        """Create a response view with configurable buttons.
        
        Args:
            query: The user's query
            response: The AI response
            show_buttons: "all" (regenerate, followup, rate), "followup_and_regenerate" (no rate), "regenerate_only", "no_buttons"
            user_id: The user ID
        """
        super().__init__(timeout=None)
        self.query = query
        self.response = response
        self.show_buttons = show_buttons
        self.user_id = user_id
        
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
            self.add_item(BtnInteractions(query=query, show_buttons=show_buttons, user_id=user_id, parent_view=self))
    
    async def update_buttons(self, interaction: discord.Interaction, show_buttons: str) -> None:
        """Update which buttons are shown in this view."""
        self.show_buttons = show_buttons
        new_view = ResponseView(self.query, self.response, show_buttons=show_buttons, user_id=self.user_id)
        await interaction.message.edit(view=new_view)
