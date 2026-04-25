import os
from sentence_transformers import SentenceTransformer
from google import genai
from huggingface_hub import InferenceClient
from db.supabase_client import supabase
from dotenv import load_dotenv
from logger import get_logger
from metrics import (
    embedding_duration_seconds,
    embedding_model_load_duration_seconds,
    llm_fallback_total,
    llm_generation_duration_seconds,
    vector_search_duration_seconds,
)

load_dotenv()
log = get_logger(__name__)

_model = None
gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
_hf_client = None


def _get_hf_client() -> InferenceClient:
    global _hf_client
    if _hf_client is None:
        _hf_client = InferenceClient(
            model=os.environ.get("HF_GLM_MODEL", "zai-org/GLM-5"),
            token=os.environ["HF_TOKEN"],
        )
    return _hf_client


def _glm5_generate(prompt: str) -> str:
    """Call GLM-5 via the Hugging Face Inference API as a fallback."""
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


def retrieve_verses(query: str, top_k: int = 7) -> list:
    log.info("retrieving_verses", top_k=top_k)
    with embedding_duration_seconds.time():
        query_embedding = _get_model().encode(query).tolist()
    with vector_search_duration_seconds.time():
        result = supabase.rpc("match_verses", {
            "query_embedding": query_embedding,
            "match_count": top_k
        }).execute()
    log.info("verses_retrieved", count=len(result.data))
    return result.data


def rag_answer(question: str) -> str:
    verses = retrieve_verses(question, top_k=10)
    context = "\n".join([f"[{v['id']}] {v['text']}" for v in verses])

    prompt = f"""You are a knowledgeable Quran assistant. Answer the question below using ONLY the provided verses.

Rules:
- Do NOT show any reasoning, thinking steps, or internal deliberation.
- Respond directly with the final answer only.
- Be concise and clear, but include all relevant detail.
- Cite every verse you reference (e.g. 2:255).
- Keep the total response under 3500 characters.

Verses:
{context}

Question: {question}

Answer:"""

    try:
        with llm_generation_duration_seconds.labels(model="gemini").time():
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
        log.info("gemini_rag_answer_generated")
        print(response.text)
        return response.text
    except Exception as e:
        log.warning("gemini_failed_fallback_glm5", error=str(e))
        llm_fallback_total.inc()
        with llm_generation_duration_seconds.labels(model="glm5").time():
            return _glm5_generate(prompt)


def rag_answer_with_history(question: str, history: list[dict]) -> str:
    verses = retrieve_verses(question, top_k=10)
    context = "\n".join([f"[{v['id']}] {v['text']}" for v in verses])

    history_text = ""
    for turn in history:
        role = "User" if turn["role"] == "user" else "Assistant"
        history_text += f"{role}: {turn['content']}\n\n"

    prompt = f"""You are a knowledgeable Quran assistant. Answer the follow-up question below using ONLY the provided verses.

Rules:
- Do NOT show any reasoning, thinking steps, or internal deliberation.
- Respond directly with the final answer only.
- Be concise and clear, but include all relevant detail.
- Cite every verse you reference (e.g. 2:255).
- Keep the total response under 4000 characters.
- Use the conversation history for context.

Verses:
{context}

Conversation history:
{history_text}
Follow-up question: {question}

Answer:"""

    try:
        with llm_generation_duration_seconds.labels(model="gemini").time():
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
        log.info("gemini_followup_answer_generated")
        return response.text
    except Exception as e:
        log.warning("gemini_failed_fallback_glm5", error=str(e))
        llm_fallback_total.inc()
        with llm_generation_duration_seconds.labels(model="glm5").time():
            return _glm5_generate(prompt)