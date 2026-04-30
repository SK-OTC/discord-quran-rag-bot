import os
import asyncio
import uvicorn
from dotenv import load_dotenv
from logger import configure_logging, get_logger
from backend.server_start import SlashBot
from backend.routes import app

configure_logging()
log = get_logger(__name__)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Missing BOT_TOKEN in environment.")


async def main():
    bot = SlashBot()
    
    @bot.event
    async def on_ready():
        log.info("bot_ready", user=str(bot.user))
    
    # Start uvicorn server
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    
    # Run both concurrently
    await asyncio.gather(
        bot.start(TOKEN),
        server.serve()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("shutdown_initiated")