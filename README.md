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

## Prerequisites

- Python 3.8+
- Node.js 16+ (for dashboard development)
- Docker & Docker Compose (for deployment)
- Discord bot token and application ID
- Supabase project
- Hugging Face token (for embeddings)
- Gemini API key (for LLM)

## Environment Variables

Create a `.env` file with the following variables:

| Variable | Description | Required |
|---|---|---|
| `BOT_TOKEN` | Discord bot token | Yes |
| `CLIENT_ID` | Discord application client ID | Yes |
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_SECRET_KEY` | Your Supabase service role key | Yes |
| `HF_TOKEN` | Hugging Face API token | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `HOST` | FastAPI server host (set to `0.0.0.0` for Docker) | Yes for Docker |
| `PROMETHEUS_URL` | Prometheus endpoint for bot metrics queries | Yes for Docker |

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

# Rebuild dashboard
docker compose build dashboard && docker compose up -d dashboard

# Check status
docker compose ps
```

## Monitoring

### Key Metrics

- **Bot Status**: `up{job="discord_bot"}`
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

- **Missing .env variables**: Ensure all required environment variables are set, including `HOST=0.0.0.0` for Docker
- **Port conflicts**: Check if ports 8000, 9090, 3000 are available
- **Model download hangs**: Monitor bot logs for embedding model loading
- **Dashboard shows no data**: Verify Prometheus is scraping metrics from bot
- **FastAPI server not accessible**: Check that `HOST=0.0.0.0` is set in Docker environment
- **Prometheus scraping fails**: Ensure bot container exposes port 8000 and Prometheus config uses correct target

### Docker Networking Issues

- **Bot metrics not scraped**: Prometheus config should use `discord_bot:8000` (container name) not `host.docker.internal:8000`
- **Dashboard can't connect**: Dashboard uses `http://prometheus:9090` which should work in the monitoring network
- **Port not exposed**: Bot container must have `ports: - "8000:8000"` in docker-compose.yml

### Docker Image Size

The bot Docker image is ~10GB due to PyTorch and SentenceTransformers dependencies. To reduce size:

- **Remove model pre-download**: Don't download embedding models during build
- **Use multi-stage builds**: Separate build and runtime stages
- **Consider smaller models**: Switch to lighter embedding models (e.g., `all-MiniLM-L6-v2` instead of `all-mpnet-base-v2`)
- **Use slim base images**: Consider `python:3.11-slim` instead of full Python image

### Logs

```bash
# All services
docker compose logs

# Specific service
docker compose logs discord_bot

# Follow logs
docker compose logs -f prometheus
```

## Requirements

- Python 3.13+
- A Discord bot application ([Discord Developer Portal](https://discord.com/developers/applications))
- A Supabase project ([supabase.com](https://supabase.com))

## License

See [LICENSE](LICENSE).
