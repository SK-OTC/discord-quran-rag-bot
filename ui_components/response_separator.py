import discord
from ui_components.btn_interactions import BtnInteractions

class ResponseView(discord.ui.LayoutView):
    """Components V2 layout: User Query / Separator / AI Response."""

    _TOTAL_LIMIT = 4000

    def __init__(self, query: str, response: str) -> None:
        super().__init__(timeout=None)
        query_display = f"**Query:** {query}"
        available = self._TOTAL_LIMIT - len(query_display)
        if not response or not response.strip():
            response = "*(No response)*"
        elif len(response) > available:
            response = response[: available - 3] + "..."
        self.add_item(discord.ui.TextDisplay(query_display))
        self.add_item(discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))
        self.add_item(discord.ui.TextDisplay(response))
        self.add_item(BtnInteractions(query=query))
