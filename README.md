# Discord Quran RAG Bot

A Discord bot that answers questions about the Quran using a RAG (Retrieval-Augmented Generation) pipeline, with a FastAPI backend and Supabase for feedback storage.

## Features

- `/ask` — Ask a question and receive an AI-generated answer
- `/ping` — Check bot latency
- `/about` — Show information about the bot
- Feedback system — Rate AI responses and submit comments, stored in Supabase

## Project Structure

```
├── main.py                  # Bot entry point, starts Discord bot + FastAPI server
├── command_list.py          # Registers all slash commands
├── bot_commands/            # Slash command handlers
│   ├── ask.py
│   ├── about.py
│   ├── feedback.py
│   └── ping.py
├── backend/                 # FastAPI routes and helpers
│   ├── routes.py
│   ├── get_api.py
│   └── server_start.py
├── db/
│   └── supabase_client.py   # Supabase client initialisation
├── ui_components/           # Discord UI components (views, modals)
├── requirements.txt
└── .env.example
```

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd discord-quran-rag-bot
```

### 2. Create and activate a virtual environment

```bash
python -m venv bot-env
```

**Windows (Git Bash):**
```bash
source bot-env/Scripts/activate
```

**Windows (Command Prompt):**
```bat
bot-env\Scripts\activate
```

### 3. Install dependencies

```bash
bot-env/Scripts/python.exe -m pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Discord bot token |
| `CLIENT_ID` | Discord application client ID |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SECRET_KEY` | Your Supabase service role key |
| `FEEDBACK_BACKEND_URL` | Feedback endpoint (default: `http://localhost:8000/feedback`) |
| `RAG_BACKEND_URL` | Ask endpoint (default: `http://localhost:8000/ask`) |

### 5. Set up Supabase

Create a `user_feedback` table in your Supabase project:

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

### 6. Run the bot

```bash
bot-env/Scripts/python.exe main.py
```

## Requirements

- Python 3.13+
- A Discord bot application ([Discord Developer Portal](https://discord.com/developers/applications))
- A Supabase project ([supabase.com](https://supabase.com))

## License

See [LICENSE](LICENSE).
