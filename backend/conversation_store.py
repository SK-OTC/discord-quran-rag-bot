# In-memory per-user conversation history.
# Maps user_id (int) -> list of {"role": str, "content": str} turns.
_store: dict[int, list[dict]] = {}


def get_history(user_id: int) -> list[dict]:
    return _store.get(user_id, [])


def start_conversation(user_id: int, question: str, answer: str) -> None:
    _store[user_id] = [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]


def append_turn(user_id: int, question: str, answer: str) -> None:
    if user_id not in _store:
        _store[user_id] = []
    _store[user_id].extend([
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ])
