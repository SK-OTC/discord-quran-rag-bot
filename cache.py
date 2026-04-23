# In-memory per-user conversation cache
# Maps user_id (str) -> {"question": str, "answer": str}
user_cache: dict[str, dict] = {}
