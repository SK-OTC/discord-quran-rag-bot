from prometheus_client import Counter, Histogram

# ---------------------------------------------------------------------------
# Discord command counters
# ---------------------------------------------------------------------------

# Incremented every time a Discord slash command is invoked.
# Label "command": ask | followup | feedback | regenerate
discord_commands_total = Counter(
    "discord_commands_total",
    "Total number of Discord slash commands invoked",
    ["command"],
)

# Incremented when a Discord command fails (network error or bad HTTP status).
discord_command_errors_total = Counter(
    "discord_command_errors_total",
    "Total number of Discord slash command errors",
    ["command"],
)

# ---------------------------------------------------------------------------
# RAG pipeline latencies
# ---------------------------------------------------------------------------

# End-to-end time from receiving the request to returning the answer.
# Label "endpoint": ask | followup | regenerate
rag_query_duration_seconds = Histogram(
    "rag_query_duration_seconds",
    "End-to-end RAG query latency in seconds",
    ["endpoint"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0],
)

# Time to encode a query into an embedding vector.
embedding_duration_seconds = Histogram(
    "embedding_duration_seconds",
    "Time to embed a query using the sentence transformer model",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

# Time for the Supabase match_verses RPC (vector similarity search).
vector_search_duration_seconds = Histogram(
    "vector_search_duration_seconds",
    "Time for Supabase vector similarity search (match_verses RPC)",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

# Time for the LLM to generate a response.
# Label "model": gemini | glm5
llm_generation_duration_seconds = Histogram(
    "llm_generation_duration_seconds",
    "Time for LLM text generation",
    ["model"],
    buckets=[1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0],
)

# One-time cold-start time to load the SentenceTransformer model into memory.
embedding_model_load_duration_seconds = Histogram(
    "embedding_model_load_duration_seconds",
    "Time to load the sentence transformer embedding model",
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0],
)

# ---------------------------------------------------------------------------
# Database metrics
# ---------------------------------------------------------------------------

# Time for Supabase table write operations.
# Label "table": user_feedback
db_write_duration_seconds = Histogram(
    "db_write_duration_seconds",
    "Time for database write operations",
    ["table"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

# Distribution of user feedback star ratings (1–5).
feedback_rating_distribution = Histogram(
    "feedback_rating_distribution",
    "Distribution of user feedback ratings",
    buckets=[1, 2, 3, 4, 5],
)

# ---------------------------------------------------------------------------
# Reliability counters
# ---------------------------------------------------------------------------

# Incremented each time Gemini fails and GLM-5 is used as a fallback.
llm_fallback_total = Counter(
    "llm_fallback_total",
    "Number of times Gemini failed and fell back to GLM-5",
)
