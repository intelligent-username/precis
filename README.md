# Précis

A system for compressing long-form content into clear, structured summaries. Précis is designed for videos, articles, and papers. Paste a YouTube link, drop in an article, or upload a text file. Précis will pulls the key facts into a single sentence using a local LLM via [Ollama](https://ollama.com).

## Stack

| Layer    | Tech |
|----------|------|
| Frontend | React 19 + Vite |
| Backend  | FastAPI (Python) |
| LLM      | Ollama (phi4-mini, qwen-4b) |

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ (or [Bun](https://bun.sh))
- [Ollama](https://ollama.com) installed and running (`ollama serve`)
- At least one model pulled: `ollama pull phi4-mini:latest`

### Run the Fine-Tuning

Follow the scripts in `scripts/`, using any model you prefer. This project has been primarily tested with phi4-mini (from Microsoft) and Qwen 3-3b (from Alibaba).

### Backend

```bash
cd backend
pip install -r ../requirements.txt
uvicorn app:app --reload
```

Runs on `http://localhost:8000`. Interactive docs at `/docs`.

### Frontend

```bash
cd frontend
npm install   # or whatever replacement for npm you may be using
npm run dev
```

Runs on `http://localhost:5173`.

## Features

- **YouTube summarization**: paste a URL, transcript is fetched automatically via `youtube-transcript-api`
- **Article / transcript**: paste any text directly
- **File upload**: drag-and-drop `.txt` files
- **Streaming**: summaries stream token-by-token from Ollama via NDJSON
- **Model switching**: choose between available Ollama models from the UI

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/health` | Health check |
| `GET`  | `/status` | Service status, available models, Ollama reachability |
| `GET`  | `/models` | List available models |
| `POST` | `/summarize/transcript` | Summarize raw text (NDJSON stream) |
| `POST` | `/summarize/youtube` | Summarize a YouTube video by URL (NDJSON stream) |
| `POST` | `/summarize/file` | Summarize an uploaded `.txt` file (NDJSON stream) |

All `/summarize/*` endpoints accept an optional `model` field to override the default.

## License

[GPL-3.0](LICENSE.md)
