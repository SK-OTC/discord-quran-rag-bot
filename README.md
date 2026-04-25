# Discord Quran RAG Bot

A Discord bot that answers questions about the Quran using a RAG (Retrieval-Augmented Generation) pipeline, with a FastAPI backend, Supabase for feedback storage, and Prometheus for metrics monitoring.

## Features

- `/ask` — Ask a question and receive an AI-generated answer
- `/ping` — Check bot latency
- `/about` — Show information about the bot
- `/feedback` — Rate AI responses and submit comments, stored in Supabase
- Real-time metrics dashboard with Prometheus integration
- Docker Compose deployment for full-stack setup

## Project Structure

```
├── main.py                  # Bot entry point, starts Discord bot + FastAPI server
├── command_list.py          # Registers all slash commands
├── cache.py                 # Caching utilities
├── logger.py                # Logging configuration
├── metrics.py               # Prometheus metrics definitions
├── prometheus.yml           # Prometheus configuration
├── docker-compose.yml       # Docker Compose services (bot, prometheus, dashboard)
├── Dockerfile               # Docker build for bot service
├── requirements.txt         # Python dependencies
├── test_endpoints.py        # API endpoint tests
├── test_server.py          # Server tests
├── .env.example             # Environment variables template
├── backend/                 # FastAPI routes and helpers
│   ├── routes.py
│   ├── rag.py
│   ├── load_chapters.py
│   ├── conversation_store.py
│   └── server_start.py
├── bot_commands/            # Slash command handlers
│   ├── ask.py
│   ├── about.py
│   ├── feedback.py
│   ├── followup.py
│   └── ping.py
├── db/
│   └── supabase_client.py   # Supabase client initialization
├── ui_components/           # Discord UI components (views, modals)
│   ├── btn_interactions.py
│   ├── feedback_modal.py
│   ├── followup_modal.py
│   └── response_separator.py
└── dashboard/               # React metrics dashboard
    ├── src/
    ├── public/
    ├── package.json
    └── Dockerfile
```

## Prerequisites

- Python 3.8+
- Node.js 16+ (for dashboard development)
- Docker & Docker Compose (for deployment)
- Discord bot token and application ID
- Supabase project
- Hugging Face token (for embeddings)
- Gemini API key (for LLM)

## Quick Start (Local Development)

### 1. Clone and Setup

```bash
git clone <repo-url>
cd discord-quran-rag-bot
```

### 2. Environment Setup

```bash
# Create virtual environment
python -m venv bot-env

# Activate (Windows)
bot-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Discord bot token |
| `CLIENT_ID` | Discord application client ID |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SECRET_KEY` | Your Supabase service role key |
| `HF_TOKEN` | Hugging Face API token |
| `GEMINI_API_KEY` | Google Gemini API key |

### 4. Setup Supabase

Create a `user_feedback` table:

```sql
create table user_feedback (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  username text not null,
  rating smallint not null,
  comments text,
  created_at timestamptz default now()
);
```

### 5. Run the Bot

```bash
python main.py
```

## Docker Deployment

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

### Access Services

- **Bot API**: http://localhost:8000 (docs: /docs, health: /health)
- **Prometheus**: http://localhost:9090
- **Dashboard**: http://localhost:3000

### Service Control

```bash
# Start specific service
docker compose up -d discord_bot

# Rebuild dashboard
docker compose build dashboard && docker compose up -d dashboard

# Check status
docker compose ps
```

## Monitoring

### Key Metrics

- **Bot Status**: `up{job="quran-bot"}`
- **Command Count**: `discord_commands_total`
- **Response Time**: `rag_query_duration_seconds` (median < 5s)
- **Feedback Rating**: `feedback_rating_distribution` (avg > 4.0/5)

### Verification

```bash
# Check containers
docker compose ps

# Test metrics
curl http://localhost:8000/metrics

# Test health
curl http://localhost:8000/health

# View dashboard
open http://localhost:3000
```

## Troubleshooting

### Common Issues

- **Missing .env variables**: Ensure all required environment variables are set
- **Port conflicts**: Check if ports 8000, 9090, 3000 are available
- **Model download hangs**: Monitor bot logs for embedding model loading
- **Dashboard shows no data**: Verify Prometheus is scraping metrics from bot

### Logs

```bash
# All services
docker compose logs

# Specific service
docker compose logs discord_bot
```

## Requirements

- Python 3.13+
- A Discord bot application ([Discord Developer Portal](https://discord.com/developers/applications))
- A Supabase project ([supabase.com](https://supabase.com))

## License

See [LICENSE](LICENSE).
