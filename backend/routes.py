import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from prometheus_fastapi_instrumentator import Instrumentator
from db.supabase_client import supabase
from backend.rag import rag_answer, rag_answer_with_history
from backend.conversation_store import get_history, start_conversation, append_turn
from logger import get_logger
from metrics import (
    db_write_duration_seconds,
    feedback_rating_distribution,
    rag_query_duration_seconds,
)

load_dotenv()
log = get_logger(__name__)
app = FastAPI()

# Auto-instruments all HTTP routes (request counts, latency, status codes)
# and exposes a /metrics endpoint for Prometheus to scrape.
Instrumentator().instrument(app).expose(app)

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    log.error("http_exception", path=request.url.path, status_code=exc.status_code, detail=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "success": False}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=request.url.path, error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "success": False}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}

class FeedbackData(BaseModel):
    user_id: str
    username: str
    rating: int
    comments: str


class AskRequest(BaseModel):
    user_id: int
    question: str


class FollowUpRequest(BaseModel):
    user_id: int
    question: str


class Response(BaseModel):
    answer: str
    success: bool = True
    error_message: str = None


class ErrorResponse(BaseModel):
    error: str
    detail: str = None
    success: bool = False


@app.post("/feedback", response_model=Response)
async def feedback(request: FeedbackData) -> Response:
    with db_write_duration_seconds.labels(table="user_feedback").time():
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
        log.error("feedback_save_failed", user_id=request.user_id)
        raise HTTPException(status_code=500, detail="Failed to save feedback.")
    feedback_rating_distribution.observe(request.rating)
    log.info("feedback_saved", user_id=request.user_id, rating=request.rating)
    return Response(answer=f"Feedback saved! You rated this AI response: {request.rating} stars.")


@app.post("/ask", response_model=Response)
async def ask(request: AskRequest) -> Response:
    log.info("ask_received", user_id=request.user_id, question=request.question)
    with rag_query_duration_seconds.labels(endpoint="ask").time():
        answer = await asyncio.to_thread(rag_answer, request.question)
    start_conversation(request.user_id, request.question, answer)
    log.info("ask_answered", user_id=request.user_id)
    return Response(answer=answer)


@app.post("/followup", response_model=Response)
async def followup(request: FollowUpRequest) -> Response:
    log.info("followup_received", user_id=request.user_id, question=request.question)
    history = get_history(request.user_id)
    if not history:
        log.warning("followup_no_history", user_id=request.user_id)
        raise HTTPException(status_code=404, detail="No conversation history found.")
    with rag_query_duration_seconds.labels(endpoint="followup").time():
        answer = await asyncio.to_thread(rag_answer_with_history, request.question, history)
    append_turn(request.user_id, request.question, answer)
    log.info("followup_answered", user_id=request.user_id)
    return Response(answer=answer)