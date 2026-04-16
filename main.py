import asyncio
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import discord
import uvicorn
from discord.ext import commands
from dotenv import load_dotenv
from db.supabase_client import supabase

load_dotenv()
app = FastAPI()
intents = discord.Intents.default()
intents.typing = False
intents.message_content = True
intents.members = True
intents.presences = True

TOKEN = os.getenv("BOT_TOKEN") 


class FeedbackData(BaseModel):
    user_id: str
    username: str
    rating: int
    comments: str 


class AskRequest(BaseModel):
    question: str


class Response(BaseModel):
    answer: str

class SlashBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="/", intents=intents)
    # Loads commands and syncs them with Discord
    async def setup_hook(self) -> None:
        await self.load_extension("command_list")
        synced = await self.tree.sync()
        print(f"Synced {len(synced)} global slash commands")

        config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
        server = uvicorn.Server(config)
        asyncio.create_task(server.serve())
        print("FastAPI server starting on http://127.0.0.1:8000")


bot = SlashBot()

# Event handler for when the bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@app.post("/feedback", response_model=Response)
async def feedback(request: FeedbackData) -> Response:
    result = (
        supabase.table("user_feedback")
        .insert({
            "user_id": request.user_id,
            "username": request.username,
            "rating": request.rating,
            "comments": request.comments,
        })
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to save feedback.")
    return Response(answer=f"Feedback saved! You rated this AI response: {request.rating} stars.")



@app.post("/ask", response_model=Response)
async def ask(request: AskRequest) -> Response:
    # TODO: connect RAG pipeline here
    return Response(answer=f"RAG pipeline not connected yet. You asked: {request.question}")


if not TOKEN:
    raise RuntimeError("Missing BOT_TOKEN or DISCORD_TOKEN in environment.")


if __name__ == "__main__":
    bot.run(TOKEN)