import discord
from discord import app_commands
from discord.ext import commands
from bot_commands.about import about
from bot_commands.ask import ask
from bot_commands.followup import followup
from bot_commands.ping import ping

# Discord Command List
class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot 

    @app_commands.command(name="ping", description="Show bot latency")
    async def getPing(self, interaction: discord.Interaction) -> None:
        await ping(self, interaction)

    @app_commands.command(name="about", description="Show information about this bot")
    async def getAbout(self, interaction: discord.Interaction) -> None:
        await about(self, interaction)

    @app_commands.command(name="ask", description="Ask a question (placeholder)")
    @app_commands.describe(question="Your question")
    async def askQuestion(self, interaction: discord.Interaction, question: str) -> None:
        await ask(self, interaction, question)

    @app_commands.command(name="followup", description="Ask a follow-up question based on your previous query")
    @app_commands.describe(question="Your follow-up question")
    async def followupQuestion(self, interaction: discord.Interaction, question: str) -> None:
        await followup(self, interaction, question)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))
