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

```
├── main.py                  # Bot entry point, starts Discord bot + FastAPI server
├── command_list.py          # Registers all slash commands
├── cache.py                 # Caching utilities
├── logger.py                # Logging configuration
├── metrics.py               # Prometheus metrics definitions
├── prometheus/              # Prometheus configuration
│   └── prometheus.yml       # Prometheus scrape configuration
├── docker-compose.yml       # Docker Compose services (bot, prometheus, dashboard)
├── Dockerfile               # Docker build for bot service
├── requirements.txt         # Python dependencies
├── test_endpoints.py        # API endpoint tests
├── test_server.py          # Server tests
├── .env.example             # Environment variables template
├── backend/                 # FastAPI routes and helpers
│   ├── routes.py            # FastAPI app with /ask, /health, /metrics endpoints
│   ├── rag.py               # RAG pipeline implementation
│   ├── load_chapters.py     # Quran data loading
│   ├── conversation_store.py # Conversation history management
│   └── server_start.py      # Discord bot + FastAPI server integration
├── bot_commands/            # Slash command handlers
│   ├── ask.py               # /ask command
│   ├── about.py             # /about command
│   ├── feedback.py          # /feedback command
│   ├── followup.py          # /followup command
│   └── ping.py              # /ping command
├── db/
│   └── supabase_client.py   # Supabase client initialization
├── ui_components/           # Discord UI components (views, modals, buttons)
│   ├── btn_interactions.py  # Button interaction handlers
│   ├── feedback_modal.py    # Feedback submission modal
│   ├── followup_modal.py    # Follow-up question modal
│   ├── response_view.py     # Response display with buttons
│   └── rate_response.py     # Rating buttons
└── dashboard/               # React metrics dashboard
    ├── src/
    │   ├── App.js           # Main dashboard component
    │   └── components/      # Reusable UI components
    ├── public/
    ├── package.json
    └── Dockerfile
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
bot-env\Scripts\activate
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
bot-env\Scripts\python.exe ./backend/embed_setup.py
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

### Service Architecture

The Discord bot runs both:
1. **Discord client** - Handles Discord interactions
2. **FastAPI server** - Exposes `/metrics` endpoint for Prometheus scraping

### Access Services

- **Bot API**: http://localhost:8000 (docs: /docs, health: /health, metrics: /metrics)
- **Prometheus**: http://localhost:9090
- **Dashboard**: http://localhost:3000
### Service Control

```bash
# Start specific service
docker compose up -d discord_bot

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
