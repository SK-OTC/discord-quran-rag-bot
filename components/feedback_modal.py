import discord

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

 
