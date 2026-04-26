import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HOST = os.getenv("HOST", "0.0.0.0")
RAG_BACKEND_URL = os.getenv("RAG_BACKEND_URL", "http://localhost:8000/ask")
RAG_FOLLOWUP_URL = os.getenv("RAG_FOLLOWUP_URL", "http://localhost:8000/followup")
FEEDBACK_BACKEND_URL = os.getenv("FEEDBACK_BACKEND_URL", "http://localhost:8000/feedback")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
HF_GLM_MODEL = os.getenv("HF_GLM_MODEL", "zai-org/GLM-5")
