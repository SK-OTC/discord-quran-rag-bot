import os
import asyncio
from sentence_transformers import SentenceTransformer
from google import genai
from huggingface_hub import InferenceClient
from db.supabase_client import supabase_async
from dotenv import load_dotenv
from logger import get_logger
from metrics import (
    embedding_duration_seconds,
    embedding_model_load_duration_seconds,
    llm_fallback_total,
    llm_generation_duration_seconds,
    vector_search_duration_seconds,
)

log = get_logger(__name__)

_model = None
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
_hf_client = None


def _get_hf_client() -> InferenceClient:
    global _hf_client
    if _hf_client is None:
        _hf_client = InferenceClient(
            model=HF_GLM_MODEL,
            token=HF_TOKEN,
        )
    return _hf_client


def _glm5_generate(prompt: str) -> str:
    """Call GLM-5 via the Hugging Face Inference API as a fallback (sync)."""
    client = _get_hf_client()
    response = client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
        temperature=0.7,
    )
    return response.choices[0].message.content


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        log.info("embedding_model_loading", model="nomic-ai/nomic-embed-text-v1")
        with embedding_model_load_duration_seconds.time():
            _model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)
        log.info("embedding_model_loaded")
    return _model

_chapter_titles_cache = None

_chapter_titles_cache = None


def _embed_query_sync(query: str) -> list:
    """Run embedding in a worker thread to avoid blocking the event loop."""
    model = _get_model()
    with embedding_duration_seconds.time():
        return model.encode(query).tolist()


async def _get_chapter_titles() -> dict:
    """Fetch and cache chapter titles asynchronously."""
    global _chapter_titles_cache
    if _chapter_titles_cache is not None:
        return _chapter_titles_cache

    log.info("fetching_chapter_titles")
    result = await supabase_async.table("quran_chapters").select("*").execute()
    _chapter_titles_cache = {str(ch["chapter_number"]): ch for ch in (result.data or [])}
    return _chapter_titles_cache


async def retrieve_context(query: str, top_k: int = 5, context_radius: int = 1) -> dict:
    """Retrieve context including verses, footnotes, subtitles, and surrounding verses (async)."""
    query_emb = await asyncio.to_thread(_embed_query_sync, query)

    with vector_search_duration_seconds.time():
        verses_coro = supabase_async.rpc(
            "match_verses",
            {"query_embedding": query_emb, "match_count": top_k},
        ).execute()
        footnotes_coro = supabase_async.rpc(
            "match_footnotes",
            {"query_embedding": query_emb, "match_count": top_k},
        ).execute()
        subtitles_coro = supabase_async.rpc(
            "match_subtitles",
            {"query_embedding": query_emb, "match_count": top_k},
        ).execute()

        verses_resp, footnotes_resp, subtitles_resp = await asyncio.gather(
            verses_coro, footnotes_coro, subtitles_coro
        )

    verses = verses_resp.data or []

    footnotes = {}
    for fn in (footnotes_resp.data or []):
        footnotes.setdefault(fn["verse_id"], []).append(fn.get("english", ""))

    subtitles = {}
    for sub in (subtitles_resp.data or []):
        subtitles.setdefault(sub["verse_id"], []).append(sub.get("english", ""))

    surrounding_tasks = []
    for v in verses:
        task = supabase_async.rpc(
            "get_surrounding_verses",
            {"target_verse_id": v["id"], "context_count": context_radius},
        ).execute()
        surrounding_tasks.append((v["id"], task))

    surrounding = {}
    for verse_id, task in surrounding_tasks:
        try:
            result = await task
            surrounding[verse_id] = result.data or []
        except Exception as e:
            log.warning("failed_to_get_surrounding_verses", verse_id=verse_id, error=str(e))
            surrounding[verse_id] = []

    chapters = await _get_chapter_titles()

    return {
        "verses": verses,
        "footnotes": footnotes,
        "subtitles": subtitles,
        "surrounding": surrounding,
        "chapters": chapters,
    }


def build_prompt(context_data: dict, question: str, history: list[dict] = None) -> str:
    parts = ["You are a knowledgeable Quran assistant. Use ONLY the provided material to answer the question.\n"]
    parts.append("Answer concisely, cite verse references (e.g., 2:255), and do not show reasoning.\n")

    parts.append("--- Chapter Information ---")
    for v in context_data["verses"]:
        ch_num = v["id"].split(":")[0]
        ch = context_data["chapters"].get(ch_num)
        if ch:
            parts.append(f"Chapter {ch_num}: {ch['title_english']} ({ch['title_arabic']})")
    parts.append("")

    for v in context_data["verses"]:
        vid = v["id"]
        parts.append(f"--- Verse {vid} ---")
        parts.append(f"Text: {v['text']}")

        surr = context_data["surrounding"].get(vid, [])
        if surr:
            parts.append("Surrounding context:")
            for sv in sorted(surr, key=lambda x: x["verse_id"]):
                parts.append(f"  {sv['verse_id']}: {sv['text']}")

        fn_texts = context_data["footnotes"].get(vid, [])
        if fn_texts:
            parts.append("Footnotes:")
            for fn in fn_texts:
                parts.append(f"  - {fn}")

        sub_texts = context_data["subtitles"].get(vid, [])
        if sub_texts:
            parts.append("Subtitles (topic):")
            for sub in sub_texts:
                parts.append(f"  - {sub}")

        parts.append("")

    if history:
        parts.append("--- Conversation History ---")
        for turn in history:
            role = "User" if turn["role"] == "user" else "Assistant"
            parts.append(f"{role}: {turn['content']}")
        parts.append("")

    parts.append(f"Question: {question}")
    parts.append("Answer:")
    return "\n".join(parts)


async def rag_answer(question: str) -> str:
    """Generate an answer using RAG with retrieved context (async)."""
    context = await retrieve_context(question, top_k=5, context_radius=1)
    prompt = build_prompt(context, question)

    verses = verses_resp.data or []
    
    # Map footnotes/subtitles to verse_id
    footnotes = {}
    for fn in (footnotes_resp.data or []):
        footnotes.setdefault(fn["verse_id"], []).append(fn.get("english", ""))
    
    subtitles = {}
    for sub in (subtitles_resp.data or []):
        subtitles.setdefault(sub["verse_id"], []).append(sub.get("english", ""))

    # Fetch surrounding verses for each retrieved verse concurrently
    surrounding_tasks = []
    for v in verses:
        task = supabase_async.rpc("get_surrounding_verses", {
            "target_verse_id": v["id"],
            "context_count": context_radius
        }).execute()
        surrounding_tasks.append((v["id"], task))
    
    surrounding = {}
    for verse_id, task in surrounding_tasks:
        try:
            result = await task
            surrounding[verse_id] = result.data or []
        except Exception as e:
            log.warning("failed_to_get_surrounding_verses", verse_id=verse_id, error=str(e))
            surrounding[verse_id] = []

    # Fetch chapter titles
    chapters = await _get_chapter_titles()

    return {
        "verses": verses,
        "footnotes": footnotes,
        "subtitles": subtitles,
        "surrounding": surrounding,
        "chapters": chapters
    }

def build_prompt(context_data: dict, question: str, history: list[dict] = None) -> str:
    parts = ["You are a knowledgeable Quran assistant. Use ONLY the provided material to answer the question.\n"]
    parts.append("Be informative and concise, cite verse references (e.g., 2:255), and do not show reasoning. Responses should be 4000 characters or less.\n")

    # Chapters (brief)
    parts.append("--- Chapter Information ---")
    for v in context_data["verses"]:
        ch_num = v["id"].split(":")[0]
        ch = context_data["chapters"].get(ch_num)
        if ch:
            parts.append(f"Chapter {ch_num}: {ch['title_english']} ({ch['title_arabic']})")
    parts.append("")

    # For each retrieved verse, combine all sources
    for v in context_data["verses"]:
        vid = v["id"]
        parts.append(f"--- Verse {vid} ---")
        parts.append(f"Text: {v['text']}")

        # Surrounding verses (before/after)
        surr = context_data["surrounding"].get(vid, [])
        if surr:
            parts.append("Surrounding context:")
            for sv in sorted(surr, key=lambda x: x["verse_id"]):
                parts.append(f"  {sv['verse_id']}: {sv['text']}")

        # Footnotes for this verse
        fn_texts = context_data["footnotes"].get(vid, [])
        if fn_texts:
            parts.append("Footnotes:")
            for fn in fn_texts:
                parts.append(f"  - {fn}")

        # Subtitles for this verse
        sub_texts = context_data["subtitles"].get(vid, [])
        if sub_texts:
            parts.append("Subtitles (topic):")
            for sub in sub_texts:
                parts.append(f"  - {sub}")

        parts.append("")

    # Conversation history (if provided)
    if history:
        parts.append("--- Conversation History ---")
        for turn in history:
            role = "User" if turn["role"] == "user" else "Assistant"
            parts.append(f"{role}: {turn['content']}")
        parts.append("")

    parts.append(f"Question: {question}")
    parts.append("Answer:")
    return "\n".join(parts)


async def rag_answer(question: str) -> str:
    """Generate an answer using RAG with retrieved context (async)."""
    context = await retrieve_context(question, top_k=5, context_radius=1)
    prompt = build_prompt(context, question)
    
    try:
        with llm_generation_duration_seconds.labels(model="gemini").time():
            response = await asyncio.to_thread(
                gemini_client.models.generate_content,
                model="gemini-2.5-flash",
                contents=prompt,
            )
        log.info("gemini_rag_answer_generated")
        return response.text
    except Exception as e:
        log.warning("gemini_failed_fallback_glm5", error=str(e))
        llm_fallback_total.inc()
        with llm_generation_duration_seconds.labels(model="glm5").time():
            return await asyncio.to_thread(_glm5_generate, prompt)


async def rag_answer_with_history(question: str, history: list[dict]) -> str:
    """Generate an answer for a follow-up question using history and retrieved context (async)."""
    context = await retrieve_context(question, top_k=5, context_radius=1)
    prompt = build_prompt(context, question, history)

    try:
        with llm_generation_duration_seconds.labels(model="gemini").time():
            response = await asyncio.to_thread(
                gemini_client.models.generate_content,
                model="gemini-2.5-flash",
                contents=prompt,
            )
        log.info("gemini_followup_answer_generated")
        return response.text
    except Exception as e:
        log.warning("gemini_failed_fallback_glm5", error=str(e))
        llm_fallback_total.inc()
        with llm_generation_duration_seconds.labels(model="glm5").time():
            return await asyncio.to_thread(_glm5_generate, prompt)