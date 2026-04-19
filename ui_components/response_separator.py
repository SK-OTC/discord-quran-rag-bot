import discord
from ui_components.btn_interactions import BtnInteractions

class ResponseView(discord.ui.LayoutView):
    """Components V2 layout: User Query / Separator / AI Response."""

    def __init__(self, query: str, response: str) -> None:
        super().__init__(timeout=None)
        self.add_item(discord.ui.TextDisplay(f"**Query:** {query}"))
        self.add_item(discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))
        self.add_item(discord.ui.TextDisplay(response))
        self.add_item(BtnInteractions(query=query))
