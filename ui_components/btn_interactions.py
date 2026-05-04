import discord
from ui_components.rate_response_btn import RateResponseButton
from ui_components.followup_modal import FollowUpButton
from ui_components.delete_btn import DeleteButton
from ui_components.try_again_btn import TryAgainButton
from ui_components.regenerate_btn import RegenerateButton


class BtnInteractions(discord.ui.ActionRow):
    def __init__(self, query: str = "", show_buttons: str = "all", user_id: int = 0, parent_view=None, action_type: str = "ask") -> None:
        super().__init__()
        self.query = query
        self.show_buttons = show_buttons
        self.user_id = user_id
        self.parent_view = parent_view
        self.action_type = action_type
        
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
            self.add_item(DeleteButton(parent_view=parent_view))
        elif show_buttons == "delete_only":
            self.add_item(DeleteButton(parent_view=parent_view))
        elif show_buttons == "disabled":
            # All buttons disabled during processing
            self.add_item(FollowUpButton(parent_view=parent_view, disabled=True))
            self.add_item(RateResponseButton(user_id=self.user_id, parent_view=parent_view, disabled=True))
            self.add_item(RegenerateButton(parent_view=parent_view, disabled=True))
            self.add_item(DeleteButton(parent_view=parent_view, disabled=True))
        elif show_buttons == "thinking":
            # Show thinking state on regenerate button, disable others
            self.add_item(FollowUpButton(parent_view=parent_view, disabled=True))
            self.add_item(RateResponseButton(user_id=self.user_id, parent_view=parent_view, disabled=True))
            self.add_item(RegenerateButton(parent_view=parent_view, thinking=True))
            self.add_item(DeleteButton(parent_view=parent_view, disabled=True))