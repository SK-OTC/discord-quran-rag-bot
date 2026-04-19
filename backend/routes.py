import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from db.supabase_client import supabase
from backend.rag import rag_answer

load_dotenv()
app = FastAPI()

class FeedbackData(BaseModel):
    user_id: str
    username: str
    rating: int
    comments: str 


class AskRequest(BaseModel):
    question: str


class Response(BaseModel):
    answer: str


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
    answer = await asyncio.to_thread(rag_answer, request.question)
    return Response(answer=answer)