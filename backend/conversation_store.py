# In-memory per-user conversation history with TTL caching.
# Maps user_id (int) -> {"data": list[dict], "timestamp": float}
import time

_store: dict[int, dict] = {}
_cache_ttl_seconds = 1800  # 30 minute TTL for conversation cache


def _is_cache_valid(timestamp: float) -> bool:
    """Check if cached conversation is still valid (not expired)"""
    return (time.time() - timestamp) < _cache_ttl_seconds


def get_history(user_id: int) -> list[dict]:
    """
    Get conversation history for user with TTL cache invalidation.
    Returns empty list if cache expired or doesn't exist.
    """
    if user_id in _store:
        cached = _store[user_id]
        if _is_cache_valid(cached["timestamp"]):
            return cached["data"]
        else:
            # Cache expired, remove it
            del _store[user_id]
    return []


def start_conversation(user_id: int, question: str, answer: str) -> None:
    """Start a new conversation, resetting the cache"""
    _store[user_id] = {
        "data": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
        "timestamp": time.time()
    }


def append_turn(user_id: int, question: str, answer: str) -> None:
    """Add a new turn to the conversation, updating the timestamp"""
    if user_id not in _store:
        _store[user_id] = {"data": [], "timestamp": time.time()}
    
    # Update timestamp to extend TTL
    _store[user_id]["timestamp"] = time.time()
    _store[user_id]["data"].extend([
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ])


def clear_expired_conversations() -> int:
    """
    Clear all expired conversations from cache.
    Returns number of conversations cleared.
    Used for cleanup and memory management.
    """
    expired_users = [
        user_id for user_id, cached in _store.items()
        if not _is_cache_valid(cached["timestamp"])
    ]
    for user_id in expired_users:
        del _store[user_id]
    return len(expired_users)
