import os
from dotenv import load_dotenv
from backend.server_start import SlashBot

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN") 


bot = SlashBot()

# Event handler for when the bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


if not TOKEN:
    raise RuntimeError("Missing BOT_TOKEN or DISCORD_TOKEN in environment.")


if __name__ == "__main__":
    bot.run(TOKEN)