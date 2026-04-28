from logger import configure_logging, get_logger
from backend.server_start import SlashBot
from config import BOT_TOKEN

configure_logging()
log = get_logger(__name__)

TOKEN = BOT_TOKEN


bot = SlashBot()

# Event handler for when the bot is ready
@bot.event
async def on_ready():
    log.info("bot_ready", user=str(bot.user))


if not TOKEN:
    raise RuntimeError("Missing BOT_TOKEN or DISCORD_TOKEN in environment.")


if __name__ == "__main__":
    bot.run(TOKEN)