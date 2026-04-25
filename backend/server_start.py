import os

import discord
import asyncio
import uvicorn
from discord.ext import commands
from dotenv import load_dotenv
from backend.routes import app

load_dotenv()
intents = discord.Intents.default()
intents.typing = False
intents.message_content = True
intents.members = True
intents.presences = True

host = os.environ["HOST"]
class SlashBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="/", intents=intents)

    # Loads commands and syncs them with Discord
    async def setup_hook(self) -> None:
        await self.load_extension("command_list")
        synced = await self.tree.sync()
        print(f"Synced {len(synced)} global slash commands")

        config = uvicorn.Config(app, host=host, port=8000, log_level="warning")
        server = uvicorn.Server(config)
        asyncio.create_task(server.serve())
        print(f"FastAPI server starting on {host}:8000")


