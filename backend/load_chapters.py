# ingest.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
import time
from db.supabase_client import supabase
from sentence_transformers import SentenceTransformer

BASE = "https://ws-backend.wikisubmission.org/api/v1"
model = SentenceTransformer("nomic-ai/nomic-embed-text-v1")  # free, 768-dim

for chapter in range(1, 115):
    r = requests.get(f"{BASE}/quran", params={
        "langs": "en",
        "chapter_number_start": chapter,
        "chapter_number_end": chapter
    })
    for ch in r.json()["chapters"]:
        for verse in ch["verses"]:
            text = verse["tr"]["en"]["tx"]
            embedding = model.encode(text).tolist()
            supabase.table("quran_verses").upsert({
                "id": verse["vk"],
                "chapter_number": ch["cn"],
                "verse_number": verse["vi"],
                "text": text,
                "embedding": embedding
            }).execute()
    time.sleep(0.2)