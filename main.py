import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.typing = False
intents.message_content = True
intents.members = True
intents.presences = True

TOKEN = os.getenv("BOT_TOKEN") 


class SlashBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="/", intents=intents)
    # Loads commands and syncs them with Discord
    async def setup_hook(self) -> None:
        await self.load_extension("command_list")
        synced = await self.tree.sync()
        print(f"Synced {len(synced)} global slash commands")


bot = SlashBot()

# Event handler for when the bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


if not TOKEN:
    raise RuntimeError("Missing BOT_TOKEN or DISCORD_TOKEN in environment.")

bot.run(TOKEN)