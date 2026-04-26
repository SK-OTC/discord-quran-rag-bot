# ingest.py
import sys
import os
# import psycopg2

# bot-env/Scripts/python.exe ./backend/embed_setup.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sentence_transformers import SentenceTransformer
from db.supabase_client import supabase

model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)

# Your Supabase database connection string
# DB_URL = "postgresql://[user]:[password]@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

# def run_sql_file(filepath):
#     conn = None
#     cur = None
#     try:
#         conn = psycopg2.connect(DB_URL)
#         cur = conn.cursor()
#         script_path = os.path.join(os.path.dirname(__file__), filepath)
#         with open(script_path, 'r', encoding='utf-8') as f:
#             sql = f.read()
#         cur.execute(sql)
#         conn.commit()
#         print(f"✅ Successfully executed {filepath}")
#     except Exception as e:
#         print(f"❌ Error in {filepath}: {e}")
#         if conn:
#             conn.rollback()
#     finally:
#         if cur:
#             cur.close()
#         if conn:
#             conn.close()

# # Run each of your SQL files
# files = [    
#     "quran_footnotes_rows.sql",    
#     "quran_subtitles_rows.sql",
#     "quran_chapters_rows.sql",
#     "quran_index_rows.sql",
#     "quran_verses_rows.sql"
#     "quran_text_rows.sql"
# ]
# for file in files:
#     run_sql_file(file)

### INITIAL EMBEDDING (RUN ONCE) ###
def embed_table(table_name, text_column):
    response = supabase.table(table_name).select("verse_id", text_column).is_("embedding", "null").execute()
    for row in response.data:
        emb = model.encode(row[text_column] or "").tolist()
        supabase.table(table_name).update({"embedding": emb}).eq("verse_id", row["verse_id"]).execute()
    print(f"Embedded {len(response.data)} rows in {table_name}")

embed_table("verses", "text")
embed_table("quran_footnotes", "english")
embed_table("quran_subtitles", "english")