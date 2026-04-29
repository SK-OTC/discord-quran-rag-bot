# Discord Quran RAG Bot

A Discord bot with an embedded FastAPI backend that answers Quran questions using async RAG (Retrieval-Augmented Generation), Supabase vector search, and Gemini with GLM fallback.

## Current Features

- `/ask` - Ask a question about the Quran
- `/followup` - Ask a follow-up question using conversation history
- `/ping` - Check bot latency
- `/about` - Show bot info
- `/metrics` - Show metrics dashboard link/info
- In-message buttons for:
  - Regenerate
  - Follow up
  - Rate AI response
- Feedback storage in Supabase (`user_feedback`)
- Prometheus metrics exposed by FastAPI (`/metrics`)

## Architecture

- One Python process runs:
  - Discord bot
  - FastAPI app on `127.0.0.1:8000`
- `backend/routes.py` exposes:
  - `POST /ask`
  - `POST /followup`
  - `POST /feedback`
  - `GET /health`
  - `GET /metrics` (via instrumentator)
- `backend/rag.py` pipeline:
  - Embeds query with `nomic-ai/nomic-embed-text-v1`
  - Searches Supabase RPCs (`match_verses`, `match_footnotes`, `match_subtitles`)
  - Fetches surrounding verses and chapter metadata
  - Builds grounded prompt
  - Generates with Gemini (`gemini-2.5-flash`)
  - Falls back to HF Inference GLM-5 when Gemini fails

## Project Structure

```text
├── main.py
├── command_list.py
├── config.py
├── logger.py
├── metrics.py
├── requirements.txt
├── backend/
│   ├── routes.py
│   ├── rag.py
│   ├── conversation_store.py
│   ├── load_chapters.py
│   └── server_start.py
├── bot_commands/
│   ├── ask.py
│   ├── followup.py
│   ├── about.py
│   ├── ping.py
│   └── metrics.py
├── db/
│   └── supabase_client.py
├── ui_components/
│   ├── response_view.py
│   ├── btn_interactions.py
│   ├── followup_modal.py
│   ├── feedback_modal.py
│   └── rate_response.py
└── dashboard/
```

## Environment Variables

Loaded in `config.py`:

- `BOT_TOKEN`
- `CLIENT_ID`
- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`
- `HF_TOKEN`
- `GEMINI_API_KEY`
- `HF_GLM_MODEL` (default: `zai-org/GLM-5`)
- `HOST` (default: `0.0.0.0`)
- `RAG_BACKEND_URL` (default: `http://localhost:8000/ask`)
- `RAG_FOLLOWUP_URL` (default: `http://localhost:8000/followup`)
- `FEEDBACK_BACKEND_URL` (default: `http://localhost:8000/feedback`)
- `PROMETHEUS_URL` (default: `http://localhost:9090`)

## Local Setup

```bash
python -m venv bot-env
bot-env/Scripts/activate
pip install -r requirements.txt
```

Create `.env` and fill required values (`BOT_TOKEN`, Supabase creds, `HF_TOKEN`, `GEMINI_API_KEY`).

| Variable | Description | Required |
|---|---|---|
| `BOT_TOKEN` | Discord bot token | Yes |
| `CLIENT_ID` | Discord application client ID | Yes |
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_SECRET_KEY` | Your Supabase service role key | Yes |
| `HF_TOKEN` | Hugging Face API token | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `HOST` | FastAPI server host (set to `0.0.0.0` for Docker) | Yes for Docker |

Vector embedding:

```bash
bot-env/Scripts/python.exe ./backend/embed_setup.py
```

Run:

```bash
python main.py
```

## Docker Deployment

The application consists of three services:
- **discord_bot**: Discord bot with integrated FastAPI server for metrics
- **prometheus**: Metrics collection and storage
- **dashboard**: React frontend for metrics visualization

### Build and Run All Services

```bash
# Build images
docker compose build

# Start services (bot, prometheus, dashboard)
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

## Supabase Requirements

This app expects:

1. A `user_feedback` table:

```sql
create table if not exists user_feedback (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  username text not null,
  rating smallint not null,
  comments text,
  created_at timestamptz default now()
);
```

2. Quran-related tables/RPCs used by RAG:
- `quran_chapters`
- RPCs: `match_verses`, `match_footnotes`, `match_subtitles`, `get_surrounding_verses`

## API Quick Check

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

## Notes

- UI responses use Discord components v2 (`LayoutView` + `TextDisplay`), so messages are sent via view-only payloads (no plain `content` when sending those views).
- Heavy inference work in `backend/rag.py` is offloaded with `asyncio.to_thread(...)` to reduce event-loop blocking.

## License

See `LICENSE`.
