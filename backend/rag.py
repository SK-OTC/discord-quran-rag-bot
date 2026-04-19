import os
from sentence_transformers import SentenceTransformer
from google import genai
from db.supabase_client import supabase
from dotenv import load_dotenv

load_dotenv()

_model = None
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)
    return _model


def retrieve_verses(query: str, top_k: int = 10) -> list:
    query_embedding = _get_model().encode(query).tolist()
    result = supabase.rpc("match_verses", {
        "query_embedding": query_embedding,
        "match_count": top_k
    }).execute()
    return result.data


def rag_answer(question: str) -> str:
    verses = retrieve_verses(question, top_k=10)
    context = "\n".join([f"[{v['id']}] {v['text']}" for v in verses])

    prompt = f"""Answer this question using only the Quran verses provided below. \
Cite the verse references (e.g. 2:255) in your answer.

Context:
{context}

Question: {question}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text