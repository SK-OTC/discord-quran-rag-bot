import asyncio
import time
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
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

# Timeout middleware - prevent hanging requests from blocking the server
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """Enforce 60 second timeout on all requests to prevent event loop blocking"""
    try:
        response = await asyncio.wait_for(call_next(request), timeout=60.0)
        return response
    except asyncio.TimeoutError:
        log.error("request_timeout", path=request.url.path)
        return JSONResponse(
            status_code=504,
            content={"error": "Request processing timeout (60s limit)", "success": False}
        )

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


async def _save_feedback_to_db(user_id: str, username: str, rating: int, comments: str) -> None:
    """
    Background task: Save feedback to database without blocking the response.
    This runs asynchronously after the API response is sent to the client.
    """
    try:
        with db_write_duration_seconds.labels(table="user_feedback").time():
            result = (
                supabase.table("user_feedback")
                .insert({
                    "user_id": user_id,
                    "username": username,
                    "rating": rating,
                    "comments": comments,
                })
                .execute()
            )
        
        if result.data:
            feedback_rating_distribution.observe(rating)
            log.info("feedback_saved_background", user_id=user_id, rating=rating)
        else:
            log.error("feedback_save_failed_background", user_id=user_id, error="No data returned")
    except Exception as e:
        log.error("feedback_background_error", user_id=user_id, error=str(e), exc_info=True)


@app.post("/feedback", response_model=Response, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def feedback(request: FeedbackData, background_tasks: BackgroundTasks) -> Response:
    try:
        log.info("feedback_received", user_id=request.user_id, rating=request.rating)
        
        # Add feedback saving as background task - returns immediately without waiting for DB write
        # This prevents the slow database operation from blocking the response
        background_tasks.add_task(
            _save_feedback_to_db,
            request.user_id,
            request.username,
            request.rating,
            request.comments
        )
        
        # Return response immediately
        log.info("feedback_queued_background", user_id=request.user_id)
        return Response(answer=f"Feedback received! You rated this AI response: {request.rating} stars.")

    except Exception as e:
        log.error("feedback_error", user_id=request.user_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/ask", response_model=Response, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def ask(request: AskRequest) -> Response:
    try:
        log.info("ask_received", user_id=request.user_id, question_length=len(request.question))

        # Add timeout for RAG query to prevent hanging
        try:
            with rag_query_duration_seconds.labels(endpoint="ask").time():
                answer = await asyncio.wait_for(
                    asyncio.to_thread(rag_answer, request.question),
                    timeout=30.0  # 30 second timeout for RAG processing
                )
        except asyncio.TimeoutError:
            log.error("ask_timeout", user_id=request.user_id)
            raise HTTPException(status_code=504, detail="Question processing took too long. Please try again.")

        if not answer or not answer.strip():
            log.warning("ask_empty_answer", user_id=request.user_id, question=request.question[:100])
            raise HTTPException(status_code=500, detail="No answer generated. Please try again.")

        start_conversation(request.user_id, request.question, answer)
        log.info("ask_answered", user_id=request.user_id, answer_length=len(answer))
        return Response(answer=answer)

    except HTTPException:
        raise
    except Exception as e:
        log.error("ask_error", user_id=request.user_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")


@app.post("/followup", response_model=Response, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def followup(request: FollowUpRequest) -> Response:
    try:
        log.info("followup_received", user_id=request.user_id, question_length=len(request.question))

        history = get_history(request.user_id)
        if not history:
            log.warning("followup_no_history", user_id=request.user_id)
            raise HTTPException(status_code=404, detail="No conversation history found. Please start a new conversation with /ask first.")

        # Add timeout for RAG query with history
        try:
            with rag_query_duration_seconds.labels(endpoint="followup").time():
                answer = await asyncio.wait_for(
                    asyncio.to_thread(rag_answer_with_history, request.question, history),
                    timeout=30.0  # 30 second timeout for RAG processing
                )
        except asyncio.TimeoutError:
            log.error("followup_timeout", user_id=request.user_id)
            raise HTTPException(status_code=504, detail="Question processing took too long. Please try again.")

        if not answer or not answer.strip():
            log.warning("followup_empty_answer", user_id=request.user_id, question=request.question[:100])
            raise HTTPException(status_code=500, detail="No answer generated. Please try again.")

        append_turn(request.user_id, request.question, answer)
        log.info("followup_answered", user_id=request.user_id, answer_length=len(answer))
        return Response(answer=answer)

    except HTTPException:
        raise
    except Exception as e:
        log.error("followup_error", user_id=request.user_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process follow-up question: {str(e)}")